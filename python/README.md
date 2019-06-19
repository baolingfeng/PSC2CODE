
Example Video: [Java Tutorial For Beginners 26 - Polymorphism in Java](https://www.youtube.com/watch?v=GnLtvmeGAWA)

```python
video_hash = 'GnLtvmeGAWA'

video_hash, video_name, video_playlist = get_video_info(video_hash) # get video name, its playlist's hash by video hash
print(video_hash, video_name, video_playlist)

video = video_name + '_' + video_hash # The name of video is in format of its title + hash 
video_mp4_path = os.path.join(video_dir, video_playlist, video+".mp4") # the path of raw video
```

1. Preprocess video (Related functions are in [preprocess.py](preprocess.py))

```python
extract_frames(video_mp4_path, os.path.join(images_dir, video))
diff_frames(os.path.join(images_dir, video), thre=0.05, metric="NRMSE")
```

This step uses ffmpeg to extract frames then removes 

2. 