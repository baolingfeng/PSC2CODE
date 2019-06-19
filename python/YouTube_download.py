from pytube import YouTube, Playlist
import re
import os
import string
import urlparse
from dbimpl import DBImpl
from setting import *
# YouTube('http://youtube.com/watch?v=9bZkp7q19f0').streams.first().download()

def insert_video(db, video_hash, video_name, playlist, list_order):
    sql = 'select * from videos where hash = ?'
    res = db.queryone(sql, video_hash)
    print 'db result', res
    if res is not None:
        return
    
    sql = 'insert into videos(hash, title, playlist, list_order) values(?, ?, ?, ?)'
    db.updateone(sql, video_hash, video_name, playlist, list_order)


def parse_video(url):
    yt = YouTube(url)
    streams = yt.streams.filter(progressive=True, file_extension='mp4')
    stream = streams.order_by('resolution').desc().first()

    filename = stream.default_filename
    title = filename[0:-4]

    parsed = urlparse.urlparse(url)
    video_hash = urlparse.parse_qs(parsed.query)['v'][0]

    return video_hash, title

def download_youtube(url, folder="."):
    yt = YouTube(url)
    parsed = urlparse.urlparse(url)
    video_hash = urlparse.parse_qs(parsed.query)['v'][0]

    print "downloading ", video_hash, yt.title
    
    streams = yt.streams.filter(progressive=True, file_extension='mp4')
    stream = streams.order_by('resolution').desc().first()
   
    filename = stream.default_filename
    title = filename[0:-4].decode("ascii", 'ignore')
    video_file = title + "_" + video_hash

    stream.download(output_path=folder, filename=video_file)
    
    if len(yt.captions.all()) > 0:
        caption = yt.captions.all()[0]
        xml_source = caption.xml_captions
        text = caption.xml_caption_to_srt(xml_source.encode("utf-8"))

        with open("%s/%s.srt" % (folder, video_file), "w") as fout:
            fout.write(text)
    
    return title, video_hash


def download_youtube_list(pl_url, folder="."):
    pl = Playlist(pl_url)
    pl.populate_video_urls()
    print "List size is %s:" % len(pl.video_urls)

    videos = []
    for url in pl.video_urls:
        title, video_hash = download_youtube(url, folder=folder)

        videos.append((video_hash, title))

    return videos

def download_from_file(link_file, output_folder):
    with open(link_file) as fin:
        for line in fin.readlines():
            arr = line.strip().split("|")
            url = arr[0]

            print url
            if not os.path.exists(output_folder):
                os.mkdir(output_folder)

            try:
                download_youtube(url, output_folder)
            except Exception as e:
                print "fail to download", url

def download():
    db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})
    sql = 'select id, title from playlists where used = 1'
    sql2 = 'select * from videos where playlist = ?'
    res = db.querymany(sql)

    video_folder = "/Volumes/Seagate/VideoAnalytics/Videos"
    for list_id, title in res:
        res = db.querymany(sql2, list_id)
        if len(res) > 0:
            print 'list has been downloaded', list_id
            continue
        
        print list_id, title
        playlist_url = "https://www.youtube.com/playlist?list=%s" % list_id
        
        output_folder = os.path.join(video_folder, list_id)
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)

        videos = download_youtube_list(playlist_url, output_folder)
        
        for idx, (video_hash, title) in enumerate(videos):
            insert_video(db, video_hash, title, list_id, idx+1)

    db.close()


def get_resolution():
    playlists = []
    with open('playlists.txt') as fin:
        for line in fin.readlines():
            playlists.append(line.strip())

    for idx, list_id in enumerate(playlists):
        playlist_url = "https://www.youtube.com/playlist?list=%s" % list_id

        pl = Playlist(playlist_url)
        pl.populate_video_urls()

        for url in pl.video_urls:
            yt = YouTube(url)
            parsed = urlparse.urlparse(url)
            video_hash = urlparse.parse_qs(parsed.query)['v'][0]

            # print "downloading ", video_hash, yt.title
            
            streams = yt.streams.filter(progressive=True, file_extension='mp4')
            stream = streams.order_by('resolution').desc().first()

            print idx, list_id, stream.resolution
            break


def test():
    url = "https://www.youtube.com/watch?v=7MBgaF8wXls"
    yt = YouTube(url)
    caption = yt.captions.all()[0]
    xml_source = caption.xml_captions
    
    print caption.xml_caption_to_srt(xml_source.encode("utf-8"))


if __name__ == '__main__':
    test()    

