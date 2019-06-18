import cv2
import numpy as np
from matplotlib import pyplot as plt
from sklearn.cluster import DBSCAN
from sklearn.cluster import KMeans
import hdbscan
import skimage.measure
import os
import sys
from util import *
import random
import math
import json
from collections import Counter

from img import CImage


class CVideo:
    def __init__(self, video_name, frame_folder):
        self.name = video_name
        self.images = []

        with open("%s/frames.txt" % frame_folder) as fin:
            lines = fin.readlines()

            self.frame_num = int(lines[0].strip())
            self.filter_frames = [int(f) for f in lines[1].strip().split(" ")]

        print 'frame number', self.frame_num, len(self.filter_frames)

        for frame in range(1, self.frame_num+1):
            if frame in self.filter_frames:

                img = cv2.imread("%s/%d.png" % (frame_folder, frame))

                cimg = CImage(frame, img)
                cimg.preprocess()
                self.images.append(cimg)
            else:
                # read later...
                self.images.append(None)

        if len(self.images) > 0:
            self.height = self.images[0].height
            self.width = self.images[0].width
            print 'height/width', self.height, self.width

    def cluster_lines(self, linemap="../linemap"):
        lines = []
        # frames = [image.name for image in self.images]
        for idx, f in enumerate(self.filter_frames):
            image = self.images[f-1]
            # flatten_images.append(image.img_gray.flatten())
            for line in image.v_long_lines:
                lines.append(line + [idx])

            for line in image.h_long_lines:
                lines.append(line + [idx])
            # lines.extend(image.v_long_lines])
            # lines.extend(image.h_long_lines])

        # print self.images[0].img_gray
        # print flatten_images[0].reshape(self.height, self.width)
        # clusters = KMeans(n_clusters=10, random_state=0).fit(np.array(flatten_images))
        # print clusters.labels_

        print 'clustering lines...'
        dbscan = DBSCAN(eps=2, min_samples=len(
            self.filter_frames)*0.2, metric=hv_line_overlap_sim)
        clusters = dbscan.fit(np.array(lines))

        # clusters = hdbscan.HDBSCAN().fit(np.array(flatten_images))

        blank_image = np.zeros((self.height, self.width, 3), np.uint8)

        cluster_num = max(clusters.labels_) + 1
        cluster_lines = []

        image_vectors = np.zeros((len(self.filter_frames), cluster_num))
        cluster_lines = []
        for i in range(0, cluster_num):
            line_indexes = [idx for idx, l in enumerate(
                clusters.labels_) if l == i]

            color = (random.randint(0, 255), random.randint(
                0, 255), random.randint(0, 255))

            # temp_lines = [lines[l] for l in line_indexes]
            # if temp_lines[0][0] == temp_lines[0][2]:
            #     temp_lines = sorted(temp_lines, key=lambda x:(x[3]-x[1]), reverse=True)

            max_len = 0
            longest = None
            for l in line_indexes:
                line = lines[l]
                x1, y1, x2, y2, fid = line
                line_len = math.sqrt((y2-y1) * (y2-y1) + (x2-x1) * (x2-x1))
                if line_len > max_len:
                    max_len = line_len
                    longest = [x1, y1, x2, y2]

                # fid = self.filter_frames.index(f)
                # image_vectors[f, i] += 1
                image_vectors[fid, i] = 1
                cv2.line(blank_image, (x1, y1), (x2, y2), color, 1)

            cluster_lines.append(longest)

        print image_vectors
        # clusters = hdbscan.HDBSCAN().fit(image_vectors)
        print 'clustering images...'
        clusters = DBSCAN(eps=1, min_samples=len(
            self.filter_frames)*0.05).fit(image_vectors)
        # clusters = DBSCAN(eps=0.1, min_samples=len(self.images)*0.01).fit(image_vectors)

        res = {}
        cluster_num = max(clusters.labels_) + 1
        for i in range(0, cluster_num):
            image_indexes = [idx for idx, l in enumerate(
                clusters.labels_) if l == i]

            print i
            print [self.filter_frames[f] for f in image_indexes]
            res[i] = {}
            res[i]['frames'] = [self.filter_frames[f] for f in image_indexes]

            blank_image2 = np.zeros((self.height, self.width, 3), np.uint8)

            line_seg = image_vectors[image_indexes[0]]
            res_lines = []
            for idx, seg in enumerate(line_seg):
                if seg == 1:
                    res_lines.append(cluster_lines[idx])
                    x1, y1, x2, y2 = cluster_lines[idx]
                    cv2.line(blank_image2, (x1, y1), (x2, y2), color, 1)

            res[i]['linemap'] = res_lines

            cv2.imwrite("%s/%s-%d.png" % (linemap, self.name, i), blank_image2)

        with open("%s/%s.json" % (linemap, self.name), "w") as fout:
            json.dump(res, fout, indent=4, default=dump_numpy)

        cv2.imwrite("%s/%s.png" % (linemap, self.name), blank_image)

    def crop_rects(self, linemap="../linemap", crop_out="Crops"):
        with open('%s/%s.json' % (linemap, self.name)) as fin:
            clusters = json.load(fin)

            for cid in clusters:
                cluster = clusters[cid]
                if len(cluster['linemap']) == 0:
                    continue

                hlines = [[int(x1), int(y1), int(x2), int(y2)]
                          for x1, y1, x2, y2 in cluster['linemap'] if y1 == y2]
                vlines = [[int(x1), int(y1), int(x2), int(y2)]
                          for x1, y1, x2, y2 in cluster['linemap'] if x1 == x2]

                vlines = sorted(vlines, key=lambda x: x[0])
                hlines = sorted(hlines, key=lambda x: x[1])

                if len(vlines) == 0 or abs(vlines[0][0] - 0) > self.width * 0.01:
                    vlines.insert(0, [0, 0, 0, self.height])
                else:
                    vlines[0] = 0, 0, 0, self.height

                if abs(self.width - vlines[-1][0]) > self.width * 0.01:
                    vlines.append([self.width, 0, self.width, self.height])
                else:
                    vlines[-1] = self.width, 0, self.width, self.height
                    # vlines[-1][1], vlines[-1][3] = 0, self.height

                if len(hlines) == 0 or abs(hlines[0][1] - 0) > self.height * 0.01:
                    hlines.insert(0, [0, 0, self.width, 0])
                else:
                    hlines[0] = 0, 0, self.width, 0
                    # hlines[0][0], hlines[0][2] = 0, self.width

                if abs(self.height - hlines[-1][1]) > self.height * 0.01:
                    hlines.append([0, self.height, self.width, self.height])
                else:
                    hlines[-1] = 0, self.height, self.width, self.height
                    # hlines[-1][0], hlines[-1][2] = 0, self.width

                print len(vlines), len(hlines)

                xarray = []
                for line in vlines:
                    x1, y1, x2, y2 = line

                    if len(xarray) == 0:
                        xarray.append({'x': x1, 'line': [line]})
                    else:
                        if xarray[-1]['x'] == x1:
                            xarray[-1]['line'].append(line)
                        else:
                            xarray.append({'x': x1, 'line': [line]})

                yarray = []
                for line in hlines:
                    x1, y1, x2, y2 = line

                    if len(yarray) == 0:
                        yarray.append({'y': y1, 'line': [line]})
                    else:
                        if yarray[-1]['y'] == y1:
                            yarray[-1]['line'].append(line)
                        else:
                            yarray.append({'y': y1, 'line': [line]})

                # print len(xarray), len(yarray)
                # print xarray
                # print yarray
                xy_matrix = np.zeros(
                    (len(xarray), len(yarray)), dtype=np.int64)
                for i in range(len(xarray)):
                    for j in range(len(yarray)):

                        for vline in xarray[i]['line']:
                            for hline in yarray[j]['line']:
                                if vh_intersection(vline, hline):
                                    xy_matrix[i, j] = 1
                                    break

                rects = find_rects(xy_matrix)
                print rects

                # line_img = cv2.imread("%s/%s-%s.png" % (linemap, self.name, cid))
                selected_rects = []
                for idx, r in enumerate(rects):
                    a, b, c, d = r
                    x1 = xarray[a]['x']
                    y1 = yarray[b]['y']
                    x2 = xarray[c]['x']
                    y2 = yarray[d]['y']

                    if (y2-y1) * (x2-x1) < self.width * self.height * 0.25:
                        continue

                    selected_rects.append([x1, y1, x2, y2])
                    # color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                    # cv2.rectangle(line_img, (x1, y1), (x2, y2), color, 2)
                    # cv2.putText(line_img, str(idx), ((x1+x2)/2, (y1+y2)/2), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

                if not os.path.exists('%s/%s' % (crop_out, self.name)):
                    os.mkdir('%s/%s' % (crop_out, self.name))

                if not os.path.exists('%s/%s/%s' % (crop_out, self.name, cid)):
                    os.mkdir('%s/%s/%s' % (crop_out, self.name, cid))

                print 'rects', selected_rects
                for fidx, f in enumerate(cluster['frames']):
                    img = self.images[f-1].img

                    for idx, r in enumerate(selected_rects):
                        x1, y1, x2, y2 = r
                        cv2.imwrite("%s/%s/%s/%d_%d.png" % (crop_out,
                                                            self.name, cid, f, idx), img[y1:y2, x1:x2])

                    if fidx == len(cluster['frames']) - 1:
                        cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)

                    cv2.imwrite("%s/%s-%s-rect.png" %
                                (linemap, self.name, cid), img)


def detect_popup():
    from shutil import copyfile

    base_folder = "/Volumes/MYWD/Research/VideoAnalytics"
    # video_name = "Java Programming Lets Build a Game 1"
    video_name = "Intermediate Java Tutorial - 15 - Queue"
    # video_name = "Java Programming"
    crop_out = "%s/Crops" % base_folder

    filename = "%s/%s/0/84_0.png" % (crop_out, video_name)
    # filename = "%s/Crops/%s/1/379_0.png" % (base_folder, video_name)
    # filename = "%s/Crops/%s/0/64_0.png" % (base_folder, video_name)
    # filename = "%s/Images/%s/414.png" % (base_folder, video_name)
    # filename = "%s/Images/%s/16.png" % (base_folder, video_name)
    
    img = cv2.imread(filename)
    myimg = CImage("test", img)
    myimg.find_contours()

    # cluster = 0
    # crop_out = "%s/Crops" % base_folder
    # for filename in os.listdir("%s/%s/%s" % (crop_out, video_name, cluster)):
    #     filepath = "%s/%s/%d/%s" % (crop_out, video_name, cluster, filename)
    #     img = cv2.imread(filepath)
    
    #     myimg = CImage("test", img)
    # # print detect_background(img)

    #     rects = myimg.find_contours()
    #     if len(rects) > 0:
    #         copyfile(filepath, "%s/%s/Popup/%s" % (crop_out, video_name, filename))
    #         print filename, rects
    #         break
    #     else:
    #         jsonfile = filename.split(".")[0] + ".json"
    #         copyfile(filepath, "%s/%s/NoPopup/%s" % (crop_out, video_name, filename))
            # copyfile("/Users/lingfengbao/Dropbox/VideoAnalytics/GoogleOCR/%s/1/%s" % (video_name, jsonfile), "/Users/lingfengbao/Downloads/JSON/%s" % jsonfile)
        
    # myimg.detect_hv_lines2()
    # myimg.show()


def main():
    # detect_popup()

    base_folder = "/Volumes/MYWD/Research/VideoAnalytics"
    video_folder = "%s/Images" % base_folder
    # # video_name = "Java Programming"
    # # video_name = "Angular 2 Routing & Navigation Basics"
    # # video_name = "email"
    # # video_name = "Java Tutorial 11 GUI in Java JFrame JPanel JButton JLabel"
    # # video_name = "Arrays - Java Tutorial 10"
    # # video_name = "Java Programming Lets Build a Game 1"
    # # video_name = "JUnit Tutorial 1"
    # # video_name = "Java EE (J2EE) Tutorial for beginners Part6"
    # video_name = "Intermediate Java Tutorial - 15 - Queue"
    # video_name = "Java Threads Tutorial 2 - How to Create Threads in Java by Extending Thread Class"
    # frame_folder = video_folder + "/" + video_name

    for folder in os.listdir(video_folder):
        print folder
        frame_folder = video_folder + '/' + folder
        if not os.path.exists('%s/frames.txt' % frame_folder):
            preprocess(frame_folder)

    # video = CVideo(video_name, frame_folder)
    # video.cluster_lines()
    # video.crop_rects(crop_out="%s/Crops" % base_folder)

    # img = cv2.imread(frame_folder + "/16.png")
    # cimg = CImage("16", img)
    # cimg.preprocess()
    # cimg.show()


if __name__ == '__main__':
    main()
