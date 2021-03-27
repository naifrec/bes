from bes import api
from bes.track import SpotifyTrack, YouTubeTrack


class PlayList(object):
    name = None
    id = None
    size = None

    def __init__(self, playlist_id):
        raise NotImplementedError

    @property
    def tracks(self):
        raise NotImplementedError

    def add_tracks(self, ids):
        raise NotImplementedError

    @classmethod
    def from_item(cls, item):
        raise NotImplementedError

    def __len__(self):
        return len(self.tracks)

    def __iter__(self):
        yield from self.tracks


class YouTubePlayList(PlayList):
    def __init__(self, id, name, size=None):
        self.api = api.get_or_create_youtube_api()
        self.id = id
        self.name = name
        self.size = size
        self._tracks = None

    @property
    def tracks(self):
        if self._tracks is None:
            self._tracks = self._get_tracks()
            self.size = len(self._tracks)
        return self._tracks

    def _get_tracks(self):
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
            response = request.execute()
        print(f'{len(ids_to_add)} tracks added to youtube playlist {self.name}!')

    @classmethod
    def from_item(cls, item):
        return cls(
            id=item['id'],
            name=item['snippet']['localized']['title'],
        )

    def to_spotify(self):
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
    _MAX_TRACKS_PER_REQUEST = 100

    def __init__(self, id, name, size=None):
        self.api = api.get_or_create_spotify_api()
        self.id = id
        self.name = name
        self.size = size
        self._tracks = None

    @property
    def tracks(self):
        if self._tracks is None:
            self._tracks = self._get_tracks()
            self.size = len(self._tracks)
        return self._tracks

    def _get_tracks(self):
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

    @classmethod
    def from_item(cls, item):
        return cls(
            id=item['id'],
            name=item['name'],
            size=item['tracks']['total'],
        )

    def add_tracks(self, playlist):
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

    def to_youtube(self):
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


class SpotifySavedTracks(SpotifyPlaylist):
    """
    User saved (a.k.a liked) tracks, not handled as a playlist resource by
    spotify, so this is not strictly a playlist but more a list of tracks.

    """
    def __init__(self):
        super().__init__(id=None, name='spotify likes', size=None)

    @classmethod
    def from_item(cls, item):
        raise NotImplementedError

    def _get_tracks(self):
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
