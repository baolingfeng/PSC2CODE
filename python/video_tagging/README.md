# Removing Non-Code and Noisy-Code Frames Using Deep Learning
The implementation is based on the source code from [<b>Ott et al.</b>](https://github.com/jordanott/Video-Code-Tagging)

Files:
  * [split_dataset.py](split_dataset.py): generate training and testing files in format of [train.csv](train.csv) and [test.csv](test.csv)
  * [Models](Models/): the deep learning networks implemnted by Ott et al. to label images
  * [train.py](train.py): train a model to predict images as valid or invalid
  * [predict.py](predict.py): predict frames in our dataset
