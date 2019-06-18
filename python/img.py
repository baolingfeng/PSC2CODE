import cv2
import numpy as np
from matplotlib import pyplot as plt
from collections import Counter
from sklearn.cluster import DBSCAN
from util import *
from setting import *


def detect_background(img):
    height, width = img.shape[:2]
    rgb_stat = {}
    for y in range(height):
        for x in range(width):
            RGB = (int(img[y,x,2]), int(img[y,x,1]), int(img[y,x,0]))
            if RGB in rgb_stat:
                rgb_stat[RGB] += 1
            else:
                rgb_stat[RGB] = 1

    number_counter = Counter(rgb_stat).most_common(3)
    percentage_of_first = (float(number_counter[0][1])/(width * height))
    
    # print "percentage_of_first", percentage_of_first
    if percentage_of_first > 0.4:
        return number_counter[0][0]
    else:
        average_red = average_green = average_blue = 0
        for c in number_counter:
            average_red += c[0][0]
            average_green += c[0][1]
            average_blue += c[0][2]
        
        return average_red / len(number_counter), average_green / len(number_counter), average_blue / len(number_counter)
        
MIN_LINE_LENGTH = 50 

class CImage:
    def __init__(self, img, name=None):
        self.name = name
        self.img = img
        self.height, self.width = self.img.shape[:2]
        self.img_gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        # self.detect_hv_lines()

    def preprocess(self, kernel_size=15):
        # equ = cv2.equalizeHist(self.img_gray)
        # self.img_gray = np.hstack((self.img_gray,equ)) #stacking images side-by-side
        # self.img_gray = cv2.medianBlur(self.img_gray,5)
        self.detect_hv_lines(kernel_size=15)

    def find_contours(self, show=False):
        # img = cv2.medianBlur(self.img_gray,5)
        # ret, thresh = cv2.threshold(img, 127, 255, 0)
        # thresh = cv2.adaptiveThreshold(self.img_gray,255,cv2.ADAPTIVE_THRESH_MEAN_C,\
            # cv2.THRESH_BINARY,11,2)
        # rgb = detect_background(self.img)
        # print self.height, self.width

        thresh = cv2.adaptiveThreshold(self.img_gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,\
            cv2.THRESH_BINARY,11,2)
        # thresh = cv2.bitwise_not(self.img_gray)
        im2, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        res = []
        contours = sorted(contours, key = cv2.contourArea, reverse=True)
        for idx, c in enumerate(contours):
            x,y,w,h = cv2.boundingRect(c)
            
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.06 * peri, True)
            if len(approx) > 20:
                continue
            
            if x == 0 and y == 0 and w == self.width and h == self.height:
                continue

            area = cv2.contourArea(c)
            if w < MIN_LINE_LENGTH or h < MIN_LINE_LENGTH:
                continue

            # cv2.rectangle(self.img,(x,y),(x+w,y+h),(0,255,0),2)
            res.append([x, y, w, h])

        if show:
            cv2.imshow('image', self.img)
            if cv2.waitKey(0) & 0xff == 27:
                cv2.destroyAllWindows()
        return sorted(res, key=lambda x:x[2]*x[3])

    def detect_hv_lines(self, kernel_size=15):
        # kernel_size = 15
        self.edges = cv2.Canny(self.img_gray, kernel_size, kernel_size * 2)

        lines = cv2.HoughLinesP(self.edges, 1, np.pi/180, 30, minLineLength=60, maxLineGap=5)
        lines = lines[:, 0, :] if lines is not None else []

        self.v_lines = []
        self.h_lines = []
        self.v_long_lines = []
        self.h_long_lines = []
        ratio = 0.1
        long_ratio = 1.0/3
        for line in lines:
            x1, y1, x2, y2 = line
            if x1 == x2 and abs(y1-y2) > self.height * ratio:
                self.v_lines.append([x1, y2, x2, y1])
                if abs(y1 - y2) > self.height * long_ratio:
                    self.v_long_lines.append([x1, y2, x2, y1])
            elif (y1 == y2 and abs(x1-x2) > self.width * ratio):
                self.h_lines.append([x1, y1, x2, y2])
                if abs(x1 - x2) > self.width * long_ratio:
                    self.h_long_lines.append([x1, y2, x2, y1])
        
        self.v_lines = sorted(self.v_lines, key=lambda x:x[0])
        self.h_lines = sorted(self.h_lines, key=lambda x:x[1])
        self.v_long_lines = sorted(self.v_long_lines, key=lambda x:x[0])
        self.h_long_lines = sorted(self.h_long_lines, key=lambda x:x[1])

    def detect_hv_lines2(self):
        kernel_size = 15
        self.edges = cv2.Canny(self.img_gray, kernel_size, kernel_size * 2)

        op_size = 12
        kernel_h = np.ones((1, op_size*2+1), np.uint8)
        kernel_v = np.ones((op_size*2+1, 1), np.uint8)

        img_lines_h = cv2.erode(self.edges, kernel_h, iterations=1)
        img_lines_h = cv2.dilate(img_lines_h, kernel_h, iterations=1)

        img_lines_v = cv2.erode(self.edges, kernel_v, iterations=1)
        img_lines_v = cv2.dilate(img_lines_v, kernel_v, iterations=1)

        img_lines_h[0, 0:self.width] = 255
        img_lines_h[self.height-1, 0:self.width] = 255
        img_lines_v[0:self.height, 0] = 255
        img_lines_v[0:self.height, self.width-1] = 255

        self.v_lines = []
        self.h_lines = []
        self.v_long_lines = []
        self.h_long_lines = []
        ratio = 0.1
        long_ratio = 1.0 / 3
        # print img_lines_h.shape
        for i in range(self.height):
            j = 0
            while j < self.width:
                while j < self.width and img_lines_h[i, j] == 0:
                    j += 1
                
                k = j + 1
                while k < self.width and img_lines_h[i, k] > 0:
                    k += 1
                
                if k - j > self.width * ratio:
                    self.h_lines.append([j, i, k, i])
                
                if k - j > self.width * long_ratio:
                    self.h_long_lines.append([j, i, k, i])
                
                j = k + 1
        
        for i in range(self.width):
            j = 0
            while j < self.height:
                while j < self.height and img_lines_v[j, i] == 0:
                    j += 1
                
                k = j + 1
                while k < self.height and img_lines_v[k, i] > 0:
                    k += 1
                
                if k - j > self.height * ratio:
                    self.v_lines.append([i, j, i, k])
                
                if k - j > self.height * long_ratio:
                    self.v_long_lines.append([i, j, i, k])
                
                j = k + 1

    def cluster_lines(self):
        print 'clustering lines...'
        blank_image = np.zeros((self.height, self.width, 3), np.uint8)
        color = (0, 255, 0)

        self.h_cluster_lines = []
        self.v_cluster_lines = []

        dbscan = DBSCAN(eps=3, min_samples=1, metric=hv_line_overlap_sim)
        clusters = dbscan.fit(np.array(self.h_lines))
        cluster_num = max(clusters.labels_) + 1
        for i in range(cluster_num):
            line_indexes = [idx for idx, l in enumerate(clusters.labels_) if l == i]
            lines = [self.h_lines[idx] for idx in line_indexes]
            x1, y1, x2, y2 = max(lines, key=lambda x:x[2]-x[0])

            self.h_cluster_lines.append([x1, y1, x2, y2])
            cv2.line(blank_image, (x1, y1), (x2, y2), color, 1)

        dbscan = DBSCAN(eps=3, min_samples=1, metric=hv_line_overlap_sim)
        clusters = dbscan.fit(np.array(self.v_lines))
        cluster_num = max(clusters.labels_) + 1
        for i in range(cluster_num):
            line_indexes = [idx for idx, l in enumerate(clusters.labels_) if l == i]
            lines = [self.v_lines[idx] for idx in line_indexes]
            x1, y1, x2, y2 = max(lines, key=lambda x:x[3]-x[1])

            self.v_cluster_lines.append([x1, y1, x2, y2])
            cv2.line(blank_image, (x1, y1), (x2, y2), color, 1)
        
        cv2.imshow('image', blank_image)
        if cv2.waitKey(0) & 0xff == 27:
            cv2.destroyAllWindows()

    def show(self):
        blank_image = np.zeros((self.height, self.width, 3), np.uint8)

        for line in self.v_lines:
            cv2.line(blank_image, (line[0], line[1]),
                     (line[2], line[3]), (0, 0, 255), 2)

        for line in self.h_lines:
            cv2.line(blank_image, (line[0], line[1]),
                     (line[2], line[3]), (0, 0, 255), 2)

        cv2.imshow('image', blank_image)
        if cv2.waitKey(0) & 0xff == 27:
            cv2.destroyAllWindows()


def test():
    import os, sys

    video = "Java Tutorial For Beginners 15 - Java String"
    completed_path = os.path.join(crop_dir, video, "0", "1_0.png")
    print completed_path
    img = cv2.imread(completed_path)
    cimg = CImage(img, name=video)
    cimg.preprocess(kernel_size=30)

    print cimg.v_lines

    cimg.show()


def main():
    import os, sys
    from dbimpl import DBImpl

    db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})
    sql = 'select title from videos where hash = ?'

    video_hash = 'jJjg4JweJZU'
    frame = 143

    # video_hash = 'o4Or0PMI_aI'
    # frame = 378

    # video_hash = '6HydEu75iQI'
    # frame = 229

    # video_hash = '6TIeyVWPvDY'
    # frame = 225

    # video_hash = 'VKTEjBQzkgs'
    # frame = 37

    # video_hash = 'KUdro0G1BV4'
    # frame = 81

    video_title = db.queryone(sql, video_hash)[0].strip()
    print video_title, video_hash
    
    video_folder = video_title + '_' + video_hash
    completed_path = os.path.join(images_dir, video_folder, '%d.png'%frame)

    img = cv2.imread(completed_path)
    cimg = CImage(img, name=video_folder)
    cimg.preprocess()
    # cimg.show()
    # cimg.cluster_lines()
    rects = cimg.find_contours(show=False)

    rects = sorted(rects, key=lambda x: x[2]*x[3], reverse=True)
    x, y, w, h = rects[0]
    cv2.rectangle(cimg.img,(x,y),(x+w,y+h),(0,0,255),2)

    cv2.imshow('image', cimg.img)
    if cv2.waitKey(0) & 0xff == 27:
        cv2.destroyAllWindows()




if __name__ == '__main__':
    main()
    # test()
    