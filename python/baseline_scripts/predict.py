import os, sys
import json
import cv2
from darkflow.net.build import TFNet
from json import JSONEncoder, JSONDecoder
import pickle
import numpy

sys.path.append('../')
from dbimpl import DBImpl
from setting import *



db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})

class PythonObjectEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (list, dict, str, unicode, int, float, bool, type(None))):
            return JSONEncoder.default(self, obj)
        elif isinstance(obj, numpy.floating):
            return float(obj)
        return {'_python_object': pickle.dumps(obj)}


def predict():
    options = {"model": "cfg/tiny-yolo-voc-1c.cfg",
            "load": -1,
            'threshold': 0.1
            #    "gpu": 1.0
            }

    tfnet = TFNet(options)

    tfnet.load_from_ckpt()

    Total_TP, Total_FP, Total_TN, Total_FN = 0, 0, 0, 0
    with open("../verified_videos.txt") as fin, open('predict_results.csv', 'w') as fout, open('predict_results_detail.json', 'w') as fout2:
        sql = 'select hash, title from videos where hash = ?'

        result_detail = {}
        for line in fin.readlines():
            video_hash = line.strip()
            video_hash, video_title = db.queryone(sql, video_hash)

            print(video_title, video_hash)

            video = video_title.strip() + '_' + video_hash
            
            result_detail[video] = {}
            with open(os.path.join(images_dir, video, "predict.json")) as fin2:
                predict_info = json.load(fin2)

            with open(os.path.join(images_dir, video, "frames.txt")) as fin2:
                frames = fin2.readlines()[0].split()
                
                TP, FP, TN, FN = 0, 0, 0, 0
                for frame in frames:
                    img_path = os.path.join(images_dir, video, frame+'.png')
                    frame_img = cv2.imread(img_path)
                    frame_img = cv2.cvtColor(frame_img, cv2.COLOR_BGR2RGB)

                    results = tfnet.return_predict(frame_img)
                    # print results
                    
                    if str(frame) not in predict_info:
                        continue

                    result_detail[video][str(frame)] = results
                    hasCode = False
                    for r in results:
                        if r['label'] == 'Code':
                            # print frame, predict_info[str(frame)]['label'], 'Code Region:', r['topleft'], r['bottomright']
                            hasCode = True
                            if predict_info[str(frame)]['label'] == "valid":
                                TP += 1
                            else:
                                FP += 1
            
                    
                    if not hasCode:
                        # print frame, predict_info[str(frame)]['label'], ' No Code Region'
                        if predict_info[str(frame)]['label'] == "invalid":
                            TN += 1
                        else:
                            FN += 1
                
                print(TP, FP, TN, FN)
                precison1 = TP*1.0/(TP+FP) if TP+FP != 0 else 0
                recall1 = TP*1.0/(TP+FN) if TP+FN != 0 else 0
                precison2 = TN*1.0/(TN+FN) if TN+FN != 0 else 0
                recall2 = TN*1.0/(TN+FP) if TN+FP != 0 else 0
                fout.write('%s,%s,%d,%d,%d,%d,%.2f,%.2f,%.2f,%.2f,%.2f\n' % (video_title, video_hash, TP, FP, TN, FN, (TP+TN)*1.0/(TP+TN+FP+FN), precison1, recall1, precison2, recall2))
                Total_TP += TP
                Total_FP += FP
                Total_TN += TN
                Total_FN += FN

        json.dump(result_detail, fout2, indent=4, cls=PythonObjectEncoder)        

    print(Total_TP, Total_FP, Total_TN, Total_FN, (Total_TP + Total_TN)*1.0/(Total_TP+Total_FP+Total_TN+Total_FN))


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

def bb_contours(img):
    image = cv2.imread(img, 1)

    ratio = image.shape[0] / 300.0


    # convert the image to grayscale, blur it, and find edges
    # in the image
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(gray, 30, 200)
    contours, hierarchy = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # im2, contours, hierarchy = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    try:
        hierarchy = hierarchy[0]
    except:
        hierarchy = []

    height, width, _ = image.shape
    min_x, min_y = width, height
    max_x = max_y = 0

    # computes the bounding box for the contour, and draws it on the frame,
    i = 0
    AllContours=[]
    for contour, hier in zip(contours, hierarchy):
        (x, y, w, h) = cv2.boundingRect(contour)
        min_x, max_x = min(x, min_x), max(x + w, max_x)
        min_y, max_y = min(y, min_y), max(y + h, max_y)

        if w > 80 and h > 80:
            #cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 2)
            AllContours.append([x,y,x+w,y+h])
            i += 1

    # print("IMAGE:",img," Contours",AllContours)
    # if max_x - min_x > 0 and max_y - min_y > 0:
    #     cv2.rectangle(image, (min_x, min_y), (max_x, max_y), (255, 0, 0), 2)

    #cv2.imshow("H", image)
    return AllContours

def contourCorrection(bb_box,imgPath):
    # print(imgPath)
    predictedBox = [bb_box[0]['topleft']['x'], bb_box[0]['topleft']['y'], bb_box[0]['bottomright']['x'],
                    bb_box[0]['bottomright']['y']]
    predictedBox = list(map(int, predictedBox))

    allContours=bb_contours(imgPath)
    maxIOU=0
    if(len(allContours)>0):
        matchedContor=allContours[0]
        for cntr in allContours:
            countor = list(map(int, cntr))
            iou = bb_intersection_over_union(predictedBox, countor)
            # print("IOU:",iou)
            if(iou > maxIOU and iou > .4):
                maxIOU=iou
                matchedContor=countor
        # print(matchedContor)
        if(maxIOU!=0):
            if(imgPath.endswith("new_27_img516.png")):
                return allContours
            else:
                return (matchedContor,maxIOU)

def IOU():
    with open('predict_results_detail.json') as fin:
        results = json.load(fin)
    
    sql = 'select hash, title from videos where hash = ?'
    with open("../verified_videos.txt") as fin, open("iou_results.csv", "w") as fout: 
        pre_iou_results = []
        for pidx, line in enumerate(fin.readlines()):
            video_hash = line.strip()
            video_hash, video_title = db.queryone(sql, video_hash)

            print(video_title, video_hash)

            video = video_title.strip() + '_' + video_hash

            predict_results = results[video]

            with open(os.path.join(images_dir, video, 'predict.json')) as fin2:
                valid_info = json.load(fin2)
            
            with open(os.path.join(lines_dir, video, 'lines.json')) as fin2:
                lines_info = json.load(fin2)
                linemap = lines_info['linemap']

            iou_results = []
            for frame in predict_results:
                CodeIndex = -1
                Conf = 0
                for idx, r in enumerate(predict_results[frame]):
                    if r['label'] == 'Code' and r['confidence'] > Conf:
                        CodeIndex = idx
                        Conf = r['confidence']

                # print frame, CodeIndex, Conf, valid_info[frame]['label']
                if CodeIndex < 0  and valid_info[frame]['label'] == 'invalid':
                    iou_results.append((frame, 1, 'TN'))
                elif CodeIndex < 0 and valid_info[frame]['label'] == 'valid':
                    iou_results.append((frame, 0, 'FN'))
                elif CodeIndex >= 0 and valid_info[frame]['label'] == 'invalid':
                    iou_results.append((frame, 0, 'FP'))
                else:
                    x1, y1 = predict_results[frame][CodeIndex]['topleft']['x'],predict_results[frame][CodeIndex]['topleft']['y']
                    x2, y2 = predict_results[frame][CodeIndex]['bottomright']['x'], predict_results[frame][CodeIndex]['bottomright']['y']
                    found = False

                    img = cv2.imread(os.path.join(images_dir, video, '%s.png' % frame))
                    for c in linemap:
                        cluster = lines_info['linemap'][c]
                        if 'to_be_cropped' in cluster and not cluster['to_be_cropped']:
                            continue
                        
                        if 'rects' not in cluster or len(cluster['rects']) == 0:
                            continue

                        rect = [int(e) for e in cluster['rects'][0]]
                        img = cv2.rectangle(img, (rect[0], rect[1], rect[2], rect[3]), (0, 255, 0), 2)

                        for frame2 in cluster['frames']:
                            if int(frame) == int(frame2):
                                iou = bb_intersection_over_union((int(x1), int(y1), int(x2), int(y2)), rect)

                                if iou < 0.75:
                                    expectedContor = contourCorrection(predict_results[frame], os.path.join(images_dir, video, '%s.png' % frame))
                                    if (expectedContor is not None):
                                        if expectedContor[1] > iou:
                                            print(iou, "=========>", expectedContor[1])
                                            iou = expectedContor[1]
                                            # dRow["IOU"] = expectedContor[1]

                                iou_results.append((frame, iou, 'TP'))
                                found = True
                                break
                        if found:
                            break
                    # if found is False:
                    #     print 'not find', frame

            r1 = numpy.mean([e[1] for e in iou_results])
            r2 = numpy.mean([e[1] for e in iou_results if e[2] == 'TP'])
            fout.write("%s,%s,%f,%f\n" % (video_title, video_hash, r1, r2))

            if pidx % 2 == 1:
                pre_iou_results.extend(iou_results)
                r1 = numpy.mean([e[1] for e in pre_iou_results])
                r2 = numpy.mean([e[1] for e in pre_iou_results if e[2] == 'TP'])
                fout.write("%d,%s,%f,%f\n" % ((pidx+1)/2, "", r1, r2))


            pre_iou_results = iou_results

if __name__ == "__main__":  
    IOU()