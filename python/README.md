
Example Video: [Java Tutorial For Beginners 26 - Polymorphism in Java](https://www.youtube.com/watch?v=GnLtvmeGAWA)

```python
video_hash = 'GnLtvmeGAWA'

video_hash, video_name, video_playlist = get_video_info(video_hash) # get video name, its playlist's hash by video hash
print(video_hash, video_name, video_playlist)

video = video_name + '_' + video_hash # The name of video is in format of its title + hash 
video_mp4_path = os.path.join(video_dir, video_playlist, video+".mp4") # the path of raw video
```

1. Reducing Non-Informative Frames (Related functions are in [preprocess.py](preprocess.py))

```python
extract_frames(video_mp4_path, os.path.join(images_dir, video))
diff_frames(os.path.join(images_dir, video), thre=0.05, metric="NRMSE")
```

This step uses [ffmpeg](https://ffmpeg.org/) to extract frames then removes non-informative frames based on the dissimilarity

2. Removing Non-Code and Noisy-Code Frames (Related source code and files are in [video_tagging](video_tagging))

```python
predict_video(os.path.join(images_dir, video), model_file="video_tagging/weights.h5")
```

This step uses a trained model to identify the valid and invalid frames; the results are stored into a file named ["predict.txt"](../Images/Java%20Tutorial%20For%20Beginners%2026%20-%20Polymorphism%20in%20Java_GnLtvmeGAWA/predict.txt)

3. Distinguishing Code versus Non-Code Regions