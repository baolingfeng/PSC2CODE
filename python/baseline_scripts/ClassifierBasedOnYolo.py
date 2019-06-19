import cv2
from darkflow.net.build import TFNet
import matplotlib.pyplot as plt
import os
import lxml.etree as etree
import pandas as pd
import random
import math

#%config InlineBackend.figure_format = 'svg'
#4000, 3750, 3625, 3500, 3375, 3250
options = {
    'model': 'cfg/tiny-yolo-voc-1c.cfg',
    'load': 22875,
    'threshold': 0.1,
    'gpu': .7
}
tfnet = TFNet(options)

#for non-ide
img_folder=r"E:\karim\partiallyvisible"
outputDir=r"E:\karim\partiallyvisible\WronglyPredicted"


lstRows=[]

wronglyDetected=0
for n, image_file in enumerate(os.scandir(img_folder)):
    try:
        print(n,"  ",image_file.name)
        dRow = dict()

        path = image_file.path
        if(not path.endswith(".png")):
            continue
        # if(not image_file.name.endswith("frame3905.png")):
        #     continue

        img = image_file
        name=str(image_file.name).strip(".png")+".xml"

        img=cv2.imread(path)
        img= cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


        result = tfnet.return_predict(img)
        # print(int(result[0]['bottomright']['x']))
        if(len(result)!=0):
            tl = (result[0]['topleft']['x'], result[0]['topleft']['y'])
            br = (result[0]['bottomright']['x'], result[0]['bottomright']['y'])
            area = (br[0] - tl[0]) * (br[1] - tl[1])
            print("Confidence: ",result[0]["confidence"] )
            print("Area: ", area)
            print(tl,"  ",br)
            # result[0]["confidence"] < .3
            if (area == 0):
                print(path," Confidence", result[0]["confidence"])
                outputPath2 = os.path.join(outputDir, image_file.name)
                cv2.imwrite(outputPath2, img)
                wronglyDetected+=1
                print("Classified Wrongly")
                print(result[0]["confidence"])
                continue
            else:
                print("Classified Correctly")
        else:
            print(path, " Confidence", result[0]["confidence"])
            outputPath2 = os.path.join(outputDir, image_file.name)
            cv2.imwrite(outputPath2, img)
            wronglyDetected += 1
            print("Classified Wrongly")
            print(result[0]["confidence"])

    except Exception as e:
        print("Error in ",image_file.name)
        print(e)

print(wronglyDetected)



#for IDE


# img_folder=r"E:\karim\IDE_images"
# outputDir=r"E:\karim\IDE_images\WronglyPredicted"
# lstRows=[]
# wronglyDetected=0
# for n, image_file in enumerate(os.scandir(img_folder)):
#     try:
#         print(n,"  ",image_file.name)
#         dRow = dict()
#
#         path = image_file.path
#         if(not path.endswith(".png")):
#             continue
#         # if(not image_file.name.endswith("frame3905.png")):
#         #     continue
#
#         img = image_file
#         name=str(image_file.name).strip(".png")+".xml"
#
#         img=cv2.imread(path)
#         img= cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#
#
#         result = tfnet.return_predict(img)
#         # print(int(result[0]['bottomright']['x']))
#         if (len(result) != 0 and result[0]["confidence"] < .3 and int(result[0]['bottomright']['x'])==0):
#             print(path," Confidence", result[0]["confidence"])
#             outputPath2 = os.path.join(outputDir, image_file.name)
#             cv2.imwrite(outputPath2, img)
#             wronglyDetected+=1
#             print("Classified Wrongly")
#             print(result[0]["confidence"])
#             continue
#         else:
#             print("Classified Correctly")
#     except Exception as e:
#         print("Error in ",image_file.name)
#         print(e)
#
# print(wronglyDetected)