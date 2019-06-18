import os
import json
import numpy as np
from keras.preprocessing.image import load_img



# label_dir = 'Labeling/labels'
# image_path = '/Volumes/MYWD/Research/VideoAnalytics/Images'
    
def load_images_json(video, target_size=(300, 300, 3), label_dir="Labeling/labels", image_dir="../Images"):
    images = []
    labels = []
    labeled_file = video + '.json'
    with open(os.path.join(label_dir, labeled_file)) as fin:
        data = json.load(fin)
        frames = data['labels']
        frames = sorted([(int(frame), frames[frame])for frame in frames], key=lambda x:x[0])
        
        for frame, label in frames:
            # print 'load frame', video, frame, label
            complete_location = "%s/%s/%d.png" % (image_dir, video, frame)
            img = np.array(load_img(complete_location,target_size=target_size))
            
            if label == "1" or label == "2":
                # copyfile(complete_location, 'Labeling/data/1/%d-%s.png' % (frame, video))
                label = [1, 0]
            else:
                # copyfile(complete_location, 'Labeling/data/0/%d-%s.png' % (frame, video))
                label = [0, 1]
            # label = [1, 0] if label == "1" else [0, 1]
            images.append(img)
            labels.append(label)
    
    return images, labels, [frame for frame, label in frames]

def load_video_images(video, target_size=(300, 300, 3), image_dir="../Images"):
    images = []
    folder = image_dir + '/' + video
    with open(os.path.join(folder, 'frames.txt')) as fin:
        lines = fin.readlines()

        # frame_num = int(lines[0].strip())
        filter_frames = [int(f) for f in lines[0].strip().split(" ")]

        for frame in filter_frames:
            complete_location = "%s/%d.png" % (folder, frame)
            img = np.array(load_img(complete_location,target_size=target_size))

            images.append(img)
    
    return np.array(images), filter_frames

def load_train_images(target_size=(300,300,3), label_dir="Labeling/labels"):
    print 'loading images...'

    images = []
    labels = []
    for f in os.listdir(label_dir):
        if not f.endswith(".json"):
            continue
        
        video = f[:-5]
        one_images, one_labels = load_images_json(video)
        images.extend(one_images)
        labels.extend(one_labels)
    
    return np.array(images), np.array(labels)

