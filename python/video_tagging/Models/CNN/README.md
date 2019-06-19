# CNN Model
This is the source code from Ott et al., which is implemented in Keras with a Tensorflow backend

## [Models](model.py) ##
* Inception  
* VGG  
* Autoencoder  
* Encoder  

## [CAM](cam.py) ##
Allows you to produce CAM results on the train/test set.

## [Custom CAM](custom_cam.py) ##
Allows you to produce CAM results from a specified directory containing images.  
Specify:
1. Where your images are
2. Output options (e.g. Code/NC)
3. Set weights list for all models you want CAM from
