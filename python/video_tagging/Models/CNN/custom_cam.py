import os
import json
import sys
import numpy as np
from model import VGG
sys.path.append('../../')
from training_options import *
import matplotlib.pyplot as plt
from load_data import load_custom
from vis.visualization import overlay
from vis.visualization.saliency import visualize_cam

shape = (500,500,3)
# load data from file
images = load_custom('jp_Images/')
# class options
two_options = {0:'code',1:'nc'}
four_options = {0:'code',1:'partially',2:'handwritten',3:'nc'}
# java-python class options
two_options = {0:'Java',1:'Python'}
four_options = {0:'Java',1:'Python',2:'NC'}
# training option functions
weights = ['code_vs_no_code_strict.h5','code_vs_no_code_partially.h5','code_vs_no_code_partially_handwritten.h5','handwritten_vs_else.h5','all_four.h5']
# java-python weight training ops
weights = ['java_python.h5']#,'java_python_no_code.h5','java_python_pv_no_code.h5']
for weight in weights:
    if weight == 'all_four.h5':
        options = four_options
        model = VGG(shape,4)
    else:
        options = two_options
        model = VGG(shape,2)
    # load weights file
    model.load_weights('../../jp_Fold_0/'+weight)
    # make directory for images
    os.mkdir('jp_Images/'+weight.replace('.h5','/'))
    # predict classes for testing images
    predicitions = model.predict(images)

    # iterate over all the predictions to produce cam
    for i in range(len(predicitions)):
        # get class label from prediction
        code = np.argmax(predicitions[i])
        # label photo
        name = '_Predicted ' + options[code]

        location = 'jp_Images/'+weight.replace('.h5','/')+str(i)+name
        cam = visualize_cam(model,len(model.layers)-1,code,images[i].reshape((1,)+shape))
        img = images[i]
        plt.imshow(overlay(cam,img))
        plt.savefig(location)
