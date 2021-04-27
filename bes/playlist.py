from bes import api
from bes.track import SpotifyTrack, YouTubeTrack


class PlayList(object):
    """
    Abstract PlayList class defining the API of object wrapping the concept of
    a playlist. A playlist has tracks associated to it, and allows adding more
    tracks to it.

    """
    name = None
    id = None
    _tracks = None

    @property
    def tracks(self):
        """
        Property which contains the list of all tracks existing in this
        playlist. It is a "lazy" attribute, until you access it for the first
        time, the query to retrieve the tracks will not be performed.

        """
        if self._tracks is None:
            self._tracks = self._get_tracks()
        return self._tracks

    def add_tracks(self, playlist):
        """Add tracks in provided playlist which are not yet in this playlist."""
        raise NotImplementedError

    def _get_tracks(self):
        """Backend specific way of retrieving tracks in playlist"""
        raise NotImplementedError

    @classmethod
    def from_item(cls, item):
        """Create PlayList object from the REST API JSON."""
        raise NotImplementedError

    def __len__(self):
        """Length of playlists (i.e. how many tracks)"""
        return len(self.tracks)

    def __iter__(self):
        """
        One can iterate over the tracks of the playlist in a for loop.

        Example
        -------
        playlist = YouTubePlayList(id=<some-id>, name=<some-name>)
        for i, track in enumerate(playlist):
            print(i, track.name, track.artists)

        """
        yield from self.tracks

    def __eq__(self, other):
        """
        Checks equality between two playlists. Either same name or same ID.
        Note that I am making the (potentially wrong) assumption that you do
        not have playlist with duplicated names.

        Parameters
        ----------
        other : bes.playlist.PlayList or str
            Other playlist instance.

        Returns
        -------
        are_equal : bool

        """
        if isinstance(other, PlayList):
            return (self.id == other.id) or (self.name == other.name)
        else:
            # assume string
            return (self.name == other) or (self.id == other)

    def __getitem__(self, index):
        """
        Get track by index.

        """
        return self.tracks[index]

    def __str__(self):
        return f'{self.__class__.__name__}(name={self.name}, id={self.id})'


class YouTubePlayList(PlayList):
    """
    YouTube playlist. Note that it is unlikely that you will instantiate
    a YouTube playlist yourself. Use the YouTubeChannel instance to retrieve
    existing playlists.

    Parameters
    ----------
    id : str
        Playlist ID.
    name : str
        Playlist name.

    """
    def __init__(self, id, name):
        self.api = api.get_or_create_youtube_api()
        self.id = id
        self.name = name
        self._tracks = None

    def _get_tracks(self):
        """
        YouTube specific way of retrieving all tracks of a playlist.

        Returns
        -------
        tracks : list of bes.track.YouTubeTrack
            List of tracks.

        """
        nextPageToken = None
        tracks = []

        while True:
            request = self.api.playlistItems().list(
                part=["contentDetails", "snippet"],
                playlistId=self.id,
                maxResults=50,
                pageToken=nextPageToken,
            )
            response = request.execute()

            # expand track list
            for item in response['items']:
                try:
                    track = YouTubeTrack.from_item(item)
                    tracks.append(track)
                except ValueError as e:
                    print(f'Could not add track because of original error {e}.')
                    continue

            if 'nextPageToken' in response:
                nextPageToken = response['nextPageToken']
            else:
                break
        return tracks

    def add_tracks(self, playlist):
        """
        Add tracks from other playlist, specifically:
        1. will cast input playlist to YouTube (call .to_youtube) to retrieve
           only the tracks for which there are matches on YouTube.
        2. will compare the IDs of matched tracks with existing IDs in the
           playlist.
        3. will remove tracks for which already exist in the playlist
        4. will add remaining tracks to the playlist.

        Notes
        -----
        YouTube API has [a quota](https://developers.google.com/youtube/v3/getting-started#calculating-quota-usage)
        on the number of operation per day. Adding a track costs 50 points, one
        search is 100 points. By default, you have 20,000 points to
        spend per day. Quick math: that means you can only add 130 tracks per
        day. In practice even less as retrieving the tracks from the playlist
        already cost you points (although only 10 points per 25 tracks).

        Parameters
        ----------
        playlist : bes.playlist.PlayList
            Other playlist to add tracks from.

        """
        ids_existing = [track.id for track in self]
        ids_spotify = [track.id for track in playlist.to_youtube()]

        ids_to_add = list(set(ids_spotify) - set(ids_existing))
        print(f'There are:\n\t- {len(ids_spotify)} tracks matched from Spotify'
              f'\n\t- {len(ids_existing)} tracks existing in Youtube playlist'
              f'\n\t- {len(ids_to_add)} new tracks to add'
             )

        for video_id in ids_to_add:
            request = self.api.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": self.id,
                        "position": 0,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id,
                            }
                        }
            })
            request.execute()
        # TODO: add the tracks to _tracks?
        print(f'{len(ids_to_add)} tracks added to youtube playlist {self.name}!')

    @classmethod
    def from_item(cls, item):
        """Create YouTube Playlist from the REST API JSON"""
        return cls(
            id=item['id'],
            name=item['snippet']['localized']['title'],
        )

    def to_youtube(self):
        """Cast tracks to YouTube format (no-op)"""
        return self

    def to_spotify(self):
        """
        Cast tracks of playlist to Spotify. For each track, it will look for
        matches on Spotify, score them, and return the track scoring the lowest
        risk (under a certain threshold). If no such track exist; the track
        is simply skipped and assumed not to exist on Spotify.

        Returns
        -------
        matched_tracks : list of bes.track.SpotifyTrack
            Spotify Tracks matched from YouTube.

        """
        matched_tracks = []
        for i, track in enumerate(self):
            print(f'{i + 1:03} searching track on spotify: '
                  f'{" & ".join(track.artists)} - {track.title}')
            try:
                matched_track = SpotifyTrack.from_youtube(track)
                matched_tracks.append(matched_track)
            except ValueError as e:
                print(e)
                continue
        return matched_tracks


class SpotifyPlaylist(PlayList):
    """
    Spotify playlist. Note that it is unlikely that you will instantiate
    a Spotify playlist yourself. Use the SpotifyChannel instance to retrieve
    existing playlists.

    """
    # spotipy / spotify allow adding up to 100 tracks per API request
    # in contrast, YouTube / Google API requires to add track by track
    _MAX_TRACKS_PER_REQUEST = 100

    def __init__(self, id, name):
        self.api = api.get_or_create_spotify_api()
        self.id = id
        self.name = name
        self._tracks = None

    def _get_tracks(self):
        """
        Spotipy specific way of retrieving all tracks of a playlist.

        Returns
        -------
        tracks : list of bes.track.YouTubeTrack
            List of tracks.

        """
        offset = 0
        tracks = []

        while True:
            response = self.api.user_playlist_tracks(
                user=api.SPOTIFY_USER_ID,
                playlist_id=self.id,
                limit=self._MAX_TRACKS_PER_REQUEST,
                offset=offset,
            )
            for item in response['items']:
                tracks.append(SpotifyTrack.from_item(item))
            offset = len(tracks)
            if len(tracks) == response['total']:
                break
        return tracks

    def add_tracks(self, playlist):
        """
        Add tracks from other playlist, specifically:
        1. will cast input playlist to Spotify (call .to_spotify) to retrieve
           only the tracks for which there are matches on Spotify.
        2. will compare the IDs of matched tracks with existing IDs in the
           playlist.
        3. will remove tracks for which already exist in the playlist
        4. will add remaining tracks to the playlist.

        Notes
        -----
        Contrary to YouTube; there are no limits to how many tracks you can
        add per day (as far as I know, although I suspect that if you start
        spamming the API you may get temporary cooldown).

        Parameters
        ----------
        playlist : bes.playlist.PlayList
            Other playlist to add tracks from.

        """
        ids_existing = [track.id for track in self]
        ids_youtube = [track.id for track in playlist.to_spotify()]

        ids_to_add = list(set(ids_youtube) - set(ids_existing))
        print(f'There are:\n\t- {len(ids_youtube)} tracks matched from YouTube'
              f'\n\t- {len(ids_existing)} tracks existing in Spotify playlist'
              f'\n\t- {len(ids_to_add)} new tracks to add'
             )

        for offset in range(0, len(ids_to_add), self._MAX_TRACKS_PER_REQUEST):
            self.api.playlist_add_items(
                playlist_id=self.id,
                items=ids_to_add[offset:offset + self._MAX_TRACKS_PER_REQUEST],
                position=None,
            )
        print(f'{len(ids_to_add)} tracks added to spotify playlist {self.name}!')

    @classmethod
    def from_item(cls, item):
        """Create Spotify Playlist from the REST API JSON"""
        return cls(
            id=item['id'],
            name=item['name'],
        )

    def to_youtube(self):
        """
        Cast tracks of playlist to YouTube. For each track, it will look for
        matches on YouTube, score them, and return the track scoring the lowest
        risk (under a certain threshold). If no such track exist; the track
        is simply skipped and assumed not to exist on YouTube.

        Returns
        -------
        matched_tracks : list of bes.track.YouTubeTrack
            YouTube Tracks matched from YouTube.

        """
        matched_tracks = []
        for i, track in enumerate(self):
            print(f'{i + 1:03} searching track on spotify: '
                  f'{" & ".join(track.artists)} - {track.title}')
            try:
                matched_track = YouTubeTrack.from_spotify(track)
                matched_tracks.append(matched_track)
            except ValueError as e:
                print(e)
                continue
        return matched_tracks

    def to_spotify(self):
        """Cast tracks to Spotify format (no-op)"""
        return self


class SpotifySavedTracks(SpotifyPlaylist):
    """
    User saved (a.k.a liked) tracks, not handled as a playlist resource by
    Spotify, so this is not strictly a playlist but more a list of tracks.

    """
    def __init__(self):
        super().__init__(id=None, name='spotify likes')

    @classmethod
    def from_item(cls, item):
        raise NotImplementedError

    def _get_tracks(self):
        """Spotifpy specific way of getting liked tracks."""
        offset = 0
        tracks = []

        while True:
            response = self.api.current_user_saved_tracks(
                limit=50,
                offset=offset,
            )
            for item in response['items']:
                tracks.append(SpotifyTrack.from_item(item))
            offset = len(tracks)
            if len(tracks) == response['total']:
                break
        return tracks
