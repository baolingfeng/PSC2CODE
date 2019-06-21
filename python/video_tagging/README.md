# Removing Non-Code and Noisy-Code Frames Using Deep Learning
The implementation is based on the source code from [<b>Ott et al.</b>](https://github.com/jordanott/Video-Code-Tagging)



## Prepare Dataset
- We use [the web application](../../webapp) to label frames as valid and invalid. The labels are stored in [../../webapp/labels/](../../webapp/labels/). 
- Then, we use the python script [split_dataset.py](split_dataset.py) to generate training and testing files in format of [train.csv](train.csv) and [test.csv](test.csv).
  
## Train
  * Please use the script [train.py](train.py) to train a model to predict images as valid or invalid

## Prediction
* Use the script [predict.py](predict.py) to predict frames in our dataset
