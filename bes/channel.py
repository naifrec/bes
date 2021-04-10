from bes import api
from bes.playlist import SpotifyPlaylist, SpotifySavedTracks, YouTubePlayList
from bes.track import SpotifyTrack


class Channel(object):
    """
    Abstract Channel class defining the API of object wrapping the concept of a
    "Channel" i.e. a YouTube Channel or a Spotify account. A channel has
    playlists associated to it, and allows creation of new playlists.

    """
    backend = None
    _playlists = None

    def __init__(self,):
        self._playlists = None

    @property
    def playlists(self):
        """
        Property which contains the list of all playlists existing for this
        channel. It is a "lazy" attribute, until you access if for the first
        time, the query to retrieve the playlists will not be performed.

        """
        if self._playlists is None:
            self._playlists = self._get_playlists()
        return self._playlists

    def add_playlist(self, name):
        """Add a playlist by name. Backend specific."""
        raise NotImplementedError

    def _get_playlists(self):
        """Backend specific way of retrieving existing playlists"""
        raise NotImplementedError

    def refresh(self):
        """
        After adding a playlist or in general modifying playlists, one could
        opt to refresh the instance to avoid having unsynced information stored
        about the playlists.

        """
        self._playlists = None

    def get(self, playlist_name_or_id):
        """
        Get existing playlist, either by ID or by name. If the playlist does
        not already exist, it will create it.

        """
        if not playlist_name_or_id in self:
            self.add_playlist(playlist_name_or_id)
            self.refresh()
            print(f'{playlist_name_or_id} did not exist on {self.backend}, created one')
        playlists = [pl for pl in self if pl.name == playlist_name_or_id]
        playlists += [pl for pl in self if pl.id == playlist_name_or_id]
        assert len(playlists) == 1, \
            f'more than one hit for playlist {playlist_name_or_id} on {self.backend}: {playlists}'
        return playlists[0]

    def __contains__(self, other):
        """Check if a provided playlist is already in channel."""
        return any(playlist == other for playlist in self)

    def __iter__(self):
        """
        One can iterate over the playlist of the channels in a for loop.

        Example
        -------
        channel = YouTubeChannel()
        for playlist in channel:
            print(playlist.name)

        """
        yield from self.playlists


class YouTubeChannel(Channel):
    """
    YouTube channel. Can only wrap your YouTube channel (mine=True).

    Parameters
    ----------
    readonly : bool, default=True
        Readonly. Use readonly=False carefully; most of the time it's safer
        to use readonly when you know you only want to transfer from youtube
        to spotify and only require read operations. Note that read operations
        on Google API use less points than write operations.

    """
    backend = 'youtube'

    def __init__(self, readonly=True):
        super().__init__()
        self.api = api.get_or_create_youtube_api(readonly=readonly)

    def _get_playlists(self):
        """
        YouTube specific way of retrieving all playlists of a channel.

        Returns
        -------
        playlists : list of bes.playlist.YouTubePlayList
            List of playlists.

        """
        nextPageToken = None
        playlists = []

        while True:
            request = self.api.playlists().list(
                part="snippet,contentDetails",
                maxResults=25,
                mine=True,
                pageToken=nextPageToken,
            )
            response = request.execute()

            # expand playlist list
            for item in response['items']:
                playlists.append(YouTubePlayList.from_item(item))

            if 'nextPageToken' in response:
                nextPageToken = response['nextPageToken']
            else:
                break

        return playlists

    def add_playlist(self, name):
        """
        YouTube specific way of adding / creating new playlist (by name).

        Parameters
        ----------
        name : str
            Name of playlist to add.

        Returns
        -------
        playlist : bes.playlist.YouTubePlayList
            YouTube playlist instance for created playlist.

        """
        assert name not in self, f'Playlist {name} already exists'
        request = self.api.playlists().insert(
            part="snippet,status",
            body={
            "snippet": {
                "title": name,
            },
            "status": {
                "privacyStatus": "public"
            }
            }
        )
        response = request.execute()
        return YouTubePlayList.from_item(response)


class SpotifyChannel(Channel):
    """
    Spotify channel / account. Can only wrap your Spotify channel. Contrary to
    YouTube you do not get to pick if readonly or not, be careful as you are
    always able to write. Note though that I did not implement any deletion
    operation in this API, to avoid any irrevesible mistake (deleting a playlist
    you've been building for 10 years... can you imagine the heart sink?).

    """
    backend = 'spotify'

    def __init__(self):
        super().__init__()
        self.api = api.get_or_create_spotify_api()

    def _get_playlists(self):
        """
        Spotipy specific way of retrieving all playlists of a channel.

        Returns
        -------
        playlists : list of bes.playlist.SpotifyPlayList
            List of playlists.

        """
        playlists = []
        for item in self.api.user_playlists(api.SPOTIFY_USER_ID)['items']:
            playlists.append(SpotifyPlaylist.from_item(item))
        return playlists

    def add_playlist(self, name):
        """
        Spotipy specific way of adding / creating new playlist (by name).

        Parameters
        ----------
        name : str
            Name of playlist to add.

        Returns
        -------
        playlist : bes.playlist.SpotifyPlayList
            Spotify playlist instance for created playlist.

        """
        response = self.api.user_playlist_create(
            user=api.SPOTIFY_USER_ID,
            name=name,
            public=True,
        )
        return SpotifyPlaylist.from_item(response)

    def get_saved_tracks_playlist(self):
        """
        Get user saved (a.k.a liked) tracks. This method is specific to Spotify
        as there is no such concept as "saved tracks" on YouTube. The closest
        would be your "likes", but YouTube handles it like any other playlist.
        For some reason in Spotify your liked / saved tracks are not a playlist
        but a different object altogether.

        Returns
        -------
        playlist : bes.playlist.SpotifySavedTracks
            Spotify saved / liked tracks playlist. Note that calling this a
            "playlist" instance is abusing terminology. This playlist does not
            have an ID since it is not an actual playlist according to Spotify
            backend.

        """
        return SpotifySavedTracks()
