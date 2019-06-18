import cv2
import numpy as np
import subprocess
import sys, os

from dbimpl import DBImpl
from setting import *

def main():
    db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})
    sql = 'select hash, title from videos'
    videos = db.querymany(sql)
    for v in videos:
        # print v[0], v[1]
        frame_folder = os.path.join(crop_dir, v[1].strip())
        if os.path.exists(os.path.join(crop_dir, v[1].strip())):
            print v[0], v[1]
            new_folder = os.path.join(crop_dir, v[1].strip()+'_'+v[0].strip())
            os.rename(frame_folder, new_folder)

            # break
   
if __name__ == '__main__':
    main()