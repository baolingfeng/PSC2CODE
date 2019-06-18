import os
import json
import sys
import numpy as np
from model import VGG
sys.path.append('../../')
from training_options import *
from load_data import load_data
import matplotlib.pyplot as plt
from vis.visualization import overlay
from vis.visualization.saliency import visualize_cam
# make images folder
os.mkdir('Images/')
# load data from file
X_TRAIN,Y_TRAIN,X_TEST,Y_TEST = load_data(prefix='../../')
# class options
two_options = {0:'code',1:'nc'}
four_options = {0:'code',1:'partially',2:'handwritten',3:'nc'}
# training option functions
functions = [code_vs_no_code_strict,code_vs_no_code_partially,code_vs_no_code_partially_handwritten,handwritten_vs_else,all_four]
for f in functions:
    # get data, model and weights file name from training options function
    x_train,y_train,x_test,y_test,model,weights = f(X_TRAIN,Y_TRAIN,X_TEST,Y_TEST)
    # load weights file
    model.load_weights('../../'+weights)
    # make directory for images
    os.mkdir('Images/'+weights.replace('.h5','/'))
    # predict classes for testing images
    predicitions = model.predict(x_test)
    # set options
    if len(y_test[0]) > 2:
        options = four_options
    else:
        options = two_options
    # iterate over all the predictions to produce cam
    for i in range(len(predicitions)):
        # get class label from prediction
        code = np.argmax(predicitions[i])
        # label photo as correct/incorrect with label predicted
        if np.argmax(y_test[i]) == code:
            name = 'correct ' + options[code]
        else:
            name = 'Actual ' + options[np.argmax(y_test[i])] + ' Predicted ' + options[code]

        location = 'Images/'+weights.replace('.h5','/')+str(i)+name
        cam = visualize_cam(model,len(model.layers)-1,code,x_test[i].reshape(1,300,300,3))
        img = x_test[i]
        plt.imshow(overlay(cam,img))
        plt.savefig(location)
