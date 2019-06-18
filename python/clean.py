import os
import shutil
import subprocess
from dbimpl import DBImpl
from setting import *

def os_copy_folder(src_folder, dist_folder):
    cmd = ["cp", "-a", "%s/." % src_folder, dist_folder]

    if not os.path.exists(dist_folder):
        os.mkdir(dist_folder)
    
    subprocess.call(cmd)


def os_mv_folder(src_folder, dist_folder):
    os_copy_folder(src_folder, dist_folder)

    shutil.rmtree(src_folder)   

def os_rm_folder(folder):
    if os.path.exists(folder):
        shutil.rmtree(folder) 
       

db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})
sql = 'select id, title from playlists where used = 1'
sql2 = 'select hash, title, playlist from videos where playlist = ? and used = 1 order by list_order'

res = db.querymany(sql)
playlists = [(r[0], r[1]) for r in res]

playlist_videos = []
for list_id, title in playlists:
    videos = db.querymany(sql2, list_id)
    playlist_videos.extend(videos)

video_folders = [video_title.strip() + '_' + video_hash for video_hash, video_title, playlist in playlist_videos]

def clean_folder(folder):
    for video_folder in os.listdir(folder):
        fullpath = os.path.join(folder, video_folder)
        if not os.path.isdir(fullpath):
            continue
        
        if video_folder not in video_folders:
            print video_folder

            os_rm_folder(fullpath)
            # dist_path = os.path.join("/Volumes/Seagate/VideoAnalytics/Images2", video_folder)
            
            # os_mv_folder(fullpath, dist_path)   

            # break

def has_cropped_folder():
    for video_folder in video_folders:
        fullpath = os.path.join(crop_dir, video_folder)
        if not os.path.exists(fullpath):
            print video_folder


def clean_videos(clean_dir = '/media/blf/MYWD/TOSEM-Video'):
    playlist_dir = os.path.join(clean_dir, 'Videos')

    playlists = [video_playlist.strip() for video_hash, video_name, video_playlist in playlist_videos]
    
    pnum = 0
    vnum = 0
    for p in os.listdir(playlist_dir):
        if p not in playlists:
            print('removing playlist', p)
            shutil.rmtree(os.path.join(playlist_dir, p))   
        else:
            pnum += 1
            video_list = [video_name.strip() + '_' + video_hash for video_hash, video_name, video_playlist in playlist_videos if video_playlist == p]
            video_list2 = [video_name.strip() for video_hash, video_name, video_playlist in playlist_videos if video_playlist == p]
            vvnum = 0
            for v in os.listdir(os.path.join(playlist_dir, p)):
                if not v.endswith('.mp4'):
                    # print(v)
                    continue
                
                v2 = v[:-4]
                if v2 not in video_list:
                    if v2 not in video_list2:
                        os.remove(os.path.join(playlist_dir, p, v))
                        srt_file = os.path.join(playlist_dir, p, v2+".srt")
                        if os.path.exists(srt_file):
                            print srt_file
                            os.remove(srt_file)
                    else:
                        vnum += 1
                        idx = video_list2.index(v2)
                        new_name = video_list[idx]
                        os.rename(os.path.join(playlist_dir, p, v2+".mp4"), os.path.join(playlist_dir, p, new_name+".mp4"))
                        print('rename...', v2, new_name)
                        srt_file = os.path.join(playlist_dir, p, v2+".srt")
                        if os.path.exists(srt_file):
                            os.rename(os.path.join(playlist_dir, p, v2+".srt"), os.path.join(playlist_dir, p, new_name+".srt"))
                else:
                    vnum += 1
            # print(p, vvnum)
                    # 
    print(pnum, vnum)        

def clean_images(clean_dir = '/media/blf/MYWD/TOSEM-Video'):
    for video_hash, video_name, video_playlist in playlist_videos:
        video_images = os.path.join(images_dir, video_name.strip()+'_'+video_hash)

        if os.path.exists(video_images):
            pass
            # print('copying', video_name.strip()+'_'+video_hash)
            # os_copy_folder(video_images, os.path.join(clean_dir, "Images", video_name.strip()+'_'+video_hash))
        else:
            print('not exist', video_name.strip()+'_'+video_hash)

def main():
    # local_images_dir = os.path.join(working_dir, "Crops")
    # clean_folder(images_dir)
    # has_cropped_folder()
    clean_images()

if __name__ == '__main__':
    main()