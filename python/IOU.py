import os, sys
import json
from video import CVideo
from dbimpl import DBImpl
from setting import *
import numpy


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


db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})

with open("verified_videos.txt") as fin, open("iou_results.csv", "w") as fout:
    sql = 'select hash, title from videos where hash = ?'

    pre_iou_results = []
    for idx, line in enumerate(fin.readlines()):
        video_hash = line.strip()
        video_hash, video_title = db.queryone(sql, video_hash)

        video = video_title.strip() + '_' + video_hash.strip()
        print video

        iou_results = []
        with open(os.path.join(images_dir, video, 'predict.json')) as fin2:
            predict_results = json.load(fin2)

            for frame in predict_results:
                if predict_results[frame]['label'] == 'valid' and predict_results[frame]['predict'] == 'invalid':
                    iou_results.append((frame, 0, 'FN'))
                elif predict_results[frame]['label'] == 'invalid' and predict_results[frame]['predict'] == 'invalid':
                    iou_results.append((frame, 1, 'TN'))
                elif predict_results[frame]['label'] == 'invalid' and predict_results[frame]['predict'] == 'valid':
                    iou_results.append((frame, 0, 'FP'))
                else:
                    with open(os.path.join(working_dir, "Lines", video, "lines.json")) as fin3:
                        lines_info = json.load(fin3)

                        rect = None
                        for c in lines_info['linemap']:
                            cluster = lines_info['linemap'][c]
                            rect = [int(e) for e in cluster['rects'][0]] if 'rects' in cluster and len(cluster['rects']) > 0 else None
                            to_be_cropped = cluster['to_be_cropped'] if 'to_be_cropped' in cluster else False
                            found = False
                            for frame2 in cluster['frames']:
                                if frame == str(frame2):
                                    found = True
                                    break
                            if found:
                                break
                    
                    with open(os.path.join(working_dir, "Lines2", video, "lines.json")) as fin2:
                        lines_info = json.load(fin2)

                        rect2 = None
                        for c in lines_info['linemap']:
                            cluster = lines_info['linemap'][c]
                            rect2 = [int(e) for e in cluster['rects'][0]] if 'rects' in cluster and len(cluster['rects']) > 0 else None
                            found = False
                            for frame2 in cluster['frames']:
                                if frame == str(frame2):
                                    found = True
                                    break
                            if found:
                                break

                    if rect is not None and rect2 is not None:
                        iou = bb_intersection_over_union(rect, rect2)
                        # print rect, rect2, iou
                        iou_results.append((frame, iou, 'TP'))

            r1 = numpy.mean([e[1] for e in iou_results])
            r2 = numpy.mean([e[1] for e in iou_results if e[2] == 'TP'])

            fout.write("%s,%s,%f,%f\n" % (video_title, video_hash, r1, r2))

            if idx % 2 == 1:
                pre_iou_results.extend(iou_results)
                r1 = numpy.mean([e[1] for e in pre_iou_results])
                r2 = numpy.mean([e[1] for e in pre_iou_results if e[2] == 'TP'])

                fout.write("%d,%s,%f,%f\n" % ((idx+1)/2, "", r1, r2))

            pre_iou_results = iou_results
        # break
            

        # # new_lines_dir=os.path.join(working_dir, "Lines2")
        # if not os.path.exists(os.path.join(lines_dir, video)):
        #     os.mkdir(os.path.join(lines_dir, video))

        # cvideo = CVideo(video, config=config)
        # cvideo.cluster_lines()
        # cvideo.adjust_lines()
        # cvideo.detect_rects()