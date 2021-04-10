"""
Functions to clean up the YouTube video name prior to separating artist name
from track name.

"""
import re

TITLE_SEPARATORS = [' ~ ', ' - ', ' – ', ' -- ', '–', '--', '~', '-', '  ', ' ', ]
ARTIST_SEPARATORS = [' & ', ' x ', ]


def clean_tracklisting(string):
    """Clean tracklisting in track name: 'A1.', 'A2.', etc """
    result = re.search(r'^([ABCD]{1}[1234]{0,1}\.\s?).*$', string, re.IGNORECASE)
    if result is not None:
        tracklisting = result.groups()[0]
        string = string.replace(tracklisting, '')
    return string


def clean_label_or_catalog_number(string):
    """Clean label or catalog ID: '[TMZ12006]', '[Kalahari Oyster Cult]' """
    string = string.replace('【', '[')
    string = string.replace('】', ']')
    result = re.search(r'(\[.*\])', string)
    if result is not None:
        label_or_catalog_number = result.groups()[0]
        string = string.replace(label_or_catalog_number, '')
    return string


def clean_premiere_prefix(string):
    """Clean premiere prefix"""
    # looks for strings like "PREMIERE:", "premiere "
    result = re.search(r'(premiere\:?\s)', string, re.IGNORECASE)
    if result is not None:
        prefix = result.groups()[0]
        string = string.replace(prefix, '')
    return string


def clean_parentheses(string):
    """
    There are often additional information between parentheses. While some
    is extra info distracting the search engines, some need not be removed,
    in particular if they contain the substring: 'mix', 'remix', 'edit',
    'rework', 'reshape', 'dub', 'version'.

    """
    allowed_names = ('mix', 'remix', 'edit', 'rework', 'reshape', 'dub', 'version')
    groups = re.findall(r'(\([^\)]*\))', string)
    if groups:
        if len(groups) > 1:
            # additional parentheses usually contains junk info
            for group in groups[1:]:
                string = string.replace(group, '').strip()
        else:
            # remove parenthesis only if does not contain any allowed name
            group = groups[0].lower()
            if not any(name in group for name in allowed_names):
                string = string.replace(group, '').strip()
    return string


def clean(string):
    """Call all clean functions in sequence"""
    for function in [clean_tracklisting, clean_label_or_catalog_number,
                     clean_premiere_prefix, clean_parentheses]:
        string = function(string)
    return string.strip()


def split_artists_from_title(youtube_track):
    """
    Split track artists from title from a YouTube video name.

    Parameters
    ----------
    youtube_track : bes.track.YouTubeTrack
        Track to process.

    Returns
    -------
    artists : list of str
        List of artists.
    title : str
        Track title.

    """
    # check if YouTube music automatically generated track
    topic_string = ' - Topic'
    if topic_string in youtube_track.channel:
        artists = youtube_track.channel.replace(topic_string, '')
        title = youtube_track.name
    # regular YouTube channel, all info is in track name
    else:
        # clean track name
        track_name = clean(youtube_track.name)
        # look for separator between artist and track name
        for separator in TITLE_SEPARATORS:
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
    return split_artists(artists), title


def split_artists(artists):
    """
    Split artists string into list of artists.

    Parameters
    ----------
    artists : str
        Artist(s) string, example "Oden & Fatzo"

    Returns
    -------
    artists : list of str
        List of artists, example ["Oden", "Fatzo"].

    """
    # look for separator between artist and track name
    for separator in ARTIST_SEPARATORS:
        if separator in artists:
            break

    # if no separator found, assume single artist
    if separator not in artists:
        artists = [artists.strip()]
    else:
        artists = [artist.strip() for artist in artists.split(separator)]
    return artists
