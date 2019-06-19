#this class is to compare between two annotations that was done by two different students



import cv2
import matplotlib.pyplot as plt
import os
import lxml.etree as etree
import pandas as pd
import random
import math
def FindGroundTruth(file,flag):
    if flag==1:
        Annotation_folder = os.path.join(r"C:\Users\Mohammad\PycharmProjects\darkflow\new_model_data\ValidateAnnotation\Annotation1",file)
    else:
        Annotation_folder = os.path.join(
            r"C:\Users\Mohammad\PycharmProjects\darkflow\new_model_data\ValidateAnnotation\Annotation2", file)
    doc = etree.parse(Annotation_folder)
    return [doc.find("object").find("bndbox").find("xmin").text,doc.find("object").find("bndbox").find("ymin").text,
                    doc.find("object").find("bndbox").find("xmax").text,doc.find("object").find("bndbox").find("ymax").text]


def bb_intersection_over_union(boxA, boxB):
    # determine the (x, y)-coordinates of the intersection rectangle
    xA = max(boxA[0], boxB[0])#maxX, boxA[0] = minX
    yA = max(boxA[1], boxB[1])#minY
    xB = min(boxA[2], boxB[2])#maxX
    yB = min(boxA[3], boxB[3])#maxY

    # compute the area of intersection rectangle
    interArea = (xB - xA + 1) * (yB - yA + 1)

    # compute the area of both the prediction and ground-truth
    # rectangles
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1) #prediction
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1) #ground-truth

    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    iou = interArea / (float(boxAArea + boxBArea - interArea))
    if(iou<0):
        iou=0

    # return the intersection over union value
    return iou


img_folder=r"C:\Users\Mohammad\PycharmProjects\darkflow\new_model_data\ValidateAnnotation\Original_Images"
outputDir=r"C:\Users\Mohammad\PycharmProjects\darkflow\new_model_data\ValidateAnnotation\Result"


#for test correction
lstRows=[]
for n, image_file in enumerate(os.scandir(img_folder)):
    dRow = dict()

    path = image_file.path
    if(not path.endswith(".png")):
        continue
    # if(not image_file.name.endswith("new_27_img516.png")):
    #      continue

    img = image_file
    name=str(image_file.name)[:str(image_file.name).find(".")]
    name+=".xml"

    img=cv2.imread(path)
    img= cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    print(path)

    GroundTruth1=list(map(int, FindGroundTruth(name,1)))
    GroundTruth2 = list(map(int, FindGroundTruth(name, 2)))

    dRow['FileName'] = str(image_file.name)
    iou = bb_intersection_over_union(GroundTruth1, GroundTruth2)
    dRow["IOU"] = iou
    lstRows.append(dRow)
    img = cv2.rectangle(img,(GroundTruth1[0],GroundTruth1[1]), (GroundTruth1[2],GroundTruth1[3]), (255, 0, 0), 2)
    img = cv2.rectangle(img, (GroundTruth2[0], GroundTruth2[1]), (GroundTruth2[2], GroundTruth2[3]), (0, 255, 0), 3)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    outputPath=os.path.join(outputDir,image_file.name)
    cv2.imwrite(outputPath, img)


df = pd.DataFrame(lstRows)
print( df.sort_values(by=['IOU']))
print("\tMax: %f" % df['IOU'].max())
print("\tMin: %f" % df['IOU'].min())
print("\tAvg: %f" % df['IOU'].mean())

