import os
import sys, cv2, math, numpy
import phase1, phase2, time
import json

sys.path.append('../../python')
from dbimpl import DBImpl
from setting import *


video_hash = 'ck39jt04Qpk'
# video_hash = 'GnLtvmeGAWA'
# video_hash = 'OF3vBYWikYs'

def extract_frames(video_hash):
    db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})
    sql = 'select title, playlist from videos where hash = ?'
    res = db.queryone(sql, video_hash)
    video_name = res[0].strip()
    video_playlist = res[1].strip()

    video_file = video_name + "_" + video_hash + ".mp4"
    video_path = os.path.join(video_dir, video_playlist, video_file)

    if(not os.path.exists(video_path)):
        video_file = video_name + ".mp4"
        video_path = os.path.join(video_dir, video_playlist, video_file)

    video = cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    # fps = math.ceil(fps)
    # fps = 30

    frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
    print('video fps/frame count:', fps, "/", frame_count)

    extract_folder = '../public/Images/%s_%s' % (video_name, video_hash)
    main_folder = '../public/extracts/%s_%s/main' % (video_name, video_hash)

    second = 1

    filter_frames = []
    frame_seg = {}
    seg_frame = {}
    while True:
        frame_num = math.ceil(second * fps) + 1
        for seg in range(1, 4):
            file_path = os.path.join(main_folder, 'frame%d-segment%d.txt' % (frame_num, seg))
            print(file_path)
            if os.path.exists(file_path):
                # print 'found', frame_num
                if frame_num not in filter_frames:
                    filter_frames.append(frame_num)
                    frame_seg[frame_num] = [seg]
                else:
                    frame_seg[frame_num].append(seg)

                if seg in seg_frame:
                    seg_frame[seg].append(frame_num)
                else:
                    seg_frame[seg] = [frame_num]

        second += 1

        if frame_num > frame_count:
            break

    # print filter_frames
    # print [int(math.floor((f)/fps)) for f in filter_frames]

    for f in frame_seg:
        if len(frame_seg[f]) > 1:
            print f

    for s in seg_frame:
        print(s, len(seg_frame[s]))

    # success, image = video.read()
    # prev = numpy.zeros(image.shape, numpy.uint8)
    # time1, time2 = 0, 0
    # fnum = 0
    # while success:
    #     fnum += 1
    #     t_min = int((fnum/fps)/60)
    #     t_sec = int(math.floor((fnum/fps)%60)) #check
        

    #     if fnum in filter_frames:
    #         # print fnum, t_sec
    #         cv2.imwrite(os.path.join(extract_folder, "%d.png" % (t_min * 60 + t_sec)), image)

    #     success, image = video.read()

    # with open(os.path.join(extract_folder, "frames.txt"), "w") as fout:
    #     fout.write(' '.join([str(int(math.floor((f)/fps))) for f in filter_frames]))


def stat_valid(video_hash):
    db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})
    sql = 'select title, playlist from videos where hash = ?'
    res = db.queryone(sql, video_hash)
    video_name = res[0].strip()

    # image_folder = '../public/Images/%s_%s' % (video_name, video_hash)
    image_folder = images_dir + '/%s_%s' % (video_name, video_hash)

    with open(os.path.join(image_folder, 'predict.json')) as fin:
        predict_info = json.load(fin)
        
        valid_count, invalid_count = 0, 0
        for f in predict_info:
            if predict_info[f]['label'] == 'valid':
                valid_count += 1
            else:
                invalid_count += 1
        
        print valid_count, invalid_count

if __name__ == "__main__":
    # extract_frames('ck39jt04Qpk')
    # GnLtvmeGAWA
    # OF3vBYWikYs
    stat_valid('ck39jt04Qpk')