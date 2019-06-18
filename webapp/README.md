# The Web Application
This web application is used to view videos and images in our dataset, label and validate images.

## Run in a local machine 
    > python server.py
    
The default port is 5000, so you can vist homepage: http://127.0.0.1:5000

## URL Mapping:
- View all playlists and videos in the dataset: [/videos]()
- Label the frames in a video (the parameter `v` is equal to the hash in YouTube) [/video/label?v=###########]()
- View the predict results for a video [/video/predict?v=###########]()
- View the bounding boxes of the frames a video [/video/crop?v=###########]()
- View the ORC results for the frames in a video [/video/ocr?v=###########]()

For User Study:
- The start page for user study of enhancing programming video tutorials: [homepage]()
- The enhanced programming video tutorial: [/video?v=###########]()

The Baseline of Alahmadi et al.
- View the predicted results of the baseline: [/baseline?v=###########]()