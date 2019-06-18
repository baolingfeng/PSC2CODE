import keras
import numpy as np
import os
import sys
from shutil import copyfile
from load_images import load_images_json, load_video_images
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score
import json
sys.path.append('..')
from setting import *

label_dir = "Labeling/labels"


def predict_video(video, model):
    # model = keras.models.load_model('weights.h5')
    frame_labels = []
    if os.path.exists('%s/%s.json' % (label_dir, video)):
        print 'has labeled...'
        images, labels, frames = load_images_json(video, label_dir=label_dir, image_dir=images_dir)
        print frames
        print labels
        for idx, frame in enumerate(frames):
            frame_labels.append((frame, labels[idx][0]))
    else:
        images, filter_frames = load_video_images(video, image_dir=images_dir)
        predicted = model.predict(np.array(images))

        for idx, frame in enumerate(filter_frames):
            prediction = np.argmax(predicted[idx])                
            frame_labels.append((frame, 1-prediction))
    
    frame_labels = sorted(frame_labels, key=lambda x: x[0])
    with open(os.path.join(images_dir, video, "predict.txt"), "w") as fout:
        fout.write("1\n")
        fout.write(",".join([str(frame) for frame, label in frame_labels if label == 1]) + "\n")
        fout.write("0\n")
        fout.write(",".join([str(frame) for frame, label in frame_labels if label == 0]) + "\n")


def load_model(model_file):
    # return keras.models.load_model('weights-new.h5')
    return keras.models.load_model(model_file)


def main():
    from dbimpl import DBImpl

    model = keras.models.load_model('weights.h5')
    print 'finish loading model'

    print video_dir, images_dir

    db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})
    sql = 'select id, title from playlists where used = 1'
    sql2 = 'select hash, title from videos where playlist = ? and used = 1 order by list_order'
    
    res = db.querymany(sql)
    for list_id, title in res:
        list_folder = os.path.join(video_dir, list_id)

        # if list_id in ['PLS1QulWo1RIbfTjQvTdj8Y6yyq4R7g-Al', 'PLFE2CE09D83EE3E28', 'PLE7E8B7F4856C9B19', 'PL27BCE863B6A864E3']:
            # continue
        print list_id
        
        videos = db.querymany(sql2, list_id)
        for video_hash, video_title in videos:
            # video_path = os.path.join(list_folder, video_title + "_" + video_hash + ".mp4")

            video = video_title + "_" + video_hash

            print video 
            predict_video(video, model)

    

  

if __name__ == '__main__':
    main3()