import cv2
import numpy as np
from matplotlib import pyplot as plt
from sklearn.cluster import DBSCAN
from sklearn.cluster import KMeans
import random
import math
import json
import os
import shutil
from img import CImage
from setting import *
from util import *

class CVideo:
    def __init__(self, video_name, config={'eps1':2, 'eps2':1, 'min_samples':2, 'line_ratio':0.7}):
        self.name = video_name
        self.images = []
        self.config = config

        print 'reading frames...'
        with open(os.path.join(images_dir, video_name, "predict.txt")) as fin:
            lines = fin.readlines()
            if len(lines[1].strip()) > 0:
                frames = [int(frame) for frame in lines[1].split(",")]
            else:
                frames = []

        # validated_images_dir = os.path.join(predicted_dir, video_name, "1")
        for frame in frames:
            img = cv2.imread(os.path.join(images_dir, video_name, "%d.png" % frame))
            cimg = CImage(img, frame)
            cimg.preprocess()

            self.images.append(cimg)
        
        self.images = sorted(self.images, key=lambda x:int(x.name))
        print '%d frames have been initialized' % len(self.images)

        if len(self.images) > 0:
            self.height = self.images[0].height
            self.width = self.images[0].width
            print 'height/width', self.height, self.width


    def cluster_lines(self):
        lines = []
        for idx, image in enumerate(self.images):
            for line in image.v_long_lines:
                lines.append(line + [idx])

            for line in image.h_long_lines:
                lines.append(line + [idx])

        print 'clustering lines...'
        dbscan = DBSCAN(eps=self.config['eps1'], min_samples=len(self.images)*0.1, metric=hv_line_overlap_sim)
        clusters = dbscan.fit(np.array(lines))

        blank_image = np.zeros((self.height, self.width, 3), np.uint8)

        cluster_num = max(clusters.labels_) + 1

        image_vectors = np.zeros((len(self.images), cluster_num), dtype=int)
        cluster_lines = []
        for i in range(cluster_num):
            line_indexes = [idx for idx, l in enumerate(clusters.labels_) if l == i]
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

            max_len = 0
            min_center_distance = max(self.width, self.height)
            longest = None
            closest = None
            for l in line_indexes:
                x1, y1, x2, y2, fid = lines[l]
                if x1 == x2:
                    line_len = y2 - y1
                    center_distance = abs(self.width/2 - x1)
                elif y1 == y2:
                    line_len = x2 - x1
                    center_distance = abs(self.height/2 - y1)

                if line_len > max_len:
                    max_len = line_len
                    longest = [x1, y1, x2, y2]
                
                if center_distance < min_center_distance and line_len == max_len :
                    min_center_distance = center_distance
                    closest = [x1, y1, x2, y2]

                image_vectors[fid, i] = 1
                cv2.line(blank_image, (x1, y1), (x2, y2), color, 1)
            
            if x1 == x2:  
                cluster_lines.append([closest[0], longest[1], closest[0], longest[3]])
            else:
                cluster_lines.append([longest[0], closest[1], longest[2], closest[1]])

        print "Number of clustered lines:", len(cluster_lines)
        clusters = DBSCAN(eps=self.config['eps2'], min_samples=self.config['min_samples']).fit(image_vectors)

        # if not os.path.exists(os.path.join(lines_dir, self.name)):
        #     os.mkdir(os.path.join(lines_dir, self.name))
        # else:
        #     shutil.rmtree(os.path.join(lines_dir, self.name))
        #     os.mkdir(os.path.join(lines_dir, self.name))

        self.line_map = {}
        cluster_num = max(clusters.labels_) + 1
        for i in range(cluster_num):
            image_indexes = [idx for idx, l in enumerate(clusters.labels_) if l == i]

            print 'cluster', i, len(image_indexes), [int(self.images[f].name) for f in image_indexes]
            # print [self.images[f] for f in image_indexes]
            self.line_map[i] = {}
            self.line_map[i]['frames'] = [int(self.images[f].name) for f in image_indexes]

            blank_image2 = np.zeros((self.height, self.width, 3), np.uint8)

            # print image_vectors[image_indexes]
            res_lines = []
            for idx, column in enumerate(image_vectors[image_indexes].T):
                one = len([v for v in column if v == 1])
                if one > len(column) * self.config['line_ratio']:
                    # print idx, cluster_lines[idx]
                    res_lines.append(cluster_lines[idx])
                    x1, y1, x2, y2 = cluster_lines[idx]
                    cv2.line(blank_image2, (x1, y1), (x2, y2), (0, 255, 0), 2)     

            self.line_map[i]["lines"] = res_lines
            cv2.imwrite("%s/%s/%d.png" % (lines_dir, self.name, i), blank_image2)

        image_indexes = [idx for idx, l in enumerate(clusters.labels_) if l == -1]
        print 'not clustered image', len(image_indexes), [int(self.images[f].name) for f in image_indexes]
        self.unclustered = [int(self.images[f].name) for f in image_indexes]

        cv2.imwrite("%s/%s/linemap.png" % (lines_dir, self.name), blank_image)

    def adjust_lines(self):
        for cid in self.line_map:
            cluster = self.line_map[cid]
            # if len(cluster["frames"]) < 5:
            #     continue

            hlines = [[int(x1), int(y1), int(x2), int(y2)] for x1, y1, x2, y2 in cluster['lines'] if y1 == y2]
            vlines = [[int(x1), int(y1), int(x2), int(y2)] for x1, y1, x2, y2 in cluster['lines'] if x1 == x2]

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

            if len(hlines) == 0 or abs(hlines[0][1] - 0) > self.height * 0.01:
                hlines.insert(0, [0, 0, self.width, 0])
            else:
                hlines[0] = 0, 0, self.width, 0

            if abs(self.height - hlines[-1][1]) > self.height * 0.01:
                hlines.append([0, self.height, self.width, self.height])
            else:
                hlines[-1] = 0, self.height, self.width, self.height

            for hid, (x1, y1, x2, y2) in enumerate(hlines):
                if abs(x2 - x1) < self.width * 1.0 / 2:
                    continue

                start_intersection, end_intersection = False, False
                for vx1, vy1, vx2, vy2 in vlines:
                    if x1 == vx1 and y1 >= vy1 and y1 <= vy2:
                        start_intersection = True
                    
                    if x2 == vx1 and y2 >= vy1 and y2 <= vy2:
                        end_intersection = True
                
                # if not start_intersection ^ end_intersection:
                #     continue

                if not start_intersection:
                    temp = [vid for vid, (vx1, vy1, vx2, vy2) in enumerate(vlines) if vx1 <= x1 and y1 >= vy1 and y1 <= vy2]
                    # print "extend hline before", x1, y1, vlines[temp[-1]][0]
                    # if abs(vlines[temp[-1]][0] - hlines[hid][0]) < 20:
                    hlines[hid][0] = vlines[temp[-1]][0]
                
                if not end_intersection:
                    temp = [vid for vid, (vx1, vy1, vx2, vy2) in enumerate(vlines) if vx1 >= x2 and y2 >= vy1 and y2 <= vy2]
                    # print "extend hline after", x2, y2, vlines[temp[0]][0]
                    hlines[hid][2] = vlines[temp[0]][0]
            
            for vid, (x1, y1, x2, y2) in enumerate(vlines):
                # if y2 - y1 < self.height / 3:
                #     continue

                start_intersection, end_intersection = False, False
                for hx1, hy1, hx2, hy2 in hlines:
                    if y1 == hy1 and x1 >= hx1 and x1 <= hx2:
                        start_intersection = True
                    
                    if y2 == hy1 and x2 >= hx1 and x2 <= hx2:
                        end_intersection = True
                
                if not start_intersection:
                    temp = [hid for hid, (hx1, hy1, hx2, hy2) in enumerate(hlines) if hy1 <= y1 and x1 >= hx1 and x1 <= hx2]
                    # print "extend vline before", x1, y1, hlines[temp[-1]][1]
                    vlines[vid][1] = hlines[temp[-1]][1]
                
                if not end_intersection:
                    temp = [hid for hid, (hx1, hy1, hx2, hy2) in enumerate(hlines) if hy1 >= y2 and x2 >= hx1 and x2 <= hx2]
                    # print "extend vline after", x2, y2, hlines[temp[0]][1]
                    vlines[vid][3] = hlines[temp[0]][1]

            blank_image = np.zeros((self.height, self.width, 3), np.uint8)
            for x1, y1, x2, y2 in hlines:
                cv2.line(blank_image, (x1, y1), (x2, y2), (0, 0, 255), 2)

            for x1, y1, x2, y2 in vlines:
                cv2.line(blank_image, (x1, y1), (x2, y2), (0, 0, 255), 2)

            cv2.imwrite("%s/%s/%d_adjust.png" % (lines_dir, self.name, cid), blank_image)

            self.line_map[cid]["adjusted_hlines"] = hlines
            self.line_map[cid]["adjusted_vlines"] = vlines

    def detect_rects(self):
        for cid in self.line_map:
            cluster = self.line_map[cid]
            # if len(cluster["frames"]) < 5:
            #     continue

            hlines = cluster["adjusted_hlines"]
            vlines = cluster["adjusted_vlines"]

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

            xy_matrix = np.zeros((len(xarray), len(yarray)), dtype=np.int64)
            for i in range(len(xarray)):
                for j in range(len(yarray)):
                    for vline in xarray[i]['line']:
                        for hline in yarray[j]['line']:
                            if vh_intersection(vline, hline):
                                xy_matrix[i, j] = 1
                                break

            rects = find_rects(xy_matrix)
            print "detected rectangle", len(rects)

            selected_rects = []
            for idx, r in enumerate(rects):
                a, b, c, d = r
                x1 = xarray[a]['x']
                y1 = yarray[b]['y']
                x2 = xarray[c]['x']
                y2 = yarray[d]['y']

                if x2 - x1 < self.width * 1.0 / 3 or y2 - y1 < self.height * 1.0 / 3 :
                    continue

                selected_rects.append([x1, y1, x2, y2])

            self.line_map[cid]['rects'] = selected_rects
        
        with open(os.path.join(lines_dir, self.name, "lines.json"), "w") as fout:
            res = {}
            res['linemap'] = self.line_map
            res['config'] = self.config
            json.dump(res, fout, indent=4, default=dump_numpy)


    def crop_rects(self):
        if os.path.exists('%s/%s' % (crop_dir, self.name)):
            shutil.rmtree(os.path.join(crop_dir, self.name))    
            
        if hasattr(self, 'line_map'):
            linemap = self.line_map
        else:
            if not os.path.exists(os.path.join(lines_dir, self.name, "lines.json")):
                return 

            print 'use line map in local file'
            with open(os.path.join(lines_dir, self.name, "lines.json")) as fin:
                data = json.load(fin)
                linemap = data['linemap']

        os.mkdir('%s/%s' % (crop_dir, self.name))

        frames = [int(img.name) for img in self.images]

        clusters = []
        to_be_cropped = False
        for cid in linemap:
            cluster = linemap[cid]
            cluster_frames = cluster['frames']

            if 'to_be_cropped' in cluster:
                to_be_cropped = True

            rects = cluster['rects'] if 'rects' in cluster else []
            cropped = cluster['to_be_cropped'] if 'to_be_cropped' in cluster else False

            clusters.append([cid, cluster_frames, rects, cropped])
        
        if len(clusters) <= 0:
            return
        
        clusters = sorted(clusters, key=lambda x:len(x[1]), reverse=True)
        if not to_be_cropped:
            clusters[0][3] = True
        
        for cluster in clusters:
            to_be_cropped = cluster[3]
            if not to_be_cropped:
                continue
            
            cluster_frames = cluster[1]
            rects = cluster[2]
            if len(rects) <= 0:
            # if len(cluster_frames) < 5 or len(rects) <= 0:
                continue
 
            for fidx, f in enumerate(cluster_frames):
                # img = self.images[f]
                if f not in frames:
                    img = cv2.imread(os.path.join(images_dir, self.name, "%d.png" % f))
                    img = CImage(img, f)
                    img.preprocess()
                    # continue
                else:
                    img = self.images[frames.index(f)]
                # print f, frames.index(f)
                
                x1, y1, x2, y2 = rects[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                if len(img.v_long_lines) > 0:
                    k = np.argmin(np.array([abs(lx1-x1) for (lx1, ly1, lx2, ly2) in img.v_long_lines]))
                    x1 = img.v_long_lines[k][0] if abs(img.v_long_lines[k][0] - x1) < 10 else x1 

                    k = np.argmin(np.array([abs(lx1-x2) for (lx1, ly1, lx2, ly2) in img.v_long_lines]))
                    x2 = img.v_long_lines[k][0] if abs(img.v_long_lines[k][0] - x2) < 10 else x2

                # print img.h_long_lines
                if len(img.h_long_lines) > 0:
                    k = np.argmin(np.array([abs(ly1-y1) for (lx1, ly1, lx2, ly2) in img.h_long_lines]))
                    y1 = img.h_long_lines[k][1] if abs(img.h_long_lines[k][1] - y1) < 10 else y1

                    k = np.argmin(np.array([abs(ly1-y2) for (lx1, ly1, lx2, ly2) in img.h_long_lines]))
                    y2 = img.h_long_lines[k][1] if abs(img.h_long_lines[k][1] - y2) < 10 else y2

                cv2.imwrite("%s/%s/%s.png" % (crop_dir, self.name, img.name), img.img[y1:y2, x1:x2])


def batch():
    from dbimpl import DBImpl
    import preprocess
    from video_tagging.predict import predict_video, load_model

    db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})
    default_config = {'eps1': 3, 'eps2':2, 'min_samples':2, 'line_ratio': 0.7}

    sql = 'select id, title from playlists where used = 1'
    sql2 = 'select hash, title from videos where playlist = ? and used = 1 order by list_order'
    res = db.querymany(sql)
    for list_id, title in res:
        list_folder = os.path.join(video_dir, list_id)
        if not os.path.exists(list_folder):
            continue

        print list_id
        videos = db.querymany(sql2, list_id)
        for video_hash, video_title in videos:
            video_title = video_title.strip()
            video_folder = video_title + '_' + video_hash

            
            video_path = os.path.join(video_dir, list_id, video_folder+".mp4")
            
            if not os.path.exists(os.path.join(images_dir, video_folder)):
                continue
            if not os.path.exists(os.path.join(images_dir, video_folder, 'predict.txt')):
                predict_video(video_folder, valid_model)
            
            if os.path.exists(os.path.join(crop_dir, video_folder)):
                continue
            
            cvideo = CVideo(video_folder, config=default_config)
            if len(cvideo.images) <= 0:
                continue

            if not os.path.exists(os.path.join(lines_dir, video_folder)):
                os.mkdir(os.path.join(lines_dir, video_folder))

            
            cvideo.cluster_lines()
            cvideo.adjust_lines()
            cvideo.detect_rects()

            print video_title, video_hash
            cvideo.crop_rects()


if __name__ == '__main__':
    batch()