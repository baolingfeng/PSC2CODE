import cv2
import numpy as np
from matplotlib import pyplot as plt
from sklearn.cluster import KMeans
from sklearn.cluster import DBSCAN
import random

def overlap(min1, max1, min2, max2):
    """returns the overlap between two lines that are 1D"""
    result = None
    if min1 >= max2:
        return max2 - min1
    elif min2 >= max1: 
        result =  max1 - min2
    elif min1 <= min2:
        result = max1 - min2
    else: 
        result = max2 - min1
    return result

def line_metric(line1, line2):
    x11, y11, x12, y12 = line1
    x21, y21, x22, y22 = line2

    if x11 == x12 and x21 == x22:
        return abs(x21 - x11)
    elif y11 == y12 and y21 == y22:
        return abs(y21 - y11)
    else:
        return np.inf 

def line_metric2(line1, line2):
    x11, y11, x12, y12 = line1
    x21, y21, x22, y22 = line2

    # overlap_distance = 5

    if x11 == x12 and x21 == x22:
        # op = overlap(y11, y12, y21, y22)
        op = overlap(y12, y11, y22, y21)
        if op < 0 and abs(op) > 5:
            return np.inf
        else:
            return abs(x21 - x11)
    elif y11 == y12 and y21 == y22:
        op = overlap(x11, x12, x21, x22)
        if op < 0 and abs(op) > 5:
            return np.inf
        else:
            return abs(y21 - y11)
    else:
        return np.inf 

def detect_line(img):
    img_gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    height, width = img_gray.shape[:2]

    blank_image = np.zeros((height,width,3), np.uint8)

    edges = cv2.Canny(img_gray,18, 18*3)

    # lines = cv2.HoughLines(edges,1,np.pi/180, 180)
    # x1, y1, x2, y2 = line, i found x1 < x2 but y1 > y2
    lines = cv2.HoughLinesP(edges,1,np.pi/180,30,minLineLength=60,maxLineGap=10)
    lines1 = lines[:,0,:] #提取为为二维
    lines1 = np.append(lines1, [[0, height, 0, 0], [width, height, width, 0], [0, 0, width, 0], [0, height, width, height]], axis = 0)

    points = []
    lines2 = []
    for line in lines1[:]: 
        x1,y1,x2,y2 = line
        if (x1 == x2 and abs(y1-y2) > 100) or (y1 == y2 and abs(x1-x2) > 100):
            print x1, y1, x2, y2
            points.append([x1, y1])
            points.append([x2, y2])
            lines2.append(line)
            # cv2.circle(blank_image, (x1, y1), 2, (255,0,0), 1)
            # cv2.circle(blank_image, (x2, y2), 2, (255,0,0), 1)
            # cv2.line(blank_image,(x1,y1),(x2,y2),(255,0,0),1)

    points = np.array(points)

    db = DBSCAN(eps=5, min_samples=1, metric=line_metric2).fit(lines2)
    print db.labels_

    cluster_num = max(db.labels_) + 1
    v_lines = [[0, 0, 0, height], [width, 0, width, height]]
    h_lines = [[0, 0, width, 0], [0, height, width, height]]
    for i in range(0, cluster_num):
        line_indexes = [idx for idx, l in enumerate(db.labels_) if l == i]

        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        
        x1, y1, x2, y2 = lines2[line_indexes[0]] 
        if x1 == x2:
            maxx = max([lines2[l][0] for l in line_indexes])
            maxy = max([lines2[l][1] for l in line_indexes])
            miny = min([lines2[l][3] for l in line_indexes])
            
            v_lines.append([maxx, miny, maxx, maxy])
            cv2.line(img, (maxx,miny),(maxx,maxy),(255, 0, 255), 2)
        elif y1 == y2:
            maxy = max([lines2[l][1] for l in line_indexes])
            minx = min([lines2[l][0] for l in line_indexes])
            maxx = max([lines2[l][2] for l in line_indexes])

            h_lines.append([minx, maxy, maxx,maxy])
            cv2.line(img, (minx,maxy),(maxx,maxy),(255, 255, 0), 2)
    
        # for l in line_indexes:
        #     x1, y1, x2, y2 = lines2[l]
        #     cv2.line(img, (x1,y1),(x2,y2),color,1)
    v_lines = sorted(v_lines, key=lambda x:x[0])
    h_lines = sorted(h_lines, key=lambda x:x[1])
    print h_lines

    # small = cv2.resize(img, (0,0), fx=0.5, fy=0.5)
    cv2.imshow('line map', img)
    if cv2.waitKey(0) & 0xff == 27:
        cv2.destroyAllWindows()

def detect_corner(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    gray = np.float32(gray)
    # corners = cv2.goodFeaturesToTrack(gray, 100, 0.01, 10)
    # corners = np.int0(corners)
    # for corner in corners:
    #     x,y = corner.ravel()
    #     cv2.circle(img,(x,y),3,255,-1)
    dst = cv2.cornerHarris(gray,2,3,0.04)
    dst = cv2.dilate(dst, None)

    # Threshold for an optimal value, it may vary depending on the image.
    img[dst>0.01*dst.max()] = [0,0,255]

    cv2.imshow('dst',img)
    if cv2.waitKey(0) & 0xff == 27:
        cv2.destroyAllWindows()

def main():
    # img = cv2.imread('../imgs/mac-vscode.png')
    img = cv2.imread('../imgs/email/5034.png')
    # detect_corner(img)
    detect_line(img)
    # detect_corner(line_img)

if __name__ == '__main__':
    main()