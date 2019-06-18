#!/usr/bin/env
# -*- coding: utf8 -*-

# import requests
# import json
# from requests.auth import HTTPBasicAuth
import sqlite3
# import logging
import mysql.connector


class MySQLDB:

    def __init__(self, config):
        self.type = config['type'] if 'type' in config else 'sqlite'
        self.url = config['url']
        self.username = config['username'] if 'username' in config else None
        self.password = config['password'] if 'password' in config else None
        self.port = config['port'] if 'port' in config else 3306
        self.database = config['database'] if 'database' in config else None

        self.conn = self.connection()

    def connection(self):
        if self.type == 'sqlite' or self.type is None:
            return sqlite3.connect(self.url)
        elif self.type == 'mysql':
            return mysql.connector.connect(user=self.username, password=self.password,
                                           host=self.url,
                                           port=self.port,
                                           database=self.database)
        else:
            raise Exception('the database is not supported')

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

        if self.type == 'sqlite':
            cur.execute(
                'SELECT name FROM sqlite_master WHERE type=\'table\' AND name = ?', (table_name,))
        elif self.type == 'mysql':
            cur.execute('SHOW TABLES LIKE %s', (table_name,))

        data = cur.fetchone()
        cur.close()
        return data is not None
    
    def execute(self, sql):
        cur = self.conn.cursor()

        cur.execute(sql)

        cur.close()

    def queryone(self, sql, *args):
        # with self.conn:
        cur = self.conn.cursor(buffered=True)

        cur.execute(sql, args)

        data = cur.fetchone()

        cur.close()
        # conn.commit()
        return data

    def querymany(self, sql, *args):
        # with self.conn:
        cur = self.conn.cursor(buffered=True)

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
    
    def insertone_with_increment(self, sql, *args):
        cur = self.conn.cursor()
        cur.execute(sql, args)

        lastid = cur.lastrowid

        cur.close()
        self.conn.commit()

        return lastid

    def updatemany(self, sql, objs):
        # with self.conn:
        cur = self.conn.cursor()
        cur.executemany(sql, objs)

        cur.close()
        self.conn.commit()


if __name__ == '__main__':
    # print(sqlite3)
    db = DBImpl({'type': 'sqlite', 'url': '../jabref.db3'})

    print db.querymany('select * from jabref_commits where committer = ?', 'Tobias')
