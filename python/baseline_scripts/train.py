import cv2
from darkflow.net.build import TFNet

options = {"model": "cfg/tiny-yolo-voc-1c.cfg", 
        #    "load": "bin/tiny-yolo-voc.weights",
           "batch": 16,
           "epoch": 100,
           "gpu": 1.0,
           "train": True,
           "annotation": "./annotations/",
           "dataset": "./images/"}

tfnet = TFNet(options)

tfnet.train()