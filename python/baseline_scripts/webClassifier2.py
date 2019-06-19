import pip

installing_err_msg = """'%s' cannot be installed. You need to do one of the following:
- Run the program as a root.
- Run the program in a virtual environment.
    $python3 -m venv tmp
    $tmp/bin/python3
- Run the following command as a root:
    pip install %s"""

try:
    from flask import Flask, render_template, request,make_response,redirect, url_for
except:
    print("'flask' module is not installed. let's install it")
    pip.main(['install', "flask"])
    try:
        from flask import Flask, render_template, request
    except:
        print(installing_err_msg % ('flask','flask'))
        exit()

import json
import sqlite3
import os.path
import glob,re

videos_path = "static/"
deleted_dup_folder = 'Deleted_Dup/'
win_videos_path = "static\\"
win_deleted_dup_folder = 'Deleted_Dup\\'

conn = sqlite3.connect('Classifier.db',check_same_thread=False)
c = conn.cursor()


app = Flask(__name__)


@app.route('/') 
def index():
    username = request.cookies.get('username')
    if username is None:
        return render_template('login.html')
    else:
        # get the last frame
        sql = "select * from classifier where username='%s' or username2='%s' order by id desc limit 0,1" % (username,username)
        c.execute(sql)
        r = c.fetchone()
        frame=0
        video=0
        if r is None:
            video = request.cookies.get('start_video')
            frame = request.cookies.get('start_frame')
            frame = ("0" * (3 - len(str(frame)))) + str(frame)
            video_path = videos_path + str(video) + "/" + deleted_dup_folder
            return render_template('index.html', username=username, video=video, frame=frame,
                                   video_path=video_path)
        else:
            frame = r[1]
            video = r[2]

        next_frame = getNextFrame(frame,video)
        if next_frame[0] == '-1':
            next_video = getNextVideo(frame)
            if next_video[0]=='-1':
                return "This was the last video. Thanks!"
            else:
                return render_template('index.html', username=username, video=next_video[0], frame=next_video[1],
                                       video_path=next_video[2])
        else:
            return render_template('index.html',username=username,video=frame,frame=next_frame[0],video_path=next_frame[2])

@app.route('/login',methods=['POST', 'GET'])
def login():
    username = request.args.get("username")
    sql = "SELECT * FROM users WHERE username = '%s'" % username
    c.execute(sql)
    usr = c.fetchall()
    if len(usr):
        redirect_to_index = redirect('/')
        resp = make_response(redirect_to_index)
        usr = usr[0]

        resp.set_cookie('username', username)
        resp.set_cookie('start_video', str(usr[1]))
        resp.set_cookie('start_frame', str(usr[3]))
        resp.set_cookie('end_video', str(usr[2]))
        resp.set_cookie('end_frame', str(usr[4]))

        return resp
    redirect_to_index = redirect('/')
    resp = make_response(redirect_to_index)
    return resp


@app.route('/logout')
def logout():
    redirect_to_index = redirect('/')
    resp = make_response(redirect_to_index)
    resp.set_cookie('username', '', expires=0)
    return resp


@app.route('/next',methods=['POST', 'GET'])
def next():
    username = request.cookies.get('username')
    if username is None:
        return "You need to login"

    cmd_type=''
    if request.method == 'POST':
        cmd_type = request.form['cmd_type']
    elif request.method == 'GET':
        cmd_type = request.args.get('cmd_type')

    next_frame = getNextFrame(request.args.get('video'), request.args.get('frame'))

    end_video = request.cookies.get('end_video')
    end_frame = request.cookies.get('end_frame')

    if int(next_frame[1]) >= int(end_video) and int(next_frame[0])>int(end_frame):
        d = dict()
        d['video'] = '-1'
        d['frame'] = '-1'
        d['video_path'] = ''
        return json.dumps(d)

    if next_frame[0] == '-1':
        next_video = getNextVideo(request.args.get('video'))
        if next_video[0] == '-1':
            d = dict()
            d['video'] = '-1'
            d['frame'] = '-1'
            d['video_path'] = ''

            sql = "select * from classifier where video=%s and frame=%s and username='%s'" % (request.args.get('video'),request.args.get('frame'),username)
            c.execute(sql)

            if len(c.fetchall()):
                pass
            else:
                sql = "select * from classifier where video=%s and frame=%s" % (request.args.get('video'),request.args.get('frame'))
                c.execute(sql)		
                if len(c.fetchall()):
                    sql = "UPDATE classifier SET class2 = %s,username2='%s' WHERE video=%s and frame=%s;" % (cmd_type,username,request.args.get('video'),request.args.get('frame'))
                else:
                    sql = "INSERT INTO classifier (video, frame,class ,username) VALUES ('%s', '%s', '%s', '%s');" % (
                    request.args.get('video'), request.args.get('frame'), cmd_type, username
                )

            c.execute(sql)
            conn.commit()


            return json.dumps(d)
        else:
            d = dict()
            d['video']  = next_video[0]
            d['frame'] = next_video[1]
            d['video_path'] = next_video[2]

            sql = "INSERT INTO classifier (video, frame,class ,username) VALUES ('%s', '%s', '%s', '%s');" % (
                request.args.get('video'), request.args.get('frame'), cmd_type, username
            )
            c.execute(sql)
            conn.commit()

            return json.dumps(d)
    else:
        d = dict()
        d['video'] = next_frame[1]
        d['frame'] = next_frame[0]
        d['video_path'] = next_frame[2]
		
        sql = "select * from classifier where video=%s and frame=%s and username='%s'" % (request.args.get('video'),request.args.get('frame'),username)
        c.execute(sql)

        if len(c.fetchall()):
            pass
        else:
            sql = "select * from classifier where video=%s and frame=%s" % (request.args.get('video'),request.args.get('frame'))
            c.execute(sql)		
            if len(c.fetchall()):
                sql = "UPDATE classifier SET class2 = %s,username2='%s' WHERE video=%s and frame=%s;" % (cmd_type,username,request.args.get('video'),request.args.get('frame'))
            else:
                sql = "INSERT INTO classifier (video, frame,class ,username) VALUES ('%s', '%s', '%s', '%s');" % (
                request.args.get('video'), request.args.get('frame'), cmd_type, username
                )
        
        c.execute(sql)
        conn.commit()

        return json.dumps(d)

def getNextFrame(video,frame):
    filename = ''
    frame_no = frame
    video_no = video
    img_path = videos_path + str(video) + "/" + deleted_dup_folder
    win_img_path = win_videos_path + str(video) + "\\" + win_deleted_dup_folder
    lstFiles=glob.glob(win_img_path  + "*.png")
    lstFiles.sort()
    curFile =  "img" + ("0" * (3 - len(str(frame_no)))) + str(frame_no) + ".png"
    curFile = win_img_path + curFile
    i = lstFiles.index(curFile)
    if i==len(lstFiles)-1:
        return '-1','-1',""
    else:
        frame_no=re.findall("img([0-9]+)\.png",lstFiles[i+1])[0]
        return (frame_no,video_no,img_path)


def getNextVideo(video):
    video_no = int(video) + 1
    img_path = videos_path + str(video_no) + "/" + deleted_dup_folder
    win_img_path = win_videos_path + str(video_no) + "\\" + win_deleted_dup_folder
    lstFiles=glob.glob(win_img_path  + "*.png")
    if len(lstFiles)==0:
        return '-1','-1'
    lstFiles.sort()
    frame_no = re.findall("img([0-9]+)\.png", lstFiles[0])[0]
    return video_no,frame_no,img_path
