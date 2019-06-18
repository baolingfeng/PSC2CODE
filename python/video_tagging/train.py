import os
import sys
import json
import numpy as np
from keras.preprocessing.image import load_img
from keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import ModelCheckpoint,EarlyStopping,TensorBoard
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split, KFold
from keras.applications.inception_v3 import InceptionV3
from keras.applications.vgg16 import VGG16
from keras.models import Model
from keras.layers import Dense, GlobalAveragePooling2D, Input,Conv2D, MaxPooling2D, UpSampling2D
from keras import backend as K
from keras.optimizers import SGD
import keras
import pandas as pd
sys.path.append('Models/CNN/')
from model import Inception,VGG
from shutil import copyfile
sys.path.append('../')
from setting import *
import time
import random
from split_dataset import load_splitted_images

random.seed(0)

print K.tensorflow_backend._get_available_gpus()

def train_model(batch_size=32, epochs=100, PATIENCE=20, train_file="train.csv", test_file="test.csv", model_file="weights.h5"):

    log = open('log.txt','a')
    input_shape = (300,300,3)

    (x_train, x_test, y_train, y_test) = load_splitted_images(target_size=input_shape, train_file=train_file, test_file=test_file)
    print len(x_train), len(x_test)

    start_time = time.time()

    try:
        model = keras.models.load_model(model_file)
    except Exception as e:
        print 'cannot find existing model', e
        input_tensor = Input(shape=input_shape)
        base_model = VGG16(input_tensor=input_tensor, include_top=False)

        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        predictions = Dense(2, activation='softmax')(x)

        # this is the model we will train
        model = Model(inputs=base_model.input, outputs=predictions)

        # first: train only the top layers (which were randomly initialized)
        # i.e. freeze all convolutional InceptionV3 layers
        for layer in base_model.layers:
            layer.trainable = False

        # compile the model (should be done *after* setting layers to non-trainable)
        model.compile(optimizer='rmsprop', loss='categorical_crossentropy',metrics=['accuracy'])

    datagen = ImageDataGenerator(
                width_shift_range=0.1,
                height_shift_range=0.1,
                zoom_range=0.2,
                fill_mode='nearest')
    datagen.fit(x_train)

    # Callbacks
    tb = TensorBoard(log_dir='logs', histogram_freq=0, write_graph=True, write_images=True)
    es = EarlyStopping(monitor='val_acc', min_delta=0, patience=PATIENCE, verbose=0, mode='auto')
    w = ModelCheckpoint(model_file, monitor='val_acc', verbose=1, save_best_only=True, mode='max')
    
    # Training
    history = model.fit_generator(datagen.flow(x_train, y_train,
        batch_size=batch_size),
        steps_per_epoch=x_train.shape[0] // batch_size,
        epochs=epochs,
        validation_data=(x_test, y_test),
        callbacks=[tb,es,w])

    model.save(model_file)
    log.write("--- %s seconds are used to finish ---\n" % (time.time() - start_time))
    log.write(',ValAcc:'+"{0:.2f}".format(100*max(history.history['val_acc']))+'\n')
    

if __name__ == "__main__":
    train_model(epochs=100, PATIENCE=20, train_file="train.csv", test_file="test.csv", model_file="weights.h5")
