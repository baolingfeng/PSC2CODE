import os, sys
from setting import *
from dbimpl import DBImpl
from preprocess import extract_frames, diff_frames
from video_tagging.predict import predict_video
from video import CVideo
from OCR.image_ocr import google_ocr
from OCR.adjust_ocr import GoogleOCRParser

def get_video_info(video_hash):
    db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})
    sql = 'select title, playlist from videos where hash = ?'
    res = db.queryone(sql, video_hash)
    video_name = res[0].strip()
    video_playlist = res[1].strip()

    return [video_hash, video_name, video_playlist]


if __name__ == "__main__":
    video_hash = 'GnLtvmeGAWA'

    video_hash, video_name, video_playlist = get_video_info(video_hash)
    print(video_hash, video_name, video_playlist)

    video = video_name + '_' + video_hash # The name of video is in format of its title + hash 
    video_mp4_path = os.path.join(video_dir, video_playlist, video+".mp4")

    # preprocess if not
    if not os.path.exists(os.path.join(images_dir, video)): 
        preprocess_video(video_mp4_path, out_folder=os.path.join(images_dir, video))
        extract_frames(video_mp4_path, os.path.join(images_dir, video))
        diff_frames(os.path.join(images_dir, video), thre=0.05, metric="NRMSE")

    # predict whether a frame is valid or not
    if not os.path.exists(os.path.join(images_dir, video, 'predict.txt')): 
        predict_video(os.path.join(images_dir, video), model_file="video_tagging/weights.h5")
    
    if not os.path.exists(os.path.join(lines_dir, video)):
        os.mkdir(os.path.join(lines_dir, video))
        
        cvideo = CVideo(video)
        # detect boundingx boxes and store the information of lines and rects into folder 'Lines'
        cvideo.cluster_lines()
        cvideo.adjust_lines()
        cvideo.detect_rects()
        # crop the bounding boxes of frames into folder 'Crops'
        cvideo.crop_rects()
    
    # OCR and the results are stored into folder 'GoogleOCR'
    if not os.path.exists(os.path.join(ocr_dir, video)):
        google_ocr(video_name, video_hash)

    # correct ocr errors
    if not os.path.join(ocr_dir, video, "parse", "correct.json"):
        srt_file = os.path.join(video_dir, video_playlist, video+".srt")
        parser = GoogleOCRParser(video, srt_file)
        parser.correct_words()
