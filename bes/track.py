from bes.api import get_or_create_spotify_api, get_or_create_youtube_api
from bes.clean import split_artists_from_title
from bes.score import get_risk_score


class Track(object):
    """
    Abstrack Track class defining the API of object wrapping the concept of
    a track. We will take the exampe of "DJ Krush - Song 1" video on YouTube
    (https://youtu.be/bj3y5vFS3Es) to explain the properties of a track:
        * ID: internal ID on respective backend ("bj3y5vFS3Es")
        * title: track title ("Song 1")
        * artists : track artists (["DJ Krush",])
        * name : DJ Krush - Song 1 (basically the original video name)
        * search_string: dj krush song 1 (simplified search string to be used
          for searching in other backends)

    """
    id = None
    title = None
    artists = []
    name = None
    search_string = None

    @classmethod
    def from_youtube(cls, track, threshold):
        """
        Create track from another YouTube track if exists on Spotify backend. Use
        threshold to hedge your risk, lower threshold means you will be matching
        more tracks; but potentially have more false positives.

        Parameters
        ----------
        track : bes.track.Track
            YouTube track to port to Spotify.
        threshold : float
            Risk score threshold, lower means higher accuracy, but potentially
            increase in false negatives (not matching a track which was
            actually a good match).

        """
        raise NotImplementedError

    @classmethod
    def from_spotify(cls, track, threshold):
        """
        Create track from another Spotify track if exists on YouTube backend. Use
        threshold to hedge your risk, lower threshold means you will be matching
        more tracks; but potentially have more false positives.

        Parameters
        ----------
        track : bes.track.Track
            YouTube track to port to Spotify.
        threshold : float
            Risk score threshold, lower means higher accuracy, but potentially
            increase in false negatives (not matching a track which was
            actually a good match).

        """
        raise NotImplementedError


class YouTubeTrack(Track):
    """
    YouTube track. In addition to the properties of a regular track (see
    docstring of base class), YouTubeTrack has the channel property which
    refers to the channel which posted the track / video.

    Note that it is unlikely you will ever instantiate one yourself, you
    will probably use a YouTubePlayList object to instantiate tracks for you.

    Parameters
    ----------
    id : str
        Video / track ID
    name : str
        Video / track name
    channel : str
        Name of channel posting video.

    """
    def __init__(self, id, name, channel):
        self.id = id
        self.channel = channel
        self.name = name

        # split artists from track title
        artists, title = split_artists_from_title(self)
        self.title = title
        self.artists = artists

        # create search string
        self.search_string = ' '.join(self.artists) + ' ' + self.title

    @classmethod
    def from_item(cls, item):
        """Create YouTubeTrack instance from the REST API JSON."""
        # get channel title
        if 'videoOwnerChannelTitle' in item['snippet']:
            channel = item['snippet']['videoOwnerChannelTitle']
        elif 'channelTitle' in item['snippet']:
            channel = item['snippet']['channelTitle']
        else:
            raise ValueError('This video does not exist anymore.')

        # get video ID
        if 'contentDetails' in item:
            video_id = item['contentDetails']['videoId']
        elif 'id' in item:
            video_id = item['id']['videoId']
        else:
            raise ValueError('This video does not have an ID')

        return cls(
            id=video_id,
            name=item['snippet']['title'],
            channel=channel,
        )

    @classmethod
    def from_spotify(cls, track, threshold=1.0):
        """See base class docstring"""
        # api search, show only top 5
        api = get_or_create_youtube_api(readonly=False)
        request = api.search().list(
            part="snippet",
            maxResults=5,
            q=track.search_string,
            type="video",
        )
        response = request.execute()
        # convert items to YouTube track
        matches = []
        for i, item in enumerate(response['items']):
            try:
                match = cls.from_item(item)
                matches.append(match)
            except ValueError as e:
                print(f'Could not add YouTube match {i+1} because of original error {e}.')
                continue

        # score each match if any, pick lowest scoring track if below threshold
        match = None
        if len(matches):
            risks = []
            for i, match in enumerate(matches):
                risk, missing_artists, mismatch = get_risk_score(track, match)
                risks.append(risk)
                print(f'\t- match {i}:\n\t\t- risk {risk}'
                      f'\n\t\t- missing artists {" & ".join(missing_artists)}'
                      f'\n\t\t- mismatch in name: {mismatch}')
            if any(risk < threshold for risk in risks):
                match = matches[risks.index(min(risks))]
                print(f'matched and added track ID with risk score of {min(risks)}.')
        if match is None:
            raise ValueError(f'no match found on youtube for this track: name '
                             f'{track.name} / search string {track.search_string}')

        return match


class SpotifyTrack(Track):
    """
    Spotify track. See base class docstring for properties.

    Note that it is unlikely you will ever instantiate one yourself, you
    will probably use a SpotifyPlaylist object to instantiate tracks for you.

    Parameters
    ----------
    id : str
        Video / track ID
    title : str
        Track title
    artists : list of str
        List of artists.

    """
    def __init__(self, id, title, artists):
        self.id = id
        self.title = title
        self.artists = artists
        # create search string
        self.search_string = ' '.join(self.artists) + ' ' + self.title

    @classmethod
    def from_item(cls, item):
        """Create SpotifyTrack instance from the REST API JSON."""
        if 'track' in item:
            item = item['track']
        return cls(
            id=item['id'],
            title=item['name'],
            artists=[artist['name'] for artist in item['artists']],
        )

    @classmethod
    def from_youtube(cls, track, threshold=1.0):
        """See base class docstring."""
        api = get_or_create_spotify_api()
        result = api.search(track.search_string)
        matches = [cls.from_item(item) for item in result['tracks']['items']]
        match = None
        if len(matches):
            risks = []
            for i, match in enumerate(matches):
                risk, missing_artists, mismatch = get_risk_score(track, match)
                risks.append(risk)
                print(f'\t- match {i}:\n\t\t- risk {risk}'
                      f'\n\t\t- missing artists {" & ".join(missing_artists)}'
                      f'\n\t\t- mismatch in name: {mismatch}')
            if any(risk < threshold for risk in risks):
                match = matches[risks.index(min(risks))]
                print(f'matched and added track ID with risk score of {min(risks)}.')
        if match is None:
            raise ValueError(f'no match found on spotify for this track: name '
                             f'{track.name} / search string {track.search_string}')
        return match
