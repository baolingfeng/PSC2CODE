import os
import json
import google.oauth2.credentials

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret.
CLIENT_SECRETS_FILE = "client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

def remove_empty_kwargs(**kwargs):
    good_kwargs = {}
    if kwargs is not None:
        for key, value in kwargs.items():
            if value:
                good_kwargs[key] = value
    return good_kwargs


def get_authenticated_service():
  flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
  credentials = flow.run_console()
  return build(API_SERVICE_NAME, API_VERSION, credentials = credentials)

def channels_list_by_username(service, **kwargs):
  results = service.channels().list(
    **kwargs
  ).execute()
  
  print('This channel\'s ID is %s. Its title is %s, and it has %s views.' %
       (results['items'][0]['id'],
        results['items'][0]['snippet']['title'],
        results['items'][0]['statistics']['viewCount']))

def search_list_by_keyword(client, **kwargs):
    # See full sample for function
    kwargs = remove_empty_kwargs(**kwargs)

    response = client.search().list(
        **kwargs
    ).execute()
    
    with open("youtube_search_list.json", "w") as fout:
        json.dump(response, fout, indent=4)

    return response

def parser_response():
    from dbimpl import DBImpl
    from setting import *
    db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})

    sql = "insert into playlists(id, title, channel) values(?, ?, ?)"

    with open("youtube_search_list.json") as fin:
        result = json.load(fin)
    
        for item in result['items']:
            playlist_title = item['snippet']['title']
            channel = item['snippet']['channelId']
            playlist_id = item['id']['playlistId']

            print playlist_id, playlist_title, channel
            db.updateone(sql, playlist_id, playlist_title, channel)

if __name__ == '__main__':
    # search video lists in YouTube then store them into a local database
    parser_response()

