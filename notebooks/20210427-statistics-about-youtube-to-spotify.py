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
import datetime
from collections import defaultdict

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from bes.channel import SpotifyChannel

# %matplotlib inline

plt.rcParams['figure.dpi'] = 300

font_files = mpl.font_manager.findSystemFonts()
font_files_roboto = [f for f in font_files if 'Roboto' in f]
for font_file in font_files_roboto:
    mpl.font_manager.fontManager.addfont(font_file)

plt.rcParams['font.family'] = 'Roboto'
# -

channel = SpotifyChannel()

for i, playlist in enumerate(channel):
    print(i, playlist.name)

for name, playlist in channel.items():
    print(name, playlist, len(playlist))

for track in channel['microhouse case']:
    print(track.item['album']['release_date'])

track.item['album']

track.item['album'].keys()

df_data = defaultdict(list)
for playlist in channel:
    if 'case' not in playlist.name:
        continue
    for track in playlist:
        df_data['playlist'].append(playlist.name)
        df_data['title'].append(track.title)
        df_data['artists'].append(track.artists)
        df_data['duration'].append(track.item['duration_ms'])
        df_data['popularity'].append(track.item['popularity'])
        df_data['release_date'].append(int(track.item['album']['release_date'][:4]))
df = pd.DataFrame.from_dict(df_data)
# clean up playlist name
df['playlist'] = df['playlist'].str.replace(' case', '')
# drop playlist with too low count
playlists_lengths = df['playlist'].value_counts()
playlists_too_small = playlists_lengths.index[playlists_lengths < 50]
for playlist in playlists_too_small:
    df = df[df['playlist'] != playlist]
# change duration from ms to minutes
df['duration'] = df['duration'] / 1000. / 60.

df['playlist'].value_counts()

palette = sns.color_palette("husl", 8)

# +
fig, ax = plt.subplots(figsize=(8, 8))
sns.set_theme(font='Roboto')

# bar plot
sns.violinplot(y='playlist', x='popularity', data=df, color=palette[0], cut=0, bw=.2)

# Calculate number of obs per group & median to position labels
medians = df.groupby(['playlist'])['popularity'].median()
 
# Add text to the figure
for tick, label in enumerate(ax.get_yticklabels()):
    playlist = label.get_text()
    ax.text(medians[playlist], tick - 0.08, f'{medians[playlist]:1}',
            horizontalalignment='center',
            size='small',
            color='black' if playlist == 'ambient' else 'w',
            weight='semibold',
           )

# title
ax.text(x=0.0, y=1.05, s='Distribution of track popularity', fontsize=18, weight='bold', ha='left', va='bottom', transform=ax.transAxes)
ax.text(x=0.0, y=1.01, s='Ambient on average more popular than any other', fontsize=16, alpha=0.75, ha='left', va='bottom', transform=ax.transAxes)
ax.text(x=0.4, y=-0.12, s='Source: Spotify API | Data viz: @gsautiere', fontsize=14, weight='medium', alpha=1.0, ha='left', va='bottom', transform=ax.transAxes)

# prettify
sns.despine(bottom=True, left=True)  # remove borders of plot
plt.xlabel('')
plt.ylabel('')
plt.yticks(fontsize=14)
plt.xticks(fontsize=14)
plt.legend(fontsize=16)
plt.show()


# +
fig, ax = plt.subplots(figsize=(8, 8))
sns.set_theme(font='Roboto')

# bar plot
sns.violinplot(y='playlist', x='duration', data=df, color=palette[0], cut=0, bw=.2)

# Calculate number of obs per group & median to position labels
medians = df.groupby(['playlist'])['duration'].median()

# Add text to the figure
for tick, label in enumerate(ax.get_yticklabels()):
    playlist = label.get_text()
    ax.text(medians[playlist], tick - 0.08, f'{medians[playlist]:.1f}',
            horizontalalignment='center',
            size='small',
            color='black' if playlist == 'ambient' else 'w',
            weight='semibold',
           )

# title
ax.text(x=0.0, y=1.05, s='Distribution of track duration in minutes', fontsize=18, weight='bold', ha='left', va='bottom', transform=ax.transAxes)
ax.text(x=0.0, y=1.01, s='Wider spread for ambient, similar medians across', fontsize=16, alpha=0.75, ha='left', va='bottom', transform=ax.transAxes)
ax.text(x=0.4, y=-0.16, s='Source: Spotify API | Data viz: @gsautiere', fontsize=14, weight='medium', alpha=1.0, ha='left', va='bottom', transform=ax.transAxes)

# prettify
sns.despine(bottom=True, left=True)  # remove borders of plot
ax.set_xlim(0, 25)
plt.xlabel('duration in minutes')
plt.ylabel('')
plt.yticks(fontsize=14)
plt.xticks(fontsize=14)
plt.legend(fontsize=16)
plt.show()

# -

df_timeline = df.groupby(['release_date', 'playlist']).count()
df_timeline = df_timeline[['title']].rename({'title': 'count'}, axis=1)

# +
playlists = df['playlist'].value_counts().index.tolist()
years = list(range(df['release_date'].min(), df['release_date'].max() + 1))

for year in years:
    if year not in df_timeline.index.get_level_values(0):
        for playlist in playlists:
            df_timeline.loc[(year, playlist), 'count'] = 0
    else:
        for playlist in playlists:
            if playlist not in df_timeline.loc[year].index:
                df_timeline.loc[(year, playlist), 'count'] = 0

# +
df_timeline = df_timeline.sort_index()

df_timeline = df_timeline.swaplevel().sort_index()
# -

len(years)

# +
palette = sns.color_palette("husl", 8)
fig, ax = plt.subplots(figsize=(10, 8))
sns.set_theme(style="whitegrid", font='Roboto')

plots = []
width = 0.5
bottom = np.zeros_like(df_timeline.loc['ambient', 'count'].values)
for i, playlist in enumerate(playlists):
    counts = df_timeline.loc[playlist, 'count'].values
    p = plt.bar(
        years, counts, width,
        bottom=bottom,
        label=playlist,
        log=False,
        color=palette[i],
    )
    bottom += counts

# title
ax.text(x=0.0, y=1.05, s='Timeline of track release year', fontsize=18, weight='bold', ha='left', va='bottom', transform=ax.transAxes)
ax.text(x=0.0, y=1.01, s='Ambient has most consistent presence throughout', fontsize=16, alpha=0.75, ha='left', va='bottom', transform=ax.transAxes)
ax.text(x=0.43, y=-0.12, s='Source: Spotify API | Data viz: @gsautiere', fontsize=14, weight='medium', alpha=1.0, ha='left', va='bottom', transform=ax.transAxes)

# prettify
sns.despine(bottom=True, left=True)  # remove borders of plot
plt.legend(fontsize=16)
plt.show()

# +
# split timeline by each genre
# normalize
