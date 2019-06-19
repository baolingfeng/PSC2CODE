import os, sys
import cv2
sys.append.append('..')
from img import CImage
from dbimpl import DBImpl
from setting import *
from OCR.image_ocr import extract_text



def crop_noisy_frame(video_folder):
    with open(os.path.join(images_dir, video_folder, 'predict.txt')) as fin:
        lines = fin.readlines()

        frames = [int(frame) for frame in lines[3].strip().split(',')] if lines[3].strip() != '' else [] # noisy frames

        # print frames

        if not os.path.exists(os.path.join(crop_dir, video_folder, 'noise')):
            os.mkdir(os.path.join(crop_dir, video_folder, 'noise'))
        # print os.path.join(crop_dir, video_folder, 'noise')

        for frame in frames:
            completed_path = os.path.join(images_dir, video_folder, '%d.png'%frame)
            # print completed_path
            img = cv2.imread(completed_path)
            cimg = CImage(img, name=video_folder)
            cimg.preprocess()

            rects = cimg.find_contours(show=False)
            rects = sorted(rects, key=lambda x: x[2]*x[3], reverse=True)
            if len(rects) <= 0:
                continue
            x, y, w, h = rects[0]
            # print x, y, w, h
   
            cv2.imwrite("%s/%s/noise/%s.png" % (crop_dir, video_folder, frame), img[y:y+h, x:x+w])

def OCR_noise(video_folder):
    if not os.path.exists(os.path.join(ocr_dir, video_folder, 'noise')):
        os.mkdir(os.path.join(ocr_dir, video_folder, 'noise'))
    
    out_folder = os.path.join(ocr_dir, video_folder, 'noise')
    images_folder = os.path.join(crop_dir, video_folder, 'noise')

    for img in os.listdir(images_folder):
        if not img.endswith(".png"):
            continue
        
        img_path = os.path.join(images_folder, img)
        filename = os.path.splitext(img)[0] + '.json'
        outfile = os.path.join(out_folder, filename)

        if os.path.exists(outfile):
            continue

        print img_path
        try:
            extract_text(img_path, outfile)
        except Exception as e:
            print e
            print img_path


def batch_crop():
    db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})

    sql = 'select id, title from playlists where used = 1'
    sql2 = 'select hash, title from videos where playlist = ? and used = 1 order by list_order'
    res = db.querymany(sql)
    for list_id, title in res:
        list_folder = os.path.join(video_dir, list_id)
        if os.path.exists(list_folder):
            continue
        
        print list_id
        videos = db.querymany(sql2, list_id)
        for video_hash, video_title in videos:
            video_title = video_title.strip()
            video_folder = video_title + '_' + video_hash
            print video_folder

            crop_noisy_frame(video_folder)

def main():
    db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})

    sql = 'select id, title from playlists where used = 1'
    sql2 = 'select hash, title from videos where playlist = ? and used = 1 order by list_order'
    res = db.querymany(sql)
    for list_id, title in res:
        list_folder = os.path.join(video_dir, list_id)

        print list_id
        videos = db.querymany(sql2, list_id)
        for video_hash, video_title in videos:
            video_title = video_title.strip()
            video_folder = video_title + '_' + video_hash

            OCR_noise(video_folder)

if __name__ == '__main__':
    main()