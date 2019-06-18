import os
import cv2
from img import CImage
from setting import *

def adjust_crop(cimg):
    pass

def main():
    video_name = "Java Tutorial For Beginners 4 - Variables and Types in Java"
    cluster = "0"
    crop_folder = os.path.join(crop_dir, video_name, cluster)

    frame = "1_0.png"
    # print os.path.join(crop_folder, frame)
    img = cv2.imread(os.path.join(crop_folder, frame))

    cimg = CImage(img, name=frame)
    cimg.preprocess()
    cimg.find_contours()


if __name__ == '__main__':
    main()