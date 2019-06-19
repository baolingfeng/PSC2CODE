import cv2
import skimage.measure
import os
import subprocess
from setting import *

def extract_frames(video_path, out_folder):
    '''
    using ffmpeg to generate frames in seconds, the frames is genereted into #out_folder#
    '''
    filename = os.path.split(video_path)[-1]
    idx = filename.rfind(".")
    filename = filename[0:idx]

    # ffmpeg -i "$file" -r 1 -f image2 "$images/$filename/%d.png" -nostdin
    cmds = ["ffmpeg", "-i", video_path, "-r", "1", "-f", "image2", out_folder+"/%d.png", "-nostdin"]
    
    print ' '.join(cmds)
    subprocess.call(cmds)

def diff_frames(frame_folder, thre=0.05, metric="NRMSE"):
    '''
    The duplicated frames would be deleted and the file 'frames.txt' contains the name of the filtered frames
    @param frame_folder: the location of video frames 
    @param thre: threhold of dissimilarity
    @param metris: NRMSE or SSIM
    '''
    print("used parameters: ", thre, "/", metric == 'SSIM')
    fout = open("%s/frames.txt" % frame_folder, "w")

    frame_seq = []
    for frame in os.listdir(frame_folder):
        if not frame.endswith(".png"):
            continue

        frame_seq.append(int(frame[0:-4]))

    frame_seq = sorted(frame_seq)

    filter_frames = []
    pre_img = None
    for frame in frame_seq:
        img = cv2.imread("%s/%d.png" % (frame_folder, frame))
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        if pre_img is not None:
            if metric == 'SSIM':
                sim = 1 - skimage.measure.compare_ssim(pre_img, img_gray)
            else:
                sim = skimage.measure.compare_nrmse(pre_img, img_gray)

            if sim > thre:
                pre_img = img_gray
                filter_frames.append(frame)
            else:
                os.remove("%s/%d.png" % (frame_folder, frame))
        else:
            pre_img = img_gray
            filter_frames.append(frame)
    
    print "filtered frame number", len(filter_frames)
    fout.write(" ".join([str(f) for f in filter_frames]))
    fout.close()


def main(): # batch processing for the videos in the dataset
    from dbimpl import DBImpl

    db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})
    sql = 'select id, title from playlists where used = 1'
    sql2 = 'select hash, title from videos where playlist = ? and used = 1 order by list_order'
    res = db.querymany(sql)
    for list_id, title in res:
        list_folder = os.path.join(video_dir, list_id)
        if not os.path.exists(list_folder):
            continue

        print list_id
        videos = db.querymany(sql2, list_id)
        for video_hash, video_title in videos:
            video_path = os.path.join(list_folder, video_title + "_" + video_hash + ".mp4")

            if not os.path.exists(video_path):
                continue
            print video_path

            video = video_title + "_" + video_hash
            out_folder = os.path.join(images_dir, video)
            if os.path.exists(out_folder):
                continue
            else:
                os.mkdir(out_folder)

            extract_frames(video_path, out_folder=out_folder)
            diff_frames(out_folder)

if __name__ == '__main__':
    main()