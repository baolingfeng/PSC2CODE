#!/usr/bin/env
# -*- coding: utf8 -*-

# import requests
# import json
# from requests.auth import HTTPBasicAuth
import sqlite3
# import logging


class DBImpl:

    def __init__(self, config):
        self.url = config['url']

        self.conn = self.connection()
        # self.conn.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')

    def connection(self):
        try:
            return sqlite3.connect(self.url)
        except Exception as e:
            print e
            return None

    def close(self):
        self.conn.close()

    def create_table(self, table_name, sql, drop=True):
        # with self.conn:
        cur = self.conn.cursor()

        if drop:
            cur.execute("DROP TABLE IF EXISTS %s" % table_name)

        cur.execute(sql)

        cur.close()
        self.conn.commit()

    def create_table2(self, table_name, columns, drop=True):
        strsql = 'CREATE TABLE %s' % table_name
        strsql += '(' + ','.join([c['name'] + ' ' + c['type']
                                  for c in columns]) + ')'

        self.create_table(table_name, strsql, drop)

    def table_exist(self, table_name):
        # with self.conn:
        cur = self.conn.cursor()

        cur.execute(
            'SELECT name FROM sqlite_master WHERE type=\'table\' AND name = ?', (table_name,))

        data = cur.fetchone()
        cur.close()
        return data is not None
    
    def execute(self, sql):
        cur = self.conn.cursor()

        cur.execute(sql)

        cur.close()

    def queryone(self, sql, *args):
        # with self.conn:
        cur = self.conn.cursor()

        cur.execute(sql, args)

        data = cur.fetchone()

        cur.close()
        # conn.commit()
        return data

    def querymany(self, sql, *args):
        # with self.conn:
        cur = self.conn.cursor()

        cur.execute(sql, args)

        data = cur.fetchall()

        cur.close()
        # conn.commit()
        return data

    def updateone(self, sql, *args):
        # with self.conn:
        cur = self.conn.cursor()
        cur.execute(sql, args)

        cur.close()
        self.conn.commit()

    def updatemany(self, sql, objs):
        # with self.conn:
        cur = self.conn.cursor()
        cur.executemany(sql, objs)

        cur.close()
        self.conn.commit()


def insert_video(video_hash, video_name, playlist, list_order):
    from setting import *

    print os.path.join(playlists_dir, 'videos.db')
    db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})

    sql = 'select * from videos where hash = ?'
    res = db.queryone(sql, video_hash)
    if res is not None:
        return
    
    sql = 'insert into videos(hash, title, playlist, list_order) values(?, ?, ?, ?)'
    db.updateone(sql, video_hash, video_name, playlist, list_order)
    # db.close()

if __name__ == '__main__':
    insert_video('r59xYe3Vyks', 'test', 'test', 'test')
    # print(sqlite3)
    # from setting import *
    # import urlparse

    # db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})
    # sql = 'insert into videos(hash, title, playlist, list_order) values(?, ?, ?, ?)'

    # for playlist in os.listdir(playlists_dir):
    #     if not playlist.endswith(".csv") or not playlist.startswith("videos-"):
    #         continue
        
    #     list_hash = playlist[7:-4]

    #     with open(os.path.join(playlists_dir, playlist)) as fin:
    #         number = 1
    #         for line in fin.readlines():
    #             url_link, video = line.strip().split(",")
                
    #             parsed = urlparse.urlparse(url_link)
    #             video_hash = urlparse.parse_qs(parsed.query)['v'][0]
    #             print video_hash, number

    #             image_path = os.path.join(lines_dir, video.strip())
    #             if not os.path.exists(image_path):
    #                 continue
                
    #             db.updateone(sql, video_hash, video, list_hash, number)

    #             number += 1