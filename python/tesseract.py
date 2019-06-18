import pytesseract
import argparse
import cv2
import os
from PIL import Image
from setting import *


def tesseract_ocr(video_name, video_hash, frame):
    video_folder = video_name + '_' + video_hash
    
    crop_image_folder = os.path.join(crop_dir, video_folder)

    print crop_image_folder
    image_path = os.path.join(crop_image_folder, "%d.png" % frame)

    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    h, w = gray.shape[:2]

    resize_factor = 1
    # gray = cv2.resize(gray, (h*resize_factor, w*resize_factor), interpolation = cv2.INTER_AREA)

    # gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    # gray = cv2.medianBlur(gray, 3)
    img = Image.fromarray(gray)

    txt = pytesseract.image_to_string(img, config="--load_system_dawg F --load_freq_dawg F")
    print txt

def main():
    video_name = 'Java Tutorial 87 - JComboBox'
    video_hash = '1VERDZBsjgE'

    tesseract_ocr(video_name, video_hash, 314)

if __name__ == '__main__':
    main()
