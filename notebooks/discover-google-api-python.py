# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.10.3
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# +
import math
import os
import json

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

# +
# https://console.developers.google.com/projectselector2/apis/dashboard?supportedpurview=project
# follow tutorial at https://developers.google.com/youtube/v3/quickstart/python
# warning, also need to follow https://stackoverflow.com/a/65756560/5317241 to add yourself as a tester of the app
# what was done: creating app and credentials

# relevant thread which states i may be locked out of google api by qualcomm
# https://stackoverflow.com/questions/52204803/python-requests-to-google-com-throwing-sslerror
# -

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

# +
# Disable OAuthlib's HTTPS verification when running locally.
# *DO NOT* leave this option enabled in production.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

api_service_name = "youtube"
api_version = "v3"
client_secrets_file = f'./{os.getenv("YOUTUBE_CLIENT_SECRETS_FILE")}'
# -

client_secrets_file

with open(client_secrets_file, 'r') as handle:
    client_secrets = json.load(handle)

# Get credentials and create an API client
flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
    client_secrets_file, scopes)

credentials = flow.run_console()

youtube = googleapiclient.discovery.build(
    api_service_name, api_version, credentials=credentials)

# ## 1. List all playlists of my channel

# +
nextPageToken = None
playlists = []

while True:
    request = youtube.playlists().list(
        part="snippet,contentDetails",
        maxResults=25,
        mine=True,
        pageToken=nextPageToken,
    )
    response = request.execute()
    
    # expand playlist list
    for item in response['items']:
        playlists.append(dict(
            id=item['id'],
            name=item['snippet']['localized']['title'],
            size=item['contentDetails']['itemCount'],
        ))

    if 'nextPageToken' in response:
        nextPageToken = response['nextPageToken']
    else:
        break
# -

playlists

len(playlists)


