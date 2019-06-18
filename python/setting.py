import os

#This file contains the working directory including the location of videos, images, and other outputs

working_dir = "/home/blf/Data/VideoAnalytics"

code_dir = os.path.join(working_dir, "python")
video_dir = os.path.join(working_dir, "Videos")
images_dir = os.path.join(working_dir, "Images")
predicted_dir = os.path.join(working_dir, "Predicted")
crop_dir = os.path.join(working_dir, "Crops")
ocr_dir = os.path.join(working_dir, "GoogleOCR")
lines_dir = os.path.join(working_dir, "Lines")
audio_dir = os.path.join(working_dir, "Audios")
playlists_dir = os.path.join(working_dir, "Playlists")
model_file = os.path.join(working_dir, 'python', 'video_tagging', 'weights-new.h5')
