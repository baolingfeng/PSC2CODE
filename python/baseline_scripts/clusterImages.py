import os
import cv2
import numpy as np
import h5py
import re
from collections import defaultdict
import glob
import random
from sklearn.decomposition import IncrementalPCA, PCA
from sklearn.cluster import KMeans
import glob
import shutil
import ntpath
from collections import Counter
import ntpath


def combine_images_into_tensor(img_fnames, width, height):
    """
    Given a list of image file names, read the images, flatten them
    and return a tensor such that each row contains one image.

    Size of individual image: 300*300
    """
    # Initialize the tensor
    tensor = np.zeros((len(img_fnames), width * height))

    for i, fname in enumerate(img_fnames):
        try:
            img = cv2.imread(fname, cv2.IMREAD_GRAYSCALE)
            img = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
            tensor[i] = img.reshape(width * height)
        except Exception as ex:
            print(fname)

    return tensor


def get_image_fnames(img_dir):
    """
    Return ist of needed images
    """
    fnames = list(glob.glob(f"{img_dir}/*.png"))
    # print(fnames)
    return fnames


def get_pca_reducer(tr_tensor):
    # Apply PCA on the training images
    pca = PCA(n_components=12)
    pca.fit(tr_tensor)

    return pca


def cluster_images(all_img_fnames, num_clusters, width, height):
    # Select 200 images at random for PCA
    random.shuffle(all_img_fnames)
    tr_img_fnames = all_img_fnames[:500]

    # Flatten and combine the images
    tr_tensor = combine_images_into_tensor(tr_img_fnames,width,height)

    # Perform PCA
    pca = get_pca_reducer(tr_tensor)
    print("PCA REDUCER DONE")
    # Reduce dimensions of all
    all_tensor = combine_images_into_tensor(all_img_fnames,width,height)
    points = pca.transform(all_tensor)
    print("TRANSFORM IS DONE")
    # Cluster
    kmeans = KMeans(n_clusters=num_clusters, random_state=0).fit(points)
    print("CLUSTER IS DONE")
    cluster_fnames = defaultdict(list)
    for i, label in enumerate(kmeans.labels_):
        cluster_fnames[label].append(all_img_fnames[i])

    for k in cluster_fnames:
        print(k, len(cluster_fnames[k]), cluster_fnames[k][:3])
        destPath = os.path.join(r"E:\karim\Code\Clusters", str(k))
        if(not os.path.isdir(destPath)):
            os.mkdir(destPath)

        for fname in cluster_fnames[k]:
            destPath = os.path.join(r"E:\karim\Code\Clusters", str(k))
            destPath = os.path.join(destPath, ntpath.basename(fname))
            shutil.copy(fname,destPath)



if __name__ == "__main__":
    all_img_fnames = get_image_fnames(r"E:\karim\Code")
    cluster_images(all_img_fnames, 1000, 400 , 400)