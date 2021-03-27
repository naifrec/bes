from bes.api import get_or_create_spotify_api, get_or_create_youtube_api
from bes.clean import clean
from bes.score import get_risk_score


class Track(object):
    id = None
    title = None
    artists = []
    name = None
    search_string = None

    def from_youtube(self, item):
        raise NotImplementedError

    def from_spotify(self, item):
        raise NotImplementedError


class YouTubeTrack(Track):
    # ordered from most to least likely / dangerous
    TRACK_SEPARATORS = [' ~ ', ' - ', ' – ', ' -- ', '–', '--', '~', '-',
                        '  ', ' ', ]
    ARTIST_SEPARATORS = [' & ', ' x ', ]

    def __init__(self, id, name, channel):
        self.id = id
        self.channel = channel
        self.name = name

        # split artists from track title
        artist, title = self.split_artists_from_title()
        self.title = title
        # split artists
        artists = self.split_artists(artist)
        self.artists = artists

        # create search string
        self.search_string = ' '.join(self.artists) + ' ' + self.title

    @classmethod
    def from_item(cls, item):
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

    def split_artists_from_title(self):
        # check if YouTube music automatically generated track
        topic_string = ' - Topic'
        if topic_string in self.channel:
            artists = self.channel.replace(topic_string, '')
            title = self.name
        # regular YouTube channel, all info is in track name
        else:
            # clean track name
            track_name = clean(self.name)
            # look for separator between artist and track name
            for separator in self.TRACK_SEPARATORS:
                if separator in track_name:
                    break
            # if no separator found, need further processing
            if separator not in track_name:
                raise ValueError(f'parsing error: could not find a separator in: {track_name}')
            splits = track_name.split(separator)
            # if more thant two splits, probably EP or other info in there, need further processing
            if len(splits) != 2:
                raise ValueError(f'parsing error: found more splits than two in: {track_name}')
            artists, title = splits
        return artists, title

    def split_artists(self, artists):
        # look for separator between artist and track name
        for separator in self.ARTIST_SEPARATORS:
            if separator in artists:
                break
        # if no separator found, assume single artist
        if separator not in artists:
            artists = [artists.strip()]
        else:
            artists = [artist.strip() for artist in artists.split(separator)]
        return artists


class SpotifyTrack(Track):
    def __init__(self, id, title, artists):
        self.id = id
        self.title = title
        self.artists = artists
        # create search string
        self.search_string = ' '.join(self.artists) + ' ' + self.title

    @classmethod
    def from_item(cls, item):
        if 'track' in item:
            item = item['track']
        return cls(
            id=item['id'],
            title=item['name'],
            artists=[artist['name'] for artist in item['artists']],
        )

    @classmethod
    def from_youtube(cls, track, threshold=1.0):
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
