
## The Steps of Our Approach
Due to the limitation on file size, we use an example video: [Java Tutorial For Beginners 26 - Polymorphism in Java](https://www.youtube.com/watch?v=GnLtvmeGAWA) to show how to run our approach <b>psc2code</b>. 

For the whole dataset, please refer to the following link in [Onedrive](https://zjueducn-my.sharepoint.com/:f:/g/personal/lingfengbao_zju_edu_cn/EvDJ4r1hz7FNgmzsAiVsxCIBcg-pYxOwiooKIPya-fssQg?e=DRk35B).


```python
video_hash = 'GnLtvmeGAWA'

video_hash, video_name, video_playlist = get_video_info(video_hash) # get video name, its playlist's hash by video hash
print(video_hash, video_name, video_playlist)

video = video_name + '_' + video_hash # The name of video is in format of its title + hash 
video_mp4_path = os.path.join(video_dir, video_playlist, video+".mp4") # the path of raw video
```

1. <b>Reducing Non-Informative Frames</b> (Related functions are in [preprocess.py](preprocess.py))

```python
extract_frames(video_mp4_path, os.path.join(images_dir, video))
diff_frames(os.path.join(images_dir, video), thre=0.05, metric="NRMSE")
```

This step uses [ffmpeg](https://ffmpeg.org/) to extract frames then removes non-informative frames based on the dissimilarity.

The outputs are stored in the folder [Images](../Images).

2. <b>Removing Non-Code and Noisy-Code Frames</b> (Related source code and files are in [video_tagging](video_tagging))

```python
predict_video(os.path.join(images_dir, video), model_file="video_tagging/weights.h5")
```

Due to the limited file size of GitHub, we upload our trained model `weights.h5` into [Dropbox](https://www.dropbox.com/s/6d6mpybwxtk8rek/weights-new.h5?dl=0)

This step uses a trained model to identify the valid and invalid frames; the results are stored into a file named ["predict.txt"](../Images/Java%20Tutorial%20For%20Beginners%2026%20-%20Polymorphism%20in%20Java_GnLtvmeGAWA/predict.txt)

3. <b>Distinguishing Code versus Non-Code Regions</b> (Related functions are in [video.py](video.py))

```python
cvideo = CVideo(video)
# detect boundingx boxes and store the information of lines and rects into folder 'Lines'
cvideo.cluster_lines()
cvideo.adjust_lines()
cvideo.detect_rects()
# crop the bounding boxes of frames into folder 'Crops'
cvideo.crop_rects()
```

The information abount detected bounding boxes are stored into the folder [Lines](../Lines/Java%20Tutorial%20For%20Beginners%2026%20-%20Polymorphism%20in%20Java_GnLtvmeGAWA), and the cropped frames are in the folder [Crops](../Crops/Java%20Tutorial%20For%20Beginners%2026%20-%20Polymorphism%20in%20Java_GnLtvmeGAWA)

4. <b>Correcting Errors in OCRed Source Code</b> (Related source code and files are in [OCR](OCR))

- Get OCRed source code from cropped frames.
```python
google_ocr(video_name, video_hash)
```

- Correct errors in the OCRed source code
```python
srt_file = os.path.join(video_dir, video_playlist, video+".srt") # caption file if exist
parser = GoogleOCRParser(video, srt_file)
parser.correct_words()
```

The results are stored in the folder [GoogleOCR](../GoogleOCR).
