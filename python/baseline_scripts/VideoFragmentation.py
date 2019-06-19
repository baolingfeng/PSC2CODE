import os
import re
import sys
import time
import logging
import subprocess
import multiprocessing as mp
import cv2

# Undesirable video name pattern.
PATTERN = "(\d|\w)+\.(\d|\w)+\.mp4"
rootPath=""
#ffmpeg -i HelloWorldJava1.mp4 -vf fps=1 img%03d.jpg
# Command line for FFMPEG. Extracting full color images (grayscale conversion happens later).
COMMAND = "ffmpeg -i %s.mp4 -vf fps=1 img%03d.png"#might want to include high def. images


def ret_file_names(path):
    res = []
    for filename in os.listdir(path):
        if filename.endswith('.mp4') and not re.search(PATTERN, filename):
            res.append(filename)
    return res


def splitVideo(fullPath):#get the full path to image and write it to the destination
    vidcap = cv2.VideoCapture(fullPath)
    vidcap.set(cv2.CAP_PROP_FPS, 1)
    vidcap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    vidcap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    success, image = vidcap.read()
    count = 1
    success = True


    vidcap.set(cv2.CAP_PROP_FPS,10)
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    print("Frames per second using video.get(cv2.CAP_PROP_FPS) : {0}".format(fps))


    print("Converting video..\n")
    time_start = time.time()
    r=0
    while success:
        success, image = vidcap.read()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        #image = cv2.Canny(image, 10, 30)
        cv2.imwrite("./img%03d.png" % count, image)  # save frame as JPEG file
        count += 1

        if cv2.waitKey(100) & 0xFF == ord('q'):
            break
    time_end = time.time()
    print("It took %d seconds forconversion." % (time_end - time_start))
    vidcap.release()
    cv2.destroyAllWindows()
    cv2.waitKey(1)

def process_video(filename, path):
    rootPath=os.getcwd()
    start = time.time()
    parts = filename.split(".mp4")
    splitdir = path + "/split/" + parts[0] + "_split"
    if not os.path.exists(splitdir):
        os.makedirs(splitdir)

    os.chdir(splitdir)
    split = COMMAND.split()
    split[2] = "../../" + filename
    try:
        # splitVideo(split[2])
        currnt=os.getcwd()
        FNULL = open(os.devnull, 'w')
        splitout = subprocess.call(split, stdout=FNULL, stderr=subprocess.STDOUT)
        subprocess.call(split,stdout=FNULL,stderr=FNULL)
        os.chdir(rootPath)

    except Exception as e:
        print("Error processing video - ", filename)
        print(e)
    finally:
        #FNULL.close()
        end = time.time()


def process_video_wrapped(tup):
    process_video(tup[0], tup[1])


def process_all_videos(path):
    if os.path.exists(path):
        files = ret_file_names(path) #this will return all file names in the specificfied directory
        files = [(f, path) for f in files]  # generate tuples of (filename, path) for multiprocessing.
        try:

            pool = mp.Pool(7)
            pool.map(process_video_wrapped, files)
        except Exception as e:
            print("Error with multiprocessing.")
            print(e)
    else:
        print("Error. Path does not exist. Aborting.")


def main():
    if len(sys.argv) == 2:
        path = sys.argv[1]
    else:
        path = './Videos'
    start = time.time()
    process_all_videos(path)
    print("Processing done. Time elapsed: {} seconds.".format((time.time() - start)))


if __name__ == '__main__':
    main()
