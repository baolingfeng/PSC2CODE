import os, sys
import json
import shutil
import lxml.etree as etree
import cv2
sys.path.append('../')
from setting import *

def create_annotation_xml(frame_name, frame_path, frame_category, frame_size, rects, out_xml):
    root = etree.Element('annotation')
    folder = etree.Element('folder')
    folder.text = "images"
    root.append(folder)

    filename = etree.Element('filename')
    filename.text = frame_name
    root.append(filename)

    path = etree.Element('path')
    path.text = frame_path
    root.append(path)

    size = etree.Element('size')
    width = etree.Element('width')
    height = etree.Element('height')
    depth = etree.Element('depth')
    width.text = str(frame_size[0])
    height.text = str(frame_size[1])
    depth.text = str(frame_size[2])
    size.append(width)
    size.append(height)
    size.append(depth)
    root.append(size)

    segmented = etree.Element('segmented')
    segmented.text = '0'
    root.append(segmented)

    # if frame_category == 'NoCode':
    #     rects = [[0,0,0,0]]

    for r in rects:
        object_ = etree.Element('object')
        cname = etree.Element('name')
        pose = etree.Element('pose')
        truncated = etree.Element('truncated')
        difficult = etree.Element('difficult')
        cname.text = frame_category
        pose.text = 'Unspecified'
        truncated.text = '0'
        difficult.text = '0'
        object_.append(cname)
        object_.append(pose)
        object_.append(truncated)
        object_.append(difficult)

        bndbox = etree.Element('bndbox')
        xmin = etree.Element('xmin')
        ymin = etree.Element('ymin')
        xmax = etree.Element('xmax')
        ymax = etree.Element('ymax')
        xmin.text = str(r[0])
        ymin.text = str(r[1])
        xmax.text = str(r[2])
        ymax.text = str(r[3])
        bndbox.append(xmin)
        bndbox.append(ymin)
        bndbox.append(xmax)
        bndbox.append(ymax)
        object_.append(bndbox)

        root.append(object_)
    
    with open(out_xml, "w") as fout:
        fout.write(etree.tostring(root, pretty_print=True))



label_dir = "../../webapp/labels"

for vidx, video in enumerate(os.listdir(label_dir)):
    if not video.endswith('.json'):
        continue


    video_folder = video[:-5]
    try:
        video_name, video_hash = video_folder.strip().split('_')
    except Exception as e:
        video_hash = video_folder[-11:]
        video_name = video_folder[0:-12]
        # print video_name, ' //// ', video_hash
        # break
    
    print video_name, ' / ', video_hash
    # continue
        
    video_labels_json = os.path.join(label_dir, video)
    with open(video_labels_json) as fin:
        res = json.load(fin)

        # video_hash = res['video_hash']
        # video_name = res['video_name']
        # video_folder = video_name+"_"+video_hash
        
        video_label_map = res['labels']
        code_frames = []
        nocode_frames = []
        for frame in video_label_map:
            # img_path = os.path.join(images_dir, video_folder, '%s.png' % frame)

            if video_label_map[frame] == '1' or video_label_map[frame] == '2':
                code_frames.append(frame)
            else:
                nocode_frames.append(frame)


    linejson = os.path.join(lines_dir, video_folder, 'lines.json')
    with open(linejson) as fin:
        res = json.load(fin)
        linemap = res['linemap']

        size_read = False
        for cid in linemap:
            cluster = linemap[cid]
            frames = cluster['frames']

            if 'rects' not in cluster:
                continue

            for frame in frames:
                img_path = os.path.join(images_dir, video_folder, '%s.png' % frame)
                # print img_path
                if not size_read:
                    img = cv2.imread(img_path)
                    height, width, depth = img.shape
                    size_read = True

                rects = cluster['rects']

                # frame_name = '%s-%s.png' % (video_hash, frame)
                frame_name = '%s_%s.png' % (vidx, frame)
                # frame_path = os.path.join("images/Code", frame_name)
                frame_path = os.path.join("images", frame_name)
                shutil.copy(img_path, frame_path)

                create_annotation_xml(frame_name, frame_path, 'Code', (width, height, depth), rects, os.path.join("annotations", '%s_%s.xml' % (vidx, frame)))

        for frame in nocode_frames:
            img_path = os.path.join(images_dir, video_folder, '%s.png' % frame)

            rects = [[0, 0, 0, 0]]

            frame_name = '%s_%s.png' % (vidx, frame)
            # frame_path = os.path.join("images/NoCode", frame_name)
            frame_path = os.path.join("images", frame_name)
            shutil.copy(img_path, frame_path)

            create_annotation_xml(frame_name, frame_path, 'NoCode', (width, height, depth), rects, os.path.join("annotations", '%s_%s.xml' % (vidx, frame)))
