import fire

from bes.channel import SpotifyChannel
from bes.playlist import YouTubePlayList


MAPPING = {
    'acid techno case': 'PLBLV0mgoy14pIS8Wk6P04bg5nR9Paq04S',
    'ambient case': 'PLBLV0mgoy14omPMcOzkpHCxAubwLPPHvg',
    'ambient techno case': 'PLBLV0mgoy14rK01Lo753mOviqkbBxQmAO',
    'breakbeat case': 'PLBLV0mgoy14rnOuijW2K3agmvvvVeTJ-2',
    'downtempo case': 'PLBLV0mgoy14q9SLrVo5unTqFmkGh1NDtI',
    'deep house case': 'PLBLV0mgoy14oGSudznl_Y5VM0ox1JooKu',
    'dnb case': 'PLBLV0mgoy14rBGCVEPqHi8KtAZxohHWFE',
    'dub techno case': 'PLBLV0mgoy14o5FNmXBLLu8uLbdcb1NzKx',
    'house case': 'PLBLV0mgoy14r4-fw1ukC0cZi8cTd5D9s-',
    'old school techno case': 'PLBLV0mgoy14qx9ERJAFGQbnqpMyG2U4ZM',
    'microhouse case': 'PLBLV0mgoy14qXCOOQh6DSSvhLHcvHU_oX',
    'trance case': 'PLBLV0mgoy14rZQjnoCZe8DeMJHeW88f9N',
}


def main(playlist_name):
    youtube_playlist_id = MAPPING[playlist_name]
    youtube_playlist = YouTubePlayList(id=youtube_playlist_id, name=playlist_name)

    # get or create spotify channel
    spotify_channel = SpotifyChannel()
    spotify_playlist = spotify_channel.get(playlist_name)

    # add tracks
    spotify_playlist.add_tracks(youtube_playlist)



if __name__ == '__main__':
    fire.Fire(main)
