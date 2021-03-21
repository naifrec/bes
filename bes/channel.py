from bes import api
from bes.playlist import SpotifyPlaylist, YouTubePlayList


class Channel(object):
    """Accepts no ID yet since OAuth scope works for my channel only (mine=True)"""
    def __init__(self,):
        self._playlists = None

    @property
    def playlists(self):
        if self._playlists is None:
            self._playlists = self._get_playlists()
        return self._playlists

    def add_playlist(self, name):
        raise NotImplementedError

    def _get_playlists(self):
        raise NotImplementedError

    def refresh(self):
        self._playlists = None


class YouTubeChannel(Channel):
    def __init__(self):
        super().__init__()
        self.api = api.get_or_create_youtube_api()

    def _get_playlists(self):
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


class SpotifyChannel(Channel):
    def __init__(self):
        super().__init__()
        self.api = api.get_or_create_spotify_api()

    def _get_playlists(self):
        playlists = []
        for item in self.api.user_playlists(api.SPOTIFY_USER_ID)['items']:
            playlists.append(SpotifyPlaylist.from_item(item))
        return playlists

    def add_playlist(self, name):
        self.api.user_playlist_create(
            user=api.SPOTIFY_USER_ID,
            name=name,
            public=True,
        )

