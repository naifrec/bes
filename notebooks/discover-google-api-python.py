# -*- coding: utf-8 -*-
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
import re

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import spotipy
from spotipy.oauth2 import SpotifyOAuth


SPOTIFY_USER_ID = os.getenv('SPOTIFY_USER_ID')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

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
client_secrets_file = f'../{os.getenv("YOUTUBE_CLIENT_SECRETS_FILE")}'
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

# ## 2. List content of playlist

# +
nextPageToken = None
tracks = []

while True:
    request = youtube.playlistItems().list(
        part=["contentDetails", "snippet"],
        playlistId="PLBLV0mgoy14qXCOOQh6DSSvhLHcvHU_oX",
        maxResults=50,
        pageToken=nextPageToken,
    )
    response = request.execute()

    # expand track list
    for item in response['items']:
        if 'videoOwnerChannelTitle' in item['snippet']:
            channel = item['snippet']['videoOwnerChannelTitle']
        else:
            # if channel does not exist, usually means the video has
            # been deleted!
            print(f'Could not find channel name for track {item["snippet"]["title"]}.')
            continue

        tracks.append(dict(
            id=item['contentDetails']['videoId'],
            name=item['snippet']['title'],
            position=item['snippet']['position'],
            channel=channel,
        ))

    if 'nextPageToken' in response:
        nextPageToken = response['nextPageToken']
    else:
        break
# -

len(tracks)

response

tracks

# ## 3. Clean up track titles

for i, track in enumerate(tracks[:50]):
    print(i, track['name'])

# List of things to remove:
#
# * remove the tracklist: "A.", "A1.", etc
# * remove the label / release, usually anything between brackets "[...]"
# * remove prefix like "PREMIERE:"

string = 'B. Tripmastaz - Grime-o-Litious [TMZ12006]'
result = re.search(r'([ABCD]{1}[1234]{0,1}\.\s)', string, re.IGNORECASE)
tracklisting = result.groups()[0]
string.replace(tracklisting, '')

result = re.search(r'(\[.*\])', string)
label_or_catalog_number = result.groups()[0]
string.replace(label_or_catalog_number, '')

string = 'premiere Ike - Seven & Seventeen'
result = re.search(r'(premiere\:?\s)', string, re.IGNORECASE)
prefix = result.groups()[0]
string.replace(prefix, '')


# +
def clean_tracklist(string):
    # looks for strings like "A1.", "A2."
    result = re.search(r'^([ABCD]{1}[1234]{0,1}\.\s?).*$', string, re.IGNORECASE)
    if result is not None:
        tracklisting = result.groups()[0]
        string = string.replace(tracklisting, '')
    return string


def clean_label_or_catalog_number(string):
    # looks for strings like [TMZ12006], [Kalahari Oyster Cult]
    string = string.replace('【', '[')
    string = string.replace('】', ']')
    result = re.search(r'(\[.*\])', string)
    if result is not None:
        label_or_catalog_number = result.groups()[0]
        string = string.replace(label_or_catalog_number, '')
    return string


def clean_premiere_prefix(string):
    # looks for strings like "PREMIERE:", "premiere "
    result = re.search(r'(premiere\:?\s)', string, re.IGNORECASE)
    if result is not None:
        prefix = result.groups()[0]
        string = string.replace(prefix, '')
    return string


def clean_parentheses(string):
    # look for strings like (1XA), (unreleased), (Visionquest 2016)
    pass

def clean(string):
    for function in [clean_tracklist, clean_label_or_catalog_number, clean_premiere_prefix]:
        string = function(string)
    return string.strip()


# -

for i, track in enumerate(tracks[:]):
    print(i, clean(track['name']))


# ## 4. Split artist name from track name

# +
def split_artists_from_title(track):
    # ordered from most to least likely / dangerous
    separators = [' ~ ', ' - ', ' – ', ' -- ', '–', '--', '~', '-', '  ', ' ']
    # check if YouTube music automatically generated track
    topic_string = ' - Topic'
    if topic_string in track['channel']:
        artists = track['channel'].replace(topic_string, '')
        title = track['name']
    # regular YouTube channel, all info is in track name
    else:
        # clean track name
        track_name = clean(track['name'])
        # look for separator between artist and track name
        for separator in separators:
            if separator in track_name:
                break
        # if no separator found, need further processing
        if separator not in track_name:
            print(f'warning: could not find a separator in: {track_name}')
            return
        splits = track_name.split(separator)
        # if more thant two splits, probably EP or other info in there, need further processing
        if len(splits) != 2:
            print(f'warning: found more splits than two in: {track_name}')
            return
        artists, title = splits
    return artists, title


def split_artists(artists):
    # ordered from most to least likely / dangerous
    separators = [' & ', ' x ', ]
    # look for separator between artist and track name
    for separator in separators:
        if separator in artists:
            break
    # if no separator found, assume single artist
    if separator not in artists:
        artists = [artists.strip()]
    else:
        artists = [artist.strip() for artist in artists.split(separator)]
    return artists


# -

for i, track in enumerate(tracks):
    if 'artist' in track:
        del track['artist']
    splits = split_artists_from_title(track)
    if splits is None:
        print(f'{i}')
        continue
    else:
        artists, title = splits
        track['artists'] = split_artists(artists)
        track['title'] = title.strip()
        track['search string'] = ' '.join(track['artists']) + ' ' + track['title']
        print(f'{i:03}: artists="{" & ".join(track["artists"]):30}" title="{track["title"]:30}"')

# we should remove what's in brackets if the content within the brackets does not contain:
# * mix
# * remix
# * edit
# * rework
# * reshape
# * dub
# * version

tracks

# ## 5. Search for track on spotify

# +
# important links for documentation
# https://developer.spotify.com/documentation/general/guides/scopes/#playlist-modify-public
# https://spotipy.readthedocs.io/en/2.17.1/#module-spotipy.client

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri="http://localhost:8000",
        scope="playlist-modify-public",
    )
)
# -

track = tracks[0]  # opal sunn laika, exists on spotify
track

result = sp.search(track['search string'])

matches = result['tracks']['items']  # this is the list of tracks
matches[0].keys()

match = matches[0]
match_name = match['name']
match_artists = [artist['name'] for artist in match['artists']]
print(f'First match is {" & ".join(match_artists)} - {match_name}')


# ## 6. Compute risk score

def get_risk_score(track, match):
    score = 0

    # do the artists match?
    expected_artists = set([artist.casefold() for artist in track['artists']])
    matched_artists = set([artist['name'].casefold() for artist in match['artists']])
    # union should be the same as intersection
    missing_artists = expected_artists - matched_artists
    if len(missing_artists) and len(expected_artists) > 1:
        # check if name is not stored as single artist like Oden & Fatzo
        expected_artist = ' & '.join(track['artists']).casefold().strip()
        matched_artist = match['artists'][0]['name'].casefold().strip()
        if expected_artist != matched_artist:
            score += len(missing_artists) / len(expected_artists)
        else:
            missing_artists = set()
    else:
        score += len(missing_artists) / len(expected_artists)

    # does the track name match?
    expected_name = track['title'].casefold().strip()
    matched_name = match['name'].casefold().strip()
    i = 0
    if expected_name != matched_name:
        indices = [i for i in range(min(len(expected_name), len(matched_name))) if matched_name[i] != expected_name[i]]
        index = len(expected_name) if not len(indices) else indices[0]
        score += (index + 1) / len(expected_name)

    return score, missing_artists, matched_name[len(expected_name) - i:]


track

match['name']

get_risk_score(track, match)

# ## 7. Try it for bad matches

for i, track in enumerate(tracks):
    if 'artists' not in track:
        print(f'Skipping track {i} because not parsed: {track["name"]}')
        continue
    print(f'Searching track {i + 1:03}: {" & ".join(track["artists"])} - {track["title"]}')
    result = sp.search(track['search string'])
    matches = result['tracks']['items']
    if len(matches):
        print(f'  there are {len(matches)} matches')
        for k, match in enumerate(matches):
            match_name = match['name']
            match_artists = [artist['name'] for artist in match['artists']]
            risk, missing_artists, mismatch = get_risk_score(track, match)
            print(f'    - match {k}: risk {risk} - missing artists {" & ".join(missing_artists)} - mismatch in name: {mismatch}')

tracks[54]

result['tracks']['items'][0]['artists']

result = sp.search(tracks[8]['search string'])

result 


