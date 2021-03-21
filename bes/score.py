def get_risk_score(track, match):
    """Get risk score of matched spotify track with YouTube video."""
    score = 0

    # do the artists match?
    expected_artists = set([artist.casefold() for artist in track.artists])
    matched_artists = set([artist.casefold() for artist in match.artists])
    # union should be the same as intersection
    missing_artists = expected_artists - matched_artists
    if len(missing_artists) and len(expected_artists) > 1:
        # check if name is not stored as single artist like Oden & Fatzo
        expected_artist = ' & '.join(track.artists).casefold().strip()
        matched_artist = match.artists[0].casefold().strip()
        if expected_artist != matched_artist:
            score += len(missing_artists) / len(expected_artists)
        else:
            missing_artists = set()
    else:
        score += len(missing_artists) / len(expected_artists)

    # does the track name match?
    expected_name = track.title.casefold().strip()
    matched_name = match.title.casefold().strip()
    i = 0
    if expected_name != matched_name:
        indices = [i for i in range(min(len(expected_name), len(matched_name))) if matched_name[i] != expected_name[i]]
        index = len(expected_name) if not len(indices) else indices[0]
        score += (index + 1) / len(expected_name)

    return score, missing_artists, matched_name[len(expected_name) - i:]
