import cv2
import json
import os
import sys
sys.path.append('..')
from setting import * 


class GoogleService(object):
    def __init__(self, service_name, version, access_token):
        self.url = 'https://%s.googleapis.com/%s/images:annotate?key=%s' % (service_name, version, access_token)

    def execute(self, body):
        header = {'Content-Type': 'application/json'}
        response = requests.post(self.url, headers=header, json=body)
        return response.json()

# Pass the image data to an encoding function.
def encode_image(img_path):
    with open(img_path) as image:
        image_content = image.read()
        return base64.b64encode(image_content)

def make_request(img_path):
    body = {
        'requests': [{
            'image': {
                'content': encode_image(img_path),
            },
            'features': [{
                'type': 'DOCUMENT_TEXT_DETECTION',
                        'maxResults': 1,
            }]

        }]
    }
    return body

# Google VISION API token is set as an environment variable VISION_API
access_token = os.environ.get('VISION_API')
service = GoogleService('vision', 'v1', access_token=access_token)


def extract_text(img_path, outfile="res.json"):
    response = service.execute(body=make_request(img_path))

    with open(outfile, "w") as fout:
        json.dump(response, fout, indent=4)


def google_ocr(video_name, video_hash):
    video_folder = video_name + '_' + video_hash

    images_folder = os.path.join(crop_dir, video_folder)
    if not os.path.exists(images_folder):
        return
    
    out_folder = os.path.join(ocr_dir, video_folder)

    if not os.path.exists(out_folder):
        os.mkdir(out_folder)
    
    for img in os.listdir(images_folder):
        if not img.endswith(".png"):
            continue
        
        img_path = os.path.join(images_folder, img)
        filename = os.path.splitext(img)[0] + '.json'
        outfile = os.path.join(out_folder, filename)

        if os.path.exists(outfile):
            continue

        print img_path
        try:
            extract_text(img_path, outfile)
        except Exception as e:
            print e
            print img_path
        
        # break

def main():
    from dbimpl import DBImpl

    db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})
    sql = 'select id, title from playlists where used = 1'
    sql2 = 'select hash, title from videos where playlist = ? and used = 1 order by list_order'
    res = db.querymany(sql)
    for list_id, title in res:
        list_folder = os.path.join(video_dir, list_id)

        print list_id
        videos = db.querymany(sql2, list_id)
        for video_hash, video_title in videos:
            print video_title, video_hash
            google_ocr(video_title, video_hash)


if __name__ == '__main__':
    main()


