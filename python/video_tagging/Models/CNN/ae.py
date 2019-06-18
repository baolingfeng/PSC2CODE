from keras.preprocessing.image import load_img
from keras.callbacks import TensorBoard
import matplotlib.pyplot as plt
import numpy as np
from model import conv_ae,conv_e
import os

TRAIN = False
LOAD_TYPE = 'pre'
batch_size = 32
epochs = 700
PATIENCE = 20
counter = 0

def get_code(x_train,y_train,x_test,y_test):
    X_TRAIN = []
    for i in range(len(x_train)):
        if np.all(y_train[i] == np.array([1,0,0,0])):
            X_TRAIN.append(x_train[i])
        elif np.all(y_train[i] == np.array([0,1,0,0])):
            X_TRAIN.append(x_train[i])

    for i in range(len(x_test)):
        if np.all(y_test[i] == np.array([1,0,0,0])):
            X_TRAIN.append(x_train[i])
        elif np.all(y_test[i] == np.array([0,1,0,0])):
            X_TRAIN.append(x_train[i])

    return np.array(X_TRAIN)

if LOAD_TYPE == 'original':
    images = np.empty((1,300,300,3))
    for subdir,dirs,files in os.walk('../../../Data/'):
        for img in files:
            if img.endswith('_resized.png'):
                img_path = os.path.join(subdir,img)
                image = np.array(load_img(img_path,target_size=(300,300,3))).reshape(1,300,300,3)
                images = np.append(images,image,axis=0)
                counter += 1
            if counter % 5000 == 0:
                print 'Images saved:',counter
    np.savez('all_images',images=images)

elif LOAD_TYPE == 'aug':
    images = np.empty((1,300,300,3))
    data = np.load('../../Fold_0/data.npz')
    x_train,y_train,x_test,y_test = data['x_train'],data['y_train'],data['x_test'],data['y_test']
    images = np.append(images,x_train[1].reshape(1,300,300,3),axis=0)
    for f in os.listdir('../../Pics/'):
        print f
        image = np.array(load_img('../../Pics/'+f,target_size=(300,300,3))).reshape(1,300,300,3)
        images = np.append(images,image,axis=0)
    images = images.astype('uint8')

elif LOAD_TYPE == 'pre':
    data = np.load('../../Fold_0/data.npz')
    x_train,y_train,x_test,y_test = data['x_train'],data['y_train'],data['x_test'],data['y_test']
    images = get_code(x_train,y_train,x_test,y_test)

print 'Data loaded...',images.shape

model = conv_ae((300,300,3))
print 'Model loaded...'
if TRAIN:
    import time
    start = time.time()
    model.fit(images, images,
                epochs=epochs,
                batch_size=batch_size,
                shuffle=True,
                validation_data=(images, images),
                callbacks=[TensorBoard(log_dir='autoencoder')])
    print time.time() - start
    model.save_weights('ae.h5')
else:
    encoder = conv_e((300,300,3))
    model.load_weights('ae.h5')
    for i in range(7):
        params = model.layers[i].get_weights()
        if params != []:
            encoder.layers[i].set_weights([params[0],params[1]])

    encodings = encoder.predict(images)
    print encodings.shape

    def plot(img1,img2):
        f,ax = plt.subplots(1,2)
        ax[0].imshow(img1)
        ax[1].imshow(img2)
        plt.show()

    items = []
    plot(images[1],images[2])
    for i in range(encodings.shape[0]):
        items.append(np.linalg.norm(encodings[1] - encodings[i]))

    print items
