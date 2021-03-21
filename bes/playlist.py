from bes import api
from bes.track import SpotifyTrack, YouTubeTrack
from bes.score import get_risk_score


class PlayList(object):
    name = None
    id = None

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
        raise NotImplementedError


class YouTubePlayList(object):
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

    @classmethod
    def from_item(cls, item):
        return cls(
            id=item['id'],
            name=item['snippet']['localized']['title'],
        )

    def __len__(self):
        if self.size is None:
            self.tracks  # get the tracks to get the size
        return self.size


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
            if len(tracks) == self.size:
                break
        return tracks

    @classmethod
    def from_item(cls, item):
        return cls(
            id=item['id'],
            name=item['name'],
            size=item['tracks']['total'],
        )

    def add_tracks(self, tracks):
        ids_existing = [track.id for track in self.tracks]

        ids_youtube = []
        for i, track in enumerate(tracks):
            print(f'Searching track {i + 1:03}: {" & ".join(track.artists)} - {track.title}')
            result = self.api.search(track.search_string)
            matches = [SpotifyTrack.from_item(item) for item in result['tracks']['items']]
            if len(matches):
                risks = []
                for k, match in enumerate(matches):
                    risk, missing_artists, mismatch = get_risk_score(track, match)
                    risks.append(risk)
                    print(f'    - match {k}: risk {risk} - missing artists {" & ".join(missing_artists)} - mismatch in name: {mismatch}')
                if any(risk < 1.0 for risk in risks):
                    match = matches[risks.index(min(risks))]
                    ids_youtube.append(match.id)
                    print(f'    Matched and added track ID with risk score of {min(risks)}.')

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
        print('Tracks added!')

    def __len__(self):
        if self.size is None:
            self.tracks  # get the tracks to get the size
        return self.size
