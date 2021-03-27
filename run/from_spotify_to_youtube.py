import fire

from bes.channel import SpotifyChannel, YouTubeChannel


def main():
    youtube_channel = YouTubeChannel(readonly=False)
    youtube_playlist = youtube_channel.get('spotify likes')

    # get or create spotify channel
    spotify_channel = SpotifyChannel()
    spotify_playlist = spotify_channel.get_saved_tracks_playlist()

    # add tracks
    youtube_playlist.add_tracks(spotify_playlist)



if __name__ == '__main__':
    fire.Fire(main)
