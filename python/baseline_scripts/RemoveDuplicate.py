import numpy as np
import cv2
import time
import os
import os.path
import multiprocessing as mp


rec=0
def autoIncrement():
 global rec
 pStart = 1 #adjust start value, if req'd
 pInterval = 1 #adjust interval value, if req'd
 if (rec == 0):
  rec = pStart
 else:
  rec = rec + pInterval
 return str(rec).zfill(3)




def saveBothImagas(img1,img2,name1,name2):
    cv2.imwrite("img%s.png" % name1, img1)
    cv2.imwrite("img%s.png" % name2, img2)
    print("WRITE:",name1," and ", name2)

def compareFirstTwo(img1,img2,sift):
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)
    # BFMatcher with default params
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1,des2, k=2)

    # Apply ratio test
    good = []
    time_start = time.time()
    for m,n in matches:
        if m.distance < 0.75*n.distance:
            good.append([m])
    #print(len(good))
    return len(good)

def createNewDir(dirName):
    dir=os.path.join(dirName, "Deleted_Dup")

    if not os.path.exists(dir):
        os.makedirs(dir)
    os.chdir(dir)
    [os.remove(file) for file in os.listdir(dir) if file.endswith('.png')]

def Remove_Duplicate(dirName):


    global rec
    rec = 0
    root=os.getcwd()
    #dir=os.path.join(".\Videos\split", dirName)
    dir=os.path.join(r'C:\Users\Mohammad\PycharmProjects\pythonfinalproject\Videos\split', dirName)
    createNewDir(dir)
    currentDir=os.listdir(dir)
    s=len([name for name in currentDir if name.endswith(".png")])
    AllNumbers = []
    for i in range(s):
        AllNumbers.append(autoIncrement())

    # Initiate SIFT detector
    sift = cv2.xfeatures2d.SIFT_create()

    #FirstImage=dir+"\img001.png"
    FirstImage=dir+"/img001.png"
    # find the keypoints and descriptors with SIFT
    img1 = cv2.imread(FirstImage)
    kp1, des1 = sift.detectAndCompute(img1,None)
    v=2
    time_overall_start = time.time()
    i=1

    tmpSimilarity=0
    #img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)


    cv2.imwrite("img%s.png" % "001",img1)#write the first image to the file
    first=True
    currentImageID = AllNumbers[0]
    while i < s:
        try:
            if os.path.getsize(r"../img{}.png".format(AllNumbers[i]))<50000:  # Skip black images
                print("img%s.png skipped" % AllNumbers[i])
                i+=1
                continue

            if (first):
                #img2 = cv2.imread(r"..\img{}.png".format(AllNumbers[i]))
                img2 = cv2.imread(r"../img{}.png".format(AllNumbers[i]))
                #img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
                tmpSimilarity = compareFirstTwo(img1, img2,sift)
                print("Image :", currentImageID, " and Image ", AllNumbers[i], "= ", tmpSimilarity)
                if (tmpSimilarity == 0):
                    saveBothImagas(img1, img2, AllNumbers[i - 1], AllNumbers[i])
                    i += 1
                    #img1 = cv2.imread(r"..\img{}.png".format(AllNumbers[i]))
                    img1 = cv2.imread(r"../img{}.png".format(AllNumbers[i]))
                    currentImageID = AllNumbers[i]
                    i += 1
                    first = True
                else:
                    i += 1
                    first = False
                continue
            #img2 = cv2.imread(r"..\img{}.png".format(AllNumbers[i]))
            img2 = cv2.imread(r"../img{}.png".format(AllNumbers[i]))

            #img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            v += 1
            kp2, des2 = sift.detectAndCompute(img2, None)

            # BFMatcher with default params
            bf = cv2.BFMatcher()
            matches = bf.knnMatch(des1, des2, k=2)

            # Apply ratio test
            good = []
            time_start = time.time()
            for m, n in matches:
                if m.distance < 0.75 * n.distance:
                    good.append([m])
            # print(len(good))
            print("Image :", currentImageID, " and Image ", AllNumbers[i], "= ", len(good))
            # print("compare", tmpSimilarity, "with ",len(good))
            if (len(good) > 1000):
                if (tmpSimilarity - 15 <= len(good) <= tmpSimilarity + 15):  # we can add threshold, i.e < .9
                    # we have exactly the same image
                    i += 1  # move to the third image
                    continue
                else:
                    if not os.path.exists("img%s.png" % AllNumbers[i]):
                        cv2.imwrite("img%s.png" % AllNumbers[i], img2)

                    img1 = img2
                    currentImageID = AllNumbers[i]
                    print("WRITE:", currentImageID, "(%s)" % dirName)
                    kp1, des1 = sift.detectAndCompute(img2,
                                                      None)  # start next time and compare this image to the following image
                    i += 1
                    first = True
                    continue

            else:
                if (tmpSimilarity * .95 <= len(good) <= tmpSimilarity * 1.05):  # we can add threshold, i.e < .9
                    # we have exactly the same image
                    i += 1  # move to the third image
                    continue
                else:
                    if not os.path.exists("img%s.png" % AllNumbers[i]):
                        cv2.imwrite("img%s.png" % AllNumbers[i], img2)

                    img1 = img2
                    print("WRITE:", currentImageID, "(%s)" % dirName)
                    currentImageID = AllNumbers[i]
                    if not os.path.exists("img%s.png" % currentImageID):
                        cv2.imwrite("img%s.png" % currentImageID, img2)
                        print("WRITE:", currentImageID, "(%s)" % dirName)
                    kp1, des1 = sift.detectAndCompute(img2,
                                                      None)  # start next time and compare this image to the following image
                    i += 1
                    first = True
                    continue

            tmpSimilarity = len(good)
            print("--- %s seconds ---" % (time.time() - time_start))
            # cv2.drawMatchesKnn expects list of lists as matches.
            # img3 = cv2.drawMatchesKnn(img1,kp1,img2,kp2,matches,None,flags=2)
            # plt.imshow(img3)
            # plt.show()
            # print(len(good))
        except Exception as Ex:
            print(Ex, r"../img{}.png".format(AllNumbers[i]))

        print("--- %s seconds ---" % (time.time() - time_overall_start))


    # img2 = cv2.imread(r"..\img{}.png".format(AllNumbers[i-1]))

    # cv2.imwrite("img%s.png" % AllNumbers[i - 1], img2)  # wrtie last one
    print(dir,"has finished!")
    print(AllNumbers[i - 1],"last file!")
    os.chdir(root)

def process_video_wrapped(dir):
    Remove_Duplicate(dir)

def main():
    dir = r'C:\Users\Mohammad\PycharmProjects\pythonfinalproject\Videos\split'

    start = time.time()
    AllDirs=[name for name in os.listdir(dir) if os.path.isdir(os.path.join(dir, name))]
    try:
        for i in range(150,151):
            Remove_Duplicate(str(i))

        # pool = mp.Pool(processes=4)
        # pool.map(process_video_wrapped, AllDirs)
    except Exception as e:
        print("Error with multiprocessing.")
        print(e)
    #print("Processing done. Time elapsed: {} seconds.".format((time.time() - start)))


if __name__ == '__main__':
    main()