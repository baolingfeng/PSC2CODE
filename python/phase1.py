import sys, os
from preprocess import extract_frames, diff_frames
from dbimpl import DBImpl
from setting import *


def run(metric="SSIM", thre=0.05):
    out_dir = os.path.join(working_dir, "Phase1", metric)

    db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})
    sql = 'select hash, title, playlist from videos where hash = ?'

    with open("verified_videos.txt") as fin:
            for line in fin.readlines():
                video_hash = line.strip()
                video_hash, video_title, video_playlist = db.queryone(sql, video_hash)

                # print video_title, video_hash

                video = video_title.strip() + '_' + video_hash

                video_file = video + ".mp4"
                video_path = os.path.join(video_dir, video_playlist, video_file)

                if(not os.path.exists(video_path)):
                    video_file = video_title.strip() + ".mp4"
                    video_path = os.path.join(video_dir, video_playlist, video_file)

                # print video_path
                out_folder = os.path.join(out_dir, video)
                if os.path.exists(out_folder):
                    # os.rmdir(out_folder)
                    continue
                else:
                    os.mkdir(out_folder)

                extract_frames(video_path, out_folder=out_folder)
                diff_frames(out_folder, thre=thre, metric=metric)

                # break

def stat(metric="SSIM"):
    out_dir = os.path.join(working_dir, "Phase1", metric)

    db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})
    sql = 'select hash, title, playlist from videos where hash = ?'
    total = 0
    with open("verified_videos.txt") as fin:
        for line in fin.readlines():
            video_hash = line.strip()
            video_hash, video_title, video_playlist = db.queryone(sql, video_hash)

            # print video_title, video_hash

            video = video_title.strip() + '_' + video_hash
            frame_folder = os.path.join(out_dir, video)

            with open(os.path.join(frame_folder, 'frames.txt')) as fin2:
                line = fin2.readlines()[0]
                print(len(line.split()))
                total += len(line.split())
    print total

def compare():
    out_dir1 = os.path.join(working_dir, "Phase1", "SSIM")
    out_dir2 = os.path.join(working_dir, "Phase1", "NRMSE")

    db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})
    sql = 'select hash, title, playlist from videos where hash = ?'
    total = 0
    with open("verified_videos.txt") as fin:
        for line in fin.readlines():
            video_hash = line.strip()
            video_hash, video_title, video_playlist = db.queryone(sql, video_hash)

            # print video_title, video_hash

            video = video_title.strip() + '_' + video_hash
            frame_folder = os.path.join(out_dir1, video)

            with open(os.path.join(frame_folder, 'frames.txt')) as fin2:
                line = fin2.readlines()[0]
                frames1 = line.split()
            
            video = video_title.strip() + '_' + video_hash
            frame_folder = os.path.join(out_dir2, video)

            with open(os.path.join(frame_folder, 'frames.txt')) as fin2:
                line = fin2.readlines()[0]
                frames2 = line.split()

            print len(set(frames1)-set(frames2)), len(set(frames2)-set(frames1))


if __name__ == "__main__":
    # run(metric="SSIM")
    # run(metric="SSIM", thre=0.1)
    # run(metric="NRMSE", thre=0.05)
    stat(metric="SSIM")
    # compare()



