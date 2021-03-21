from bes.clean import clean


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
        if 'videoOwnerChannelTitle' in item['snippet']:
            channel = item['snippet']['videoOwnerChannelTitle']
        else:
            raise ValueError('This video does not exist anymore.')

        return cls(
            id=item['contentDetails']['videoId'],
            name=item['snippet']['title'],
            channel=channel,
        )

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

    @classmethod
    def from_item(cls, item):
        if 'track' in item:
            item = item['track']
        return cls(
            id=item['id'],
            title=item['name'],
            artists=[artist['name'] for artist in item['artists']],
        )
