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
from collections import Counter

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt


def plot_eigvals(eigvals, out_img="eigenval_plot.png"):
    """
    Plot a given a list of sorted eigen values.
    """
    fig, ax = plt.subplots(nrows=1, ncols=1)


    ax.plot(eigvals, "rv-")
    ax.set_title(f"First {len(eigvals)} eigenvalues")
    ax.set_yticks([1.0], minor=True)
    ax.yaxis.grid(True, which='minor')
    ax.set_xlim(0, 40)
    ax.set_ylim(0, 80000)

    ax.grid(True)

    plt.savefig(out_img)


def combine_images_into_tensor(img_fnames):
    """
    Given a list of image filenames, read the images, flatten them
    and return a tensor such that each row contains one image.

    Size of individual image: 300*300
    """
    # Initialize the tensor
    tensor = np.zeros((len(img_fnames), 416 * 416))


    for i, fname in enumerate(img_fnames):
        img = cv2.imread(fname, cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img, (416, 416), interpolation=cv2.INTER_AREA)
        tensor[i] = img.reshape(416 * 416)

    return tensor

def get_image_fnames(img_dir):
    """
    Return ist of needed images
    """
    fnames = list(glob.glob(f"{img_dir}/*.png"))
    #print(fnames)
    return fnames

def get_pca_reducer(tr_tensor, n_comp=10):
    # Apply PCA on the training images
    pca = PCA(n_components=n_comp)
    pca.fit(tr_tensor)

    return pca


def cluster_images(all_img_fnames, num_clusters=4):
    # Select 100 images at random for PCA
    random.shuffle(all_img_fnames)
    tr_img_fnames = all_img_fnames[:100]

    # Flatten and combine the images
    tr_tensor = combine_images_into_tensor(tr_img_fnames)

    # Perform PCA
    pca = get_pca_reducer(tr_tensor)

    # Reduce dimensions of all
    all_tensor = combine_images_into_tensor(all_img_fnames)
    points = pca.transform(all_tensor)

    # CLuster
    kmeans = KMeans(n_clusters=num_clusters, random_state=0).fit(points)

    cluster_fnames = defaultdict(list)
    for i, label in enumerate(kmeans.labels_):
        cluster_fnames[label].append(all_img_fnames[i])

    for k in cluster_fnames:
        print(k, len(cluster_fnames[k]), cluster_fnames[k][:3])


def test_eigenvals():
    all_img_fnames = get_image_fnames(r"E:\karim\Code")

    # First: random 200 images.
    k = 200
    tr_img_fnames = random.choices(all_img_fnames, k=k)
    tr_tensor = combine_images_into_tensor(tr_img_fnames)
    pca = get_pca_reducer(tr_tensor, 40)
    plot_eigvals(pca.singular_values_, f"eigenval_plot_{k}_rand_images.png")


    # Second: random 1400 images.
    k = 1400
    tr_img_fnames = random.choices(all_img_fnames, k=k)
    tr_tensor = combine_images_into_tensor(tr_img_fnames)
    pca = get_pca_reducer(tr_tensor, 40)
    plot_eigvals(pca.singular_values_, f"eigenval_plot_{k}_rand_images.png")




if __name__ == "__main__":
    #all_img_fnames = get_image_fnames("ide_data")
    #cluster_images(all_img_fnames)
    test_eigenvals()
