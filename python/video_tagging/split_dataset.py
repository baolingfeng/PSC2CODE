import os, sys
import json
import numpy as np
from keras.preprocessing.image import load_img
from sklearn.model_selection import train_test_split, KFold
sys.path.append('../')
from setting import *

image_path = images_dir

def load_images(target_size=(300,300,3), label_dir = '../../webapp/labels'):
    print 'loading images...'

    images = []
    labels = []
    image_frames = []
    for f in os.listdir(label_dir):
        if not f.endswith(".json"):
            continue

        video = f[:-5]
        if not os.path.exists(os.path.join(image_path, video)):
            continue

        with open(os.path.join(label_dir, f)) as fin:
            data = json.load(fin)
            frames = data['labels']
            frames = sorted([(int(frame), frames[frame])for frame in frames], key=lambda x:x[0])
            
            for frame, label in frames:
                # print 'load frame', video, frame, label
                complete_location = "%s/%s/%d.png" % (image_path, video, frame)
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
                image_frames.append((video, frame))
    
    return np.array(images), np.array(labels), np.array(image_frames)

def load_splitted_images(target_size=(300,300,3), train_file="train.csv", test_file="test.csv"):
    train_images = []
    train_labels = []
    with open("train.csv") as fin:
        for line in fin.readlines():
            video, frame, label = line.strip().split(",")

            complete_location = "%s/%s/%s.png" % (image_path, video, frame)

            train_images.append(np.array(load_img(complete_location,target_size=target_size)))
            label = [1, 0] if label.strip() == "1" else [0, 1]
            train_labels.append(label)
    
    test_images = []
    test_labels = []
    with open("test.csv") as fin:
        for line in fin.readlines():
            video, frame, label = line.strip().split(",")
            # print frame, label

            complete_location = "%s/%s/%s.png" % (image_path, video, frame)

            test_images.append(np.array(load_img(complete_location,target_size=target_size)))
            label = [1, 0] if label.strip() == "1" else [0, 1]
            test_labels.append(label)
    
    return np.array(train_images), np.array(test_images), np.array(train_labels), np.array(test_labels)

def split_train_test(train_file="train.csv", test_file="test.csv"):
    images, labels, image_frames = load_images()

    # print len([for l in labels if l[0] == 1]), len([for l in labels if l[0] == 0])

    (x_train, x_test, y_train, y_test, train_frames, test_frames) = train_test_split(images, labels, image_frames, test_size=0.1, random_state=42)

    print len([e[0] for e in y_train if e[0] == 1]), len([e[0] for e in y_train if e[0] == 0])
    print len([e[0] for e in y_test if e[0] == 1]), len([e[0] for e in y_test if e[0] == 0])


    # (x_train, x_test, y_train, y_test) = load_splitted_images()
    with open(train_file, "w") as fout:
        for idx, (video, frame) in enumerate(train_frames):
            fout.write('%s,%s,%d\n' % (video, frame, y_train[idx][0])) 

    with open(test_file, "w") as fout:
        for idx, (video, frame) in enumerate(test_frames):
            fout.write('%s,%s, %d\n' % (video, frame, y_test[idx][0])) 


if __name__ == "__main__":
    split_train_test("train.csv", "test.csv")
