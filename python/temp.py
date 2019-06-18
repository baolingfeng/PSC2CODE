import os, sys
from setting import *
from dbimpl import DBImpl


db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})

sql = 'select b.id, b.title from videos a, playlists b where a.playlist = b.id and a.hash = ?'

labels_dir = '../webapp/labels'

playlists = set()
playlist_video = {}

verified_videos = []
with open('verified_videos.txt') as fin:
    for line in fin.readlines():
        verified_videos.append(line.strip())

for f in os.listdir(labels_dir):
    if not f.endswith('.json'):
        continue
    
    f = f[:-5]
    video_hash = f[-11:]

    if video_hash in verified_videos:
        continue

    # print video_hash

    res = db.queryone(sql, video_hash)
    if res is None:
        continue
    
    playlist_id, playlist_title = res

    playlists.add(playlist_title)
    if playlist_title not in playlist_video:
            playlist_video[playlist_title] = []
    playlist_video[playlist_title].append(f)


for f in playlist_video:
    print f
    print playlist_video[f]
    print '--------\n'


sql = 'select id, title from playlists where used = 1'
res = db.querymany(sql)

all_playlists = set()
for pid, title in res:
    all_playlists.add(title)

for p in all_playlists - playlists:
    print p