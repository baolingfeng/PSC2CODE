from flask import Flask, request, jsonify, render_template, make_response, redirect, url_for
from flask import g
from flask_wtf.csrf import CSRFProtect
# from flask.ext.images import Images
import random
import sys
import os
import json
import cv2
import shutil
sys.path.append('../python')
from setting import *
from video import CVideo
from dbimpl import DBImpl
from MySQLDB import MySQLDB
from youtube_download import download_youtube, parse_video
import preprocess
from video_tagging.predict import predict_video, load_model
from adjust_ocr import GoogleOCRParser, generate_doc

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

app = Flask(__name__, static_folder=ASSETS_DIR)
app.config['TEMPLATES_AUTO_RELOAD'] = True
csrf = CSRFProtect(app)

app.secret_key = os.urandom(24)

valid_model = None

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = DBImpl(
            {'url': os.path.join(playlists_dir, 'videos.db')})
    return db


def insert_video(video_hash, video_name, playlist, list_order):
    db = get_db()

    sql = 'select * from videos where hash = ?'
    res = db.queryone(sql, video_hash)
    print 'db result', res
    if res is not None:
        return

    sql = 'insert into videos(hash, title, playlist, list_order) values(?, ?, ?, ?)'
    db.updateone(sql, video_hash, video_name, playlist, list_order)


def get_video_playlist(video_hash):
    db = get_db()
    sql = 'select playlist from videos where hash = ?'
    res = db.queryone(sql, video_hash)
    if res is not None:
        return res[0]
    else:
        return None


def get_playlist():
    db = get_db()
    sql = 'select distinct(a.playlist), b.title from videos a left join playlists b on a.playlist = b.id where b.used=1'
    res = db.querymany(sql)

    return [(r[0], r[1]) for r in res]


def get_videos_of_playlist(playlist):
    db = get_db()
    if playlist is not None:
        sql = 'select hash, title from videos where playlist = ? and used = 1 order by list_order'
        res = db.querymany(sql, playlist)
    else:
        sql = 'select hash, title from videos where playlist is null'
        res = db.querymany(sql)

    return res


def get_video(video_hash):
    db = get_db()
    sql = 'select hash, title from videos where hash = ?'
    return db.queryone(sql, video_hash)


@app.route('/')
def home():
    if 'group' in request.args:
        group = request.args['group']
    else:
        group = 1

    if 'youtube' in request.args:
        use_youtube = request.args['youtube']
    else:
        use_youtube = 1
    
    return render_template('index.html', group=group, use_youtube=use_youtube)


@csrf.exempt
@app.route('/pullvideo', methods=['POST'])
def pull_video():
    youtube_url = request.json['url']
    print 'downloading', youtube_url

    video_hash, video_name = parse_video(youtube_url)

    video_file = video_name + "_" + video_hash + ".mp4"
    playlist = get_video_playlist(video_hash)
    if not os.path.exists(os.path.join(video_dir, video_file)) or not os.path.exists(os.path.join(video_dir, playlist, video_file)):
        download_youtube(youtube_url, folder=video_dir)

    insert_video(video_hash, video_name, None, None)

    return jsonify({'msg': 'success', 'video_hash': video_hash, 'video_name': video_name})


@csrf.exempt
@app.route('/diffvideo', methods=['POST'])
def diff_video():
    video_hash = request.json['video_hash']
    video_name = request.json['video_name']
    print 'diff video', video_name, video_hash

    video_file = video_name + '_' + video_hash

    video_path = os.path.join(video_dir, video_file+'.mp4')
    image_path = os.path.join(images_dir, video_file)
    if not os.path.exists(image_path):
        os.mkdir(image_path)

        preprocess.extract_frames(video_path, image_path)
        preprocess.diff_frames(image_path)

    return jsonify({'msg': 'success', 'video_hash': video_hash, 'video_name': video_name})


@csrf.exempt
@app.route('/predictvideo', methods=['POST'])
def predictvideo():
    video_hash = request.json['video_hash']
    video_name = request.json['video_name']
    print 'validate frames in video', video_name, video_hash

    video_file = video_name + '_' + video_hash

    global valid_model
    if valid_model is None:
        print 'loading model from', model_file
        valid_model = load_model(model_file)

    if not os.path.exists(os.path.join(images_dir, video_file, 'predict.txt')):
        predict_video(video_file, valid_model)

    return jsonify({'msg': 'success'})


@csrf.exempt
@app.route('/cropvideo', methods=['POST'])
def crop_video():
    args = request.json

    video_hash = args['video_hash']
    video_name = args['video_name']
    print 'crop frames in video', video_name, video_hash

    config = {}
    config['eps1'] = int(args['eps1']) if 'eps1' in args else 3
    config['eps2'] = int(args['eps2']) if 'eps2' in args else 1
    config['min_samples'] = int(
        args['min_samples']) if 'min_samples' in args else 2
    config['line_ratio'] = float(
        args['line_ratio']) if 'line_ratio' in args else 0.7

    v = video_name + '_' + video_hash
    if os.path.exists(os.path.join(lines_dir, v)):
        shutil.rmtree(os.path.join(lines_dir, v))
    os.mkdir(os.path.join(lines_dir, v))

    print 'using config', config
    cvideo = CVideo(v, config=config)
    cvideo.cluster_lines()
    cvideo.adjust_lines()
    cvideo.detect_rects()

    return jsonify({'msg': 'success'})


@csrf.exempt
@app.route('/labelvideo', methods=['POST'])
def label_video2():
    video_name = request.json['video_name']
    video_hash = request.json['video_hash']
    labels = request.json['labels']

    with open("labels/%s_%s.json" % (video_name, video_hash), "w") as fout:
        json.dump(request.json, fout, indent=4)

    return jsonify({'msg': 'success'})

@csrf.exempt
@app.route('/fpframe', methods=['POST'])
def fpframe():
    video_name = request.json['video_name']
    video_hash = request.json['video_hash']
    frame = request.json['frame']
    video_file = video_name + '_' + video_hash

    with open(os.path.join(images_dir, video_file, 'predict.json')) as fin:
        predict = json.load(fin)
        predict[str(frame)]['label'] = 'invalid'
    
    with open(os.path.join(images_dir, video_file, 'predict.json'), 'w') as fout:
        json.dump(predict, fout, indent=4)

    return jsonify({'msg': 'success'})

@csrf.exempt
@app.route('/fnframe', methods=['POST'])
def fnframe():
    video_name = request.json['video_name']
    video_hash = request.json['video_hash']
    frame = request.json['frame']
    video_file = video_name + '_' + video_hash

    with open(os.path.join(images_dir, video_file, 'predict.json')) as fin:
        predict = json.load(fin)
        predict[str(frame)]['label'] = 'valid'
    
    with open(os.path.join(images_dir, video_file, 'predict.json'), 'w') as fout:
        json.dump(predict, fout, indent=4)

    return jsonify({'msg': 'success'})

@app.route('/video')
def play_video():
    video_hash = request.args['v']
    video = get_video(video_hash)

    video_info = {}
    video_info['video_hash'] = video_hash

    if video is None:
        video_info['has_processed'] = False
    else:
        video_info['video_name'] = video[1].strip()

        video_folder = video_info['video_name'] + '_' + video_hash
        frame_folder = os.path.join(images_dir, video_folder)
        print frame_folder
        video_info['has_processed'] = True if os.path.exists(
            frame_folder) else False

        ocr_result = os.path.join(
            ocr_dir, video_folder, "parse", "result.json")
        if os.path.exists(ocr_result):
            with open(ocr_result) as fin:
                video_info["ocr"] = json.load(fin)

    return render_template('video.html', video_info=video_info)


@app.route('/enhanced')
def enhanced_video():
    video_hash = request.args['v']
    use_youtube = request.args['youtube']
    group = request.args['group']
    
    video = get_video(video_hash)

    video_info = {}
    video_info['video_hash'] = video_hash
    video_info['group'] = int(group)
    video_info['use_youtube'] = int(use_youtube)

    if video is None:
        video_info['has_processed'] = False
    else:
        video_info['video_name'] = video[1].strip()

        video_folder = video_info['video_name'] + '_' + video_hash
        frame_folder = os.path.join(images_dir, video_folder)
        print frame_folder
        video_info['has_processed'] = True if os.path.exists(
            frame_folder) else False

        ocr_result = os.path.join(
            ocr_dir, video_folder, "parse", "result.json")
        if os.path.exists(ocr_result):
            with open(ocr_result) as fin:
                video_info["ocr"] = json.load(fin)

    return render_template('enhanced.html', video_info=video_info)

@app.route('/videos')
def list_playlists():
    playlists = get_playlist()
    print 'list all playlists', playlists

    res = []
    for playlist_id, playlist_title in playlists:
        playlist_videos = get_videos_of_playlist(playlist_id)

        res.append({'videos': playlist_videos,
                    'playlist_id': playlist_id, 'playlist_title': playlist_title})

    return render_template('videos.html', playlists=res)


@app.route('/video/label')
def label_video():
    video_hash = request.args['v']
    video = get_video(video_hash)
    if video_hash is None or video is None:
        return "Video is missing"

    video_name = video[1].strip()
    frame_folder = os.path.join(images_dir, video_name+"_"+video_hash)

    video_info = {}
    video_info['video_hash'] = video_hash
    video_info['video_name'] = video_name
    with open(os.path.join(frame_folder, "frames.txt")) as fin:
        lines = fin.readlines()
        video_info['frames'] = [int(frame) for frame in lines[0].split()]

    return render_template('label.html', video_info=video_info)


@app.route('/video/predict')
def view_predicted_frames():
    video_hash = request.args['v']
    video = get_video(video_hash)
    if video_hash is None or video is None:
        return "Video is missing"

    video_name = video[1].strip()

    frame_folder = os.path.join(images_dir, video_name+"_"+video_hash)
    video_info = {}
    video_info['video_hash'] = video_hash
    video_info['video_name'] = video_name
    with open(os.path.join(frame_folder, 'predict.txt')) as fin:
        lines = fin.readlines()

        video_info['valid'] = [int(f) for f in lines[1].strip().split(
            ",")] if lines[1].strip() != "" else []
        video_info['invalid'] = [int(f) for f in lines[3].strip().split(
            ",")] if lines[3].strip() != "" else []
    
    if os.path.exists(os.path.join(frame_folder, 'predict.json')):
        with open(os.path.join(frame_folder, 'predict.json')) as fin:
            video_info['predict'] = json.load(fin)
    else:
        predict = {}
        for f in video_info['valid']:
            predict[str(f)] = {'label': 'valid', 'predict': 'valid'}

        for f in video_info['invalid']:
            predict[str(f)] = {'label': 'invalid', 'predict': 'invalid'} 
        
        with open(os.path.join(frame_folder, 'predict.json'), 'w') as fout:
            json.dump(predict, fout, indent=4)

        video_info['predict'] = predict

    return render_template('predict.html', video_info=video_info)


@csrf.exempt
@app.route('/video/crop', methods=["GET", "POST"])
def view_crop(video=None):
    video_hash = request.args['v']
    video = get_video(video_hash)
    if video_hash is None or video is None:
        return "Video is missing"

    video_name = video[1].strip()
    video_folder = video_name+"_"+video_hash
    print 'crop video', video_name

    linejson = os.path.join(lines_dir, video_folder, 'lines.json')
    if not os.path.exists(linejson):
        return "Video isn't cropped"

    with open(linejson) as fin:
        res = json.load(fin)
        linemap = res['linemap']
        config = res['config']

        # cvideo = CVideo(video, config=config)

    res = []
    total = 0
    to_be_cropped = False
    for cid in linemap:
        cluster = linemap[cid]
        frames = cluster['frames']
        total += len(frames)

        if 'to_be_cropped' in cluster:
            to_be_cropped = True

        rects = cluster['rects'] if 'rects' in cluster else []
        cropped = cluster['to_be_cropped'] if 'to_be_cropped' in cluster else False

        res.append([cid, frames, rects, cropped])

    res = sorted(res, key=lambda x: len(x[1]), reverse=True)
    if not to_be_cropped and len(res) > 0:
        res[0][3] = True

    video_info = {}
    video_info['video_name'] = video_name
    video_info['video_hash'] = video_hash
    video_info['clustered'] = total
    video_info['clusters'] = res
    video_info['config'] = config

    return render_template('crops.html', video_info=video_info)


@csrf.exempt
@app.route('/video/ocr', methods=["GET", 'POST'])
def view_ocr():
    video_hash = request.args['v']
    video = get_video(video_hash)
    if video_hash is None or video is None:
        return "Video is missing"

    video_name = video[1].strip()
    ocr_folder = os.path.join(ocr_dir, video_name+"_"+video_hash)

    parser = GoogleOCRParser(video_name, ocr_folder)

    video_info = {}
    video_info['video_hash'] = video_hash
    video_info['video_name'] = video_name
    video_info['frames'] = []
    for doc in parser.docs:
        frame = doc['frame']
        content = generate_doc(doc['lines'])

        video_info['frames'].append([frame, content])

    return render_template('ocr.html', video_info=video_info)


@app.route('/videos/images/<name>')
def list_images(name=None):
    if name is None:
        return "Video is missing"

    frame_folder = image_folder + '/' + name
    with open(os.path.join(frame_folder, 'frames.txt')) as fin:
        lines = fin.readlines()

        filter_frames = [int(f) for f in lines[0].strip().split(" ")]

    return render_template('images.html', name=name, frames=filter_frames)


@app.route('/videos2')
def list_images2():

    return render_template('videos2.html')


@app.route("/videos/<video>/<frame>")
def images(video, frame):
    # generate_img(path)
    fullpath = os.path.join(images_dir, video, '%s.png' % frame)
    # print fullpath
    img = cv2.imread(fullpath)

    if 'rects' in request.args:
        rects = request.args['rects'].split(',')
        k = len(rects) / 4
        for i in range(k):
            x1 = int(rects[4*i])
            y1 = int(rects[4*i + 1])
            x2 = int(rects[4*i + 2])
            y2 = int(rects[4*i + 3])

            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 3)

    height, width = img.shape[:2]

    img = cv2.resize(img, (600, 400))

    retval, buffer = cv2.imencode('.png', img)
    resp = make_response(buffer.tobytes())
    resp.content_type = "image/png"
    return resp


@app.route("/videos2/<video>/<frame>")
def images2(video, frame):
    fullpath = image_folder + '/' + video + '/' + frame + '.png'
    # print fullpath
    img = cv2.imread(fullpath)
    height, width = img.shape[:2]

    img = cv2.resize(img, (600, 400))

    retval, buffer = cv2.imencode('.png', img)
    resp = make_response(buffer.tobytes())
    resp.content_type = "image/png"
    return resp


@csrf.exempt
@app.route("/submit", methods=["POST"])
def submit():
    # print 'submit', request.json
    video = request.json['video']
    labels = request.json['labels']

    with open("labels/%s.json" % video, "w") as fout:
        json.dump(request.json, fout, indent=4)

    return "success"


@csrf.exempt
@app.route("/setcrop", methods=["POST"])
def set_crop():
    print request.json

    video_name = request.json['video_name']
    video_hash = request.json['video_hash']
    video_folder = video_name + '_' + video_hash
    linejson = os.path.join(lines_dir, video_folder, 'lines.json')
    with open(linejson) as fin:
        data = json.load(fin)

    for cid in data['linemap']:
        data['linemap'][cid]['to_be_cropped'] = request.json['cid_'+cid]

    with open(linejson, 'w') as fout:
        json.dump(data, fout, indent=4)

    return jsonify({'msg': 'success'})


@csrf.exempt
@app.route("/rmframe", methods=["GET", "POST"])
def remove_frame():
    print request.json

    video_name = request.json['video_name']
    video_hash = request.json['video_hash']
    video_folder = video_name + '_' + video_hash
    cid = request.json['cid']
    frame = int(request.json['frame'])

    linejson = os.path.join(lines_dir, video_folder, 'lines.json')
    with open(linejson) as fin:
        data = json.load(fin)

    data['linemap'][str(cid)]['frames'].remove(frame)

    with open(linejson, 'w') as fout:
        json.dump(data, fout, indent=4)

    return jsonify({'msg': 'success'})


@csrf.exempt
@app.route("/updaterects", methods=["GET", "POST"])
def update_rects():
    print request.json

    video_name = request.json['video_name']
    video_hash = request.json['video_hash']
    video_folder = video_name + '_' + video_hash
    cid = request.json['cid']
    rects = request.json['rects']

    linejson = os.path.join(lines_dir, video_folder, 'lines.json')
    with open(linejson) as fin:
        data = json.load(fin)

    data['linemap'][str(cid)]['rects'] = rects

    with open(linejson, 'w') as fout:
        json.dump(data, fout, indent=4)

    return jsonify({'msg': 'success'})


@app.route("/search", methods=["GET", "POST"])
def go_search():
    return render_template('search.html')


@app.route("/query", methods=["GET", "POST"])
def search():
    return render_template('search.html')


@app.route("/survey", methods=["GET", "POST"])
def survey():
    video_hash = request.args['v']
    video = get_video(video_hash)

    group = request.args['group']
    use_youtube = request.args['youtube']

    if video_hash is None or video is None:
        return "Video is missing"

    video_name = video[1].strip()

    return render_template('survey.html', video_hash=video_hash, video_name=video_name, group=group, use_youtube=use_youtube)

@csrf.exempt
@app.route("/survey/submit", methods=["GET", "POST"])
def submit_survey():
    print request.json
    video_hash = request.json['video']
    group = int(request.json['group'])
    start_time = request.json['starttime']
    end_time = request.json['endtime']
    question_number = request.json['qnumber']

    mydb = MySQLDB(config={'type': 'mysql', 'url': '127.0.0.1',
                           'username': 'root', 'password': '123456',
                           'database': 'questionnario'})
    sql = 'insert into records(host, starttime, endtime, video, egroup) values(%s, %s, %s, %s, %s)'

    last_id = mydb.insertone_with_increment(sql, request.remote_addr, start_time, end_time, video_hash, group)
    print 'inserted record id', last_id

    sql2 = 'insert into answers(record_id, question, answer, times) values(%s, %s, %s, %s)'
    answers = []
    for i in range(1, question_number+1):
        q = request.json['q%d'%i]
        qtime = request.json['q%d_time'%i]

        answers.append([last_id, 'q%d'%i, q, qtime])

    mydb.updatemany(sql2, answers)

    mydb.close()

    return jsonify({'record_id': last_id})
    
# @csrf.exempt
@app.route("/survey/done", methods=["GET", "POST"])
def done_survey():
    record_id = request.args['id']
    group = int(request.args['group'])

    return render_template('rate.html', record_id=record_id, group=group)

@csrf.exempt
@app.route("/survey/rate", methods=["GET", "POST"])
def rate_survey():
    record_id = request.json['record_id']
    rate = request.json['rate']
    comment = request.json['comment']
    
    mydb = MySQLDB(config={'type': 'mysql', 'url': '127.0.0.1',
                           'username': 'root', 'password': '123456',
                           'database': 'questionnario'})
    
    sql = 'insert into answers(record_id, question, answer) values(%s, %s, %s)'
    mydb.updateone(sql, record_id, 'rate', rate)

    mydb.updateone(sql, record_id, 'comment', comment)

    mydb.close()

    return jsonify({'msg': "success"})


@csrf.exempt
@app.route("/baseline", methods=["GET", "POST"])
def baseline():
    video_hash = request.args['v']
    video = get_video(video_hash)
    if video_hash is None or video is None:
        return "Video is missing"

    video_name = video[1].strip()
    video_folder = video_name+"_"+video_hash
    
    with open(os.path.join(working_dir, 'python', 'baseline_scripts', 'predict_results_detail.json')) as fin:
        res = json.load(fin)
        predict = res[video_folder]

    code_frames = []
    nocode_frames = []
    for frame in predict:
        code_index = -1
        conf = 0
        for idx, r in enumerate(predict[frame]):
            if r['label'] == 'Code' and r['confidence'] > conf:
                code_index = idx
                conf = r['confidence']
        
        if code_index >= 0:
            rect = predict[frame][code_index]
            x1, y1, x2, y2 = rect['topleft']['x'], rect['topleft']['y'], rect['bottomright']['x'], rect['bottomright']['y']
            code_frames.append((frame, (x1, y1, x2, y2)))
        else:
            nocode_frames.append(frame)

    code_frames = sorted(code_frames, key=lambda x: len(x[0]))
    nocode_frames = sorted(nocode_frames)
    print 'code', len(code_frames)
    print 'nocode', len(nocode_frames)

    video_info = {}
    video_info['video_name'] = video_name
    video_info['video_hash'] = video_hash
    video_info['code_frames'] = code_frames
    video_info['nocode_frames'] = nocode_frames

    return render_template('baseline.html', video_info=video_info)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


if __name__ == "__main__":
    # connect to ip adress
    app.run(host='0.0.0.0')
