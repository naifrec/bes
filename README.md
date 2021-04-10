# bes: from youtube to spotify and back

Python package allowing you to sync your Spotify and YouTube playlists.
The name is a reference to [an ancient Egyptian god](https://ancientegyptonline.co.uk/bes/)
who seem loosely related with music but more importantly has a 3 letters name
which makes those imports super short and neat (slurp slurp).

## 1. Example

Let's say I have a "ambient techno" playlist on YouTube but not on Spotify.
I can run the following command to create the playlist on spotify and populate
it with all tracks for which we can find a match in Spotify:

```python
from bes.channel import SpotifyChannel, YouTubeChannel

playlist_name = 'ambient techno'
youtube_channel = YouTubeChannel()
youtube_playlist = youtube_channel.get(name=playlist_name)

spotify_channel = SpotifyChannel()
spotify_playlist = spotify_channel.add_playlist(playlist_name)

spotify_playlist.add_tracks(youtube_playlist)
```

## 2. Installation instructions

### 2.1 Python dependencies

Assuming you use [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/),
and create a conda environment called `bes`:

```bash
conda create --name bes python=3.6
conda activate bes
conda install -c conda-forge --file requirements.txt
```

### 2.2 Secrets file

You will need to create two apps, one Spotify app and one Google API app, both
will give you access to client ID / secrets allowing you authenticate yourself
and hence allowing you to communicate with the respective APIs.

The `bes` package expects you to define 4 environment variable:
* `SPOTIFY_USER_ID`: Spotify user ID
* `SPOTIFY_CLIENT_ID`: Spotify client ID
* `SPOTIFY_CLIENT_SECRET`: Spotify client secret
* `YOUTUBE_CLIENT_SECRETS_FILE`: path to Google / YouTube API secrets file

We will store these variables in a file at the root of the repository which
we will call `.env`. Before calling any script using `bes` you will need to
make sure these variables are defined, which you will be able to do by calling:

```bash
source .env
python <your-script-using-bes>
```

#### 2.2.1 Spotify secrets

Go to https://developer.spotify.com/dashboard/applications, if you already
have a Spotify account it is free to create a developer application.

To this app will be associated a Client ID and Clien Secret. Copy them inside
your `.env` file, in plain terms add the following lines to file:

```bash
export SPOTIFY_CLIENT_ID=<your-client-id>
export SPOTIFY_CLIENT_SECRET=<your-client-secret>
```

The easiest way to retrieve your SPOTIFY_USER_ID is by opening Spotify, clicking
on your user profile on the top right corner, click on the three dots below
your profile name, select share, select "Copy Profile Link" which will look
like: `https://open.spotify.com/user/6iqjcfrvp6kmgqx0u4ivp9ueg?si=dk0SQCrmQ_ygjrjMv9eD-A`.
Here `6iqjcfrvp6kmgqx0u4ivp9ueg` is my user ID (don't worry it's public information
I am not compromising myself here).

Now that you know how to retrieve your user ID, you can add it to you `.env` file,
i.e. add the following line:

```bash
export SPOTIFY_USER_ID=<your-user-id>
```

That's it, you are ready to interact with Spotify! If you want to see how
exactly these variables are used, read `bes/api.py`, in particular
`get_or_create_spotify_api`.

#### 2.2.2 YouTube / Google API secrets

First of all, buckle up because Spotify is like 100 times easier to setup than
YouTube.

The idea is that the [YouTube API quickstart](https://developers.google.com/youtube/v3/quickstart/python#step_1_set_up_your_project_and_credentials)
is somewhat giving the right directions, but they are not exactly correct.

So let me break it down a bit more for you:
1. Go to [the API console](https://console.developers.google.com/) and create a new app
   with the same account as your YouTube channel account (very important since you will
   only be able to access / edit your own channel).
2. Once created, go to [the credentials tab](https://console.cloud.google.com/apis/credentials)
   and click "create credentials". Choose to create an OAuth Client ID, with
   "Desktop App" as application type. Give it an appropriate name.
3. In the credentials tab you should now see the OAuth Client ID listed in a
   table, to the very right there is a download button which will allow you
   to download the secrets file.
4. Now that you have your secrets file, you can copy it inside the root of
   `bes` project (or anywhere else you see fit) and you can add to your `.env`
   file the `YOUTUBE_CLIENT_SECRETS_FILE` pointing to said file

```bash
export YOUTUBE_CLIENT_SECRETS_FILE=<path/to/secrets.json>
```

You are not done yet! Quite incredibily you need to add yourself as test user
otherwise all your requests will be refused. Follow this [stackover flow answer](https://stackoverflow.com/questions/65756266/error-403-access-denied-the-developer-hasn-t-given-you-access-to-this-app-despi/65756560#65756560)
to add yourself as a test user of your own app.

You should now be ready to roll.
