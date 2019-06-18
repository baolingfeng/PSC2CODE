import os, sys
import json
from dbimpl import DBImpl
from setting import *

db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})

sql = 'select b.id, b.title, count(1) from videos a, playlists b where a.playlist = b.id and a.used=1 and b.used=1 group by b.id'
sql2 = 'select hash, title from videos where playlist = ? and used = 1'


def stat1():
    fout = open("video_stat.csv", "w")

    res = db.querymany(sql)
    for playlist_hash, playlist_title, video_count in res:
        fout.write('%s,%s,%s\n' % (playlist_hash, playlist_title, video_count))
        print playlist_hash, playlist_hash, video_count

        res2 = db.querymany(sql2, playlist_hash)
        stat = []
        for video_hash, video_title in res2:
            video_folder = video_title.strip() + '_' + video_hash

            with open(os.path.join(images_dir, video_folder, 'frames.txt')) as fin:
                frames = [int(f) for f in fin.readlines()[0].split(' ')]
                max_frame = frames[-1]
            
            with open(os.path.join(images_dir, video_folder, 'predict.txt')) as fin:
                lines = fin.readlines()
                valid = lines[1].split(',') if lines[1] != '' else []
                invalid = lines[3].split(',') if lines[3] != '' else []
            
            stat.append((max_frame, len(valid)+len(invalid), len(valid)))

            fout.write('%s,%s,%d,%d,%d\n' % (video_hash, video_title, max_frame, len(valid), len(invalid)))
        
        print sum([s[0] for s in stat])/len(stat), sum([s[1] for s in stat])/len(stat), sum([s[2] for s in stat])/len(stat)

        fout.write('\n\n')

def stat2():
    import numpy as np

    res = db.querymany(sql)
    fout = open('correct_stat.csv', 'w')
    for playlist_hash, playlist_title, video_count in res:
        # fout.write('%s,%s,%s\n' % (playlist_hash, playlist_title, video_count))
        # print playlist_hash, playlist_title, video_count

        res2 = db.querymany(sql2, playlist_hash)
        words = []
        lines = []
        for video_hash, video_title in res2:
            video_folder = video_title.strip() + '_' + video_hash

            with open(os.path.join(ocr_dir, video_folder, 'parse', 'correct.json')) as fin:
                correct = json.load(fin)
                # print len([(w, correct['words']) for w in correct['words']]), len(correct['lines'])
                words.append(len([(w, correct['words']) for w in correct['words']]))
                lines.append(len(correct['lines']))

            # break
        fout.write('%s,%d,%0.2f,%0.2f,%d,%0.2f,%0.2f\n' % (playlist_hash, np.sum(words), np.mean(words), np.std(words), np.sum(lines), np.mean(lines), np.std(lines)))
        print np.sum(words), np.mean(words), np.std(words), np.sum(lines), np.mean(lines), np.std(lines)
        # break  

def stat3():
    Total_TP, Total_FP, Total_TN, Total_FN = 0, 0, 0, 0
    with open("verified_videos.txt") as fin, open("predict_results.csv", "w") as fout:
        sql = 'select hash, title from videos where hash = ?'

        for line in fin.readlines():
            video_hash = line.strip()
            video_hash, video_title = db.queryone(sql, video_hash)

            # print video_title, video_hash

            video = video_title.strip() + '_' + video_hash
            
            # if not os.path.exists(os.path.join(images_dir, video, "predict.json")):
            #     continue

            with open(os.path.join(images_dir, video, "predict2.json")) as fin2:
                predict_info = json.load(fin2)

                TP, FP, TN, FN = 0, 0, 0, 0
                for f in predict_info:
                    if predict_info[f]['label'] == 'valid':
                        if predict_info[f]['label'] == predict_info[f]['predict']:
                            TP += 1
                        else:
                            FN += 1
                    elif predict_info[f]['label'] == 'invalid':
                        if predict_info[f]['label'] == predict_info[f]['predict']:
                            TN += 1
                        else:
                            FP += 1
                print TP, FP, TN, FN 

                Total_TP += TP
                Total_FP += FP
                Total_TN += TN
                Total_FN += FN
                fout.write("%s,%s,%d,%d,%d,%d\n" % (video_title, video_hash, TP, FP, TN, FN))
    
    print Total_TP, Total_FP, Total_TN, Total_FN, (Total_TP + Total_TN)*1.0/(Total_TP+Total_FP+Total_TN+Total_FN)


def main():
    stat3()

if __name__ == '__main__':
    main()