import cv2
import numpy as np
from matplotlib import pyplot as plt
from sklearn.cluster import DBSCAN
import random
from auto_canny import auto_canny


def overlap(min1, max1, min2, max2):
    """returns the overlap between two lines that are 1D"""
    if min1 < min2:
        min1, min2 = min2, min1
        max1, max2 = max2, max1
    
    if max2 < min1:
        return 0
    elif max1 > max2:
        return max2 - min1
    else:
        return max1 - min1

    # result = None
    # if min1 >= max2:
    #     return max2 - min1
    # elif min2 >= max1: 
    #     result =  max1 - min2
    # elif min1 <= min2:
    #     result = max1 - min2
    # else: 
    #     result = max2 - min1
    # return result


def v_line_sim_metric(line1, line2):
    return abs(line1[0] - line2[0])

def h_line_sim_metric(line1, line2):
    return abs(line1[1] - line2[1])

def line_overlap_sim_metric(line1, line2, thre=5):
    x11, y11, x12, y12 = line1
    x21, y21, x22, y22 = line2
    
    if x11 == x12 and x21 == x22:
        op = overlap(y11, y12, y21, y22)
        if op < 0: # and abs(op) > thre:
            return np.inf
        else:
            return abs(x21 - x11)
    elif y11 == y12 and y21 == y22:
        op = overlap(x11, x12, x21, x22)
        if op < 0:  #and abs(op) > thre:
            return np.inf
        else:
            return abs(y21 - y11)
    else:
        return np.inf

def line_overlap_sim_metric2(line1, line2):
    x11, y11, x12, y12 = line1
    x21, y21, x22, y22 = line2
    
    thre = 0.5
    if x11 == x12 and x21 == x22: #vertical
        op = overlap(y11, y12, y21, y22)
        if op < 0:
            return np.inf

        ratio = (op * 1.0) / min(abs(y11 - y12), abs(y21 - y22))
        if ratio < thre:
            return np.inf
        
        return abs(x21 - x11) 
    elif y11 == y12 and y21 == y22:
        op = overlap(x11, x12, x21, x22)
        if op < 0:
            return np.inf

        ratio = (op * 1.0) / min(abs(x11 - x12), abs(x21 - x22))
        if ratio < thre:
            return np.inf
        
        return abs(y21 - y11)
    else:
        return np.inf

def vh_intersection(vline, hline, vlimit=10, hlimit=10):
    x1, y1, x2 ,y2 = vline
    x3, y3, x4, y4 = hline

    if x1 != x2 or y3 != y4:
        return None

    if abs(x1 - x3) < hlimit:
        x3 = x1
    
    if abs(x1 - x4) < hlimit:
        x4 = x1
    
    if abs(y3 - y1) < vlimit:
        y1 = y3
    
    if abs(y3 - y2) < vlimit:
        y2 = y3

    if not (x1 >= x3 and x1 <= x4 and y3 >= y1 and y3 <= y2):
        return None

    px = x1 
    py = y3

    if px == x3:
        if py == y1:
            corner_type = 1
        elif py == y2:
            corner_type = 4
        else:
            corner_type = 1 | 4
    elif px == x4:
        if py == y1:
            corner_type = 2
        elif py == y2:
            corner_type = 8
        else:
            corner_type = 2 | 8
    else:
        if py == y1:
            corner_type = 1 | 2
        elif py == y2:
            corner_type = 4 | 8
        else:
            corner_type = 1 | 2 | 4 | 8
        
    return (px, py, corner_type)

 
class ImageProcesser:
    def __init__(self, name, img):
        self.name = name
        self.img = img
        self.img_gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        self.height, self.width = self.img_gray.shape[:2]

        print self.height, self.width
    
    def detect_lines(self):
        kernel_size = 15
        # blurred = cv2.GaussianBlur(self.img_gray, (3, 3), 0)
        # self.edges = cv2.Canny(blurred, kernel_size, kernel_size * 2)
        self.edges = cv2.Canny(self.img_gray, kernel_size, kernel_size * 2)

        lines = cv2.HoughLinesP(self.edges, 1, np.pi/180, 30, minLineLength=60, maxLineGap=10)
        lines = lines[:,0,:] if lines is not None else []

        self.v_lines = [[0, 0, 0, self.height], [self.width, 0, self.width, self.height]]
        self.h_lines = [[0, 0, self.width, 0], [0, self.height, self.width, self.height]]
        ratio = 1.0/3
        for line in lines: 
            x1,y1,x2,y2 = line
            if x1 == x2 and abs(y1-y2) > self.height * ratio: 
                self.v_lines.append([x1, y2, x2, y1])
            elif (y1 == y2 and abs(x1-x2) > self.width * ratio):
                self.h_lines.append([x1, y1, x2, y2])
        
    def cluster_lines(self, lines, eps=5, horizontal=True):
        db = DBSCAN(eps=eps, min_samples=1, metric=line_overlap_sim_metric, metric_params={"thre":5}).fit(np.array(lines))

        cluster_num = max(db.labels_) + 1
        cluster_lines = []
        for i in range(0, cluster_num):
            line_indexes = [idx for idx, l in enumerate(db.labels_) if l == i]

            if horizontal:
                max_len = 0
                selected_line = None
                for l in line_indexes:
                    if abs(lines[l][2] - lines[l][0]) > max_len:
                        selected_line = lines[l]
                        max_len = abs(lines[l][2] - lines[l][0])

                minx = min([lines[l][0] for l in line_indexes])
                maxx = max([lines[l][2] for l in line_indexes])
                cluster_lines.append([minx, selected_line[1], maxx, selected_line[1]])
                # maxy = max([lines[l][1] for l in line_indexes])
                # minx = min([lines[l][0] for l in line_indexes])
                # maxx = max([lines[l][2] for l in line_indexes])

                # cluster_lines.append([minx, maxy, maxx, maxy])
            else:
                max_len = 0
                selected_line = None
                for l in line_indexes:
                    if abs(lines[l][3] - lines[l][1]) > max_len:
                        selected_line = lines[l]
                        max_len = abs(lines[l][3] - lines[l][1])

                miny = min([lines[l][1] for l in line_indexes])
                maxy = max([lines[l][3] for l in line_indexes])
                cluster_lines.append([selected_line[0], miny, selected_line[0], maxy])

                # maxx = max([lines[l][0] for l in line_indexes])
                # miny = min([lines[l][1] for l in line_indexes])
                # maxy = max([lines[l][3] for l in line_indexes])
                
                # cluster_lines.append([maxx, miny, maxx, maxy])
        
        return cluster_lines
    
    def cluster_lines_2(self, lines, eps, horizontal=True):
        db = DBSCAN(eps=eps, min_samples=1, metric=line_overlap_sim_metric2).fit(np.array(lines))

        cluster_num = max(db.labels_) + 1
        cluster_lines = []
        for i in range(0, cluster_num):
            line_indexes = [idx for idx, l in enumerate(db.labels_) if l == i]

            if horizontal:
                longest = None
                for lid in line_indexes:
                    line = lines[lid]
                    if longest is None:
                        longest = line
                    else:
                        if longest[2] - longest[0] < line[2] - line[0]:
                            longest = line
                cluster_lines.append(longest)
            else:
                longest = None
                for lid in line_indexes:
                    line = lines[lid]
                    if longest is None:
                        longest = line
                    else:
                        if longest[3] - longest[1] < line[3] - line[1]:
                            longest = line
                cluster_lines.append(longest)

        return cluster_lines


    def clusters(self):
        self.cluster_v_lines = self.cluster_lines(self.v_lines, eps=self.width/200, horizontal=False)
        # self.cluster_v_lines = sorted(self.cluster_v_lines, key=lambda x:x[0])
        
        self.cluster_h_lines = self.cluster_lines(self.h_lines, eps=self.height/200, horizontal=True)
        # self.cluster_h_lines = sorted(self.cluster_h_lines, key=lambda x:x[1])

        self.cluster_v_lines_2 = self.cluster_lines_2(self.cluster_v_lines, eps=self.width/40, horizontal=False)
        self.cluster_h_lines_2 = self.cluster_lines_2(self.cluster_h_lines, eps=self.height/50, horizontal=True)

        self.cluster_v_lines_2 = sorted(self.cluster_v_lines_2, key=lambda x:x[0])
        self.cluster_h_lines_2 = sorted(self.cluster_h_lines_2, key=lambda x:x[1])

    def find_corners(self):
        self.up_left = []
        self.bottom_right = []
        for vline in self.cluster_v_lines_2:
            vx1, vy1, vx2, vy2 = vline

            for hline in self.cluster_h_lines_2:
                hx1, hy1, hx2, hy2 = hline

                corner = vh_intersection(vline, hline, vlimit=self.height/50, hlimit=self.width/50) 
                if corner is None:
                    continue
                
                if corner[2] & 1 > 0:
                    self.up_left.append(corner[0:2])
                
                if corner[2] & 8 > 0:
                    self.bottom_right.append(corner[0:2])
        
        print self.up_left
        print self.bottom_right
        
    def detect_rect(self):
        points = [(line[0], line[1]) for line in self.cluster_v_lines_2]
        points = sorted(points, key=lambda x:x[1])

        h_lines = []
        h_lines.append((points[0], points[1]))
        for i in range(2, len(points)):
            p = points[i]

            x1 = points[i-1][0]
            x2 = points[i-2][0]
            if x1 > x2:
                x1, x2 = x2, x1

            h_lines.append(((x1, points[i][1]), (x2, points[i][1])))

        down_points = [(line[2], line[3]) for line in self.cluster_v_lines_2]
        down_points = sorted(down_points, key=lambda x:x[1], reverse=True)

        h_lines.append((down_points[0], down_points[1]))
        for i in range(2, len(down_points)):
            p = down_points[i]

            x1 = down_points[i-1][0]
            x2 = down_points[i-2][0]
            if x1 > x2:
                x1, x2 = x2, x1

            h_lines.append(((x1, down_points[i][1]), (x2, down_points[i][1])))

        return h_lines

    def test_mser(self):
        mser = cv2.MSER_create()

        regions = mser.detectRegions(self.img_gray)
        # print regions
        hulls = [cv2.convexHull(p.reshape(-1, 1, 2)) for p in regions[0]]

        print hulls[0]
        cv2.polylines(self.img_gray, hulls, 1, (0, 0, 255), 2)
        cv2.imshow('line map', self.img_gray)
        if cv2.waitKey(0) & 0xff == 27:
            cv2.destroyAllWindows()

    def test(self):
        self.detect_lines()
        self.clusters()
        self.find_corners()
        # print self.cluster_v_lines_2
        
        # h_lines = self.detect_rect()
        # print h_lines

        # print self.cluster_h_lines
        linemap = self.img.copy()
        for line in self.v_lines:
            cv2.line(linemap, (line[0], line[1]), (line[2], line[3]), (255, 0, 255), 1)
        
        for line in self.h_lines:
            cv2.line(linemap, (line[0], line[1]), (line[2], line[3]), (255, 0, 0), 1)

        # cv2.imwrite('../linemap/%s_linemap.png' % self.name, linemap)

        linemap2 = self.img.copy()
        for line in self.cluster_v_lines:
            cv2.line(linemap2, (line[0], line[1]), (line[2], line[3]), (255, 0, 255), 2)
        
        for line in self.cluster_h_lines:
            cv2.line(linemap2, (line[0], line[1]), (line[2], line[3]), (255, 0, 0), 2)

        # cv2.imwrite('../linemap/%s_linemap2.png' % self.name, linemap2)

        linemap3 = self.img.copy()
        # linemap3 = np.zeros((self.height, self.width,3), np.uint8)
        for line in self.cluster_v_lines_2:
            cv2.line(linemap3, (line[0], line[1]), (line[2], line[3]), (255, 0, 255), 2)
        
        for line in self.cluster_h_lines_2:
            cv2.line(linemap3, (line[0], line[1]), (line[2], line[3]), (255, 0, 0), 2)
        
        for corner in self.up_left:
            cv2.circle(linemap3, corner, 3, (0,0,255), 2)
        
        for corner in self.bottom_right:
            cv2.circle(linemap3, corner, 8, (0,255,0), 2)

        # cv2.imwrite('../linemap/%s_linemap3.png' % self.name, linemap3)

        scale = 0.6
        small = cv2.resize(linemap, (0,0), fx=scale, fy=scale)
        cv2.imshow('line map', small)
        if cv2.waitKey(0) & 0xff == 27:
            cv2.destroyAllWindows()


def main():
    img = cv2.imread('../imgs/CS50/test.png')
    ip = ImageProcesser("CS50-test", img)
    img = cv2.imread('../imgs/email/3314.png')
    ip = ImageProcesser("email_3314", img)

    # img = cv2.imread('../imgs/array/4414.png')
    # ip = ImageProcesser("array_4414", img)

    # img = cv2.imread('../imgs/mac-vscode.png')
    # ip = ImageProcesser("mac-vscode", img)

    # img = cv2.imread('../imgs/ThinkAloud.png')
    # ip = ImageProcesser("ThinkAloud", img)

    ip.test()
    # ip.test_mser()

    # print overlap(10, 218, 228, 1064)

if __name__ == '__main__':
    main()