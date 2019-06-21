import os
import sys, cv2, math, numpy
import phase1, phase2, time

sys.path.append('../../python')
from dbimpl import DBImpl
from setting import *

big_windows = ''

# video hash
video_hash = 'GnLtvmeGAWA'

db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})
sql = 'select title, playlist from videos where hash = ?'
res = db.queryone(sql, video_hash)
video_name = res[0].strip()
video_playlist = res[1].strip()

video_file = video_name + "_" + video_hash + ".mp4"
video_path = os.path.join(video_dir, video_playlist, video_file)

if(not os.path.exists(video_path)):
    video_file = video_name + ".mp4"
    video_path = os.path.join(video_dir, video_playlist, video_file)


# check videos #5 and 6
# fps_list = [15.002999, 29.970030, 30, 23.976150, 30, 29.970030, 30.001780, 30, 29.970030, 29.970030, 30, 15, 23.976024, 30, 15, 30, 29.873960, 30, 15, 25.000918, 30]

# fps = fps_list[vnum-1]
# video = cv2.VideoCapture('../public/videos/video'+str(vnum)+'.mp4')
video = cv2.VideoCapture(video_path)
fps = video.get(cv2.CAP_PROP_FPS)

print(video_path)
print('fps', fps)

fnum = 0

success, image = video.read()
prev = numpy.zeros(image.shape, numpy.uint8)
time1, time2 = 0, 0
while success:
    fnum += 1
    t_min = int((fnum/fps)/60)
    t_sec = int(math.floor((fnum/fps)%60)) #check

    # if len(sys.argv) > 2 and fnum < int(sys.argv[2]) and fnum%7200 == 0:
    #     print 'crossed frame', fnum # at time

    if round(fnum%fps) == 1: # process one frame each second
        diff = cv2.subtract(image, prev)
        imgray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        ndiff = cv2.countNonZero(imgray)

        # sys.stdout.write("\r100%\033[K")
        # print '\r%d:%02d processing...' % (t_min, t_sec), # (<ndiff> differences)
        # sys.stdout.flush()
        # path = '../public/extracts/video'+str(vnum)
        path = '../public/extracts/%s_%s' % (video_name, video_hash)
        if not os.path.exists(path):
            os.mkdir(path)

        sys.stdout.write("\r100%\033[K")
        print '\r%d:%02d finding segments...' % (t_min, t_sec),
        sys.stdout.flush()
        start1 = time.time()
        segments = phase1.process(image, path, 'frame'+str(fnum)+'-segment', big_windows)
        end1 = time.time()
        time1 += end1 - start1
        # write num_segments somewhere


        # break

        sys.stdout.write("\r100%\033[K")
        print '\r%d:%02d extracting text...' % (t_min, t_sec),
        sys.stdout.flush()
        start2 = time.time()
        phase2.process(fnum, segments, path)
        end2 = time.time()
        time2 += end2 - start2

        if ndiff > 7500: # show significant changes #improve
            marked = image.copy()
            ret, thresh = cv2.threshold(imgray, 60, 255, 0)
            contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(marked, contours, -1, (0,255,0), 1)
            cv2.imwrite(path+'/diffs/'+'frame'+str(fnum)+'.jpg', marked)

        prev = image
        # end of if stmt

    success, image = video.read()

    # end of while loop #todo

print '\ndone'
print '1:', round(time1, 2)
print '2:', round(time2, 2)


