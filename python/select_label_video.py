import os
from dbimpl import DBImpl
from setting import *

db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})
sql = 'select id, title from playlists where used = 1'
sql2 = 'select hash, title from videos where playlist = ? and used = 1 order by list_order'
res = db.querymany(sql)
total_video_num = 0
for list_id, title in res:

    list_folder = os.path.join(video_dir, list_id)
    # if not os.path.exists(list_folder):
    #     continue

    videos = db.querymany(sql2, list_id)

    video_frame_stat = {}
    video_num = 0
    for video_hash, video_title in videos:
        video = video_title.strip() + "_" + video_hash
        
        image_path = os.path.join(images_dir, video)
        if not os.path.exists(image_path):
            continue
        
        # print video_title, video_hash
        video_num += 1

    total_video_num += video_num
    print list_id, title, video_num

print total_video_num
    #     with open(os.path.join(image_path, "frames.txt")) as fin:
    #         lines = fin.readlines()
    #         frames = [int(f) for f in lines[0].split()]

    #         video_frame_stat[video]= len(frames)
    #         # print len(frames)

    # video_frame_stat= sorted([(k, video_frame_stat[k]) for k in video_frame_stat], key=lambda x:x[1], reverse=True)
    
    # for idx, (video, frame_num) in enumerate(video_frame_stat):
    #     if idx > 3:
    #         break

    #     print video, frame_num
    #     break
 