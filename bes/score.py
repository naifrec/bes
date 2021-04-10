def get_risk_score(track, other):
    """
    Get "risk" score between a track an another track. The "risk" evaluates
    how likely the two tracks are to be the same, lower being better, with
    0 being a perfect match. This is a super handcrafted score, with little
    to no tuning, will probably not catch all possible cases.

    The scoring rules are:
      * if N artists over M are missing, then risk += N/M
      * if either the track title or the other track title are empty; score +=1
      * if the titles of the two tracks do not match, add to
        score += (index of disagreement between title and other) / (length of track title)

    Parameters
    ----------
    track : bes.track.Track
        Reference track.
    other : bes.track.Track
        Track to compare to reference and evaluate risk for.

    Returns
    -------
    score : float
        Risk score, positive real number. 0 means perfect match.
    missing_artists : list of str
        Missing artists.
    title_deviation : str
        If the title of the two tracks deviate after N elements, this returns
        the title of the "other" track after this deviation. So for instance
        let's say we have:
          1. track.title = "teknology (original mix)"
          2. other.title = "teknology (gods of technology remix)"
        Then title_deviation will be "gods of technology remix)".

    """
    score = 0

    # do the artists match?
    expected_artists = set([artist.casefold() for artist in track.artists])
    matched_artists = set([artist.casefold() for artist in other.artists])
    # union should be the same as intersection
    missing_artists = expected_artists - matched_artists
    if len(missing_artists) and len(expected_artists) > 1:
        # check if name is not stored as single artist like Oden & Fatzo
        expected_artist = ' & '.join(track.artists).casefold().strip()
        matched_artist = other.artists[0].casefold().strip()
        if expected_artist != matched_artist:
            score += len(missing_artists) / len(expected_artists)
        else:
            missing_artists = set()
    else:
        score += len(missing_artists) / len(expected_artists)

    # does the track name match?
    expected_title = track.title.casefold().strip()
    matched_title = other.title.casefold().strip()
    i = 0
    if len(expected_title) == 0 or len(matched_title) == 0:
        # something problematic happened upstream, bump risk by 1
        score += 1
    elif expected_title != matched_title:
        indices = [i for i in range(min(len(expected_title), len(matched_title))) if matched_title[i] != expected_title[i]]
        index = len(expected_title) if not len(indices) else indices[0]
        score += (index + 1) / len(expected_title)

    return score, missing_artists, matched_title[len(expected_title) - i:]
