from sponsor_match.ml.pipeline import score_and_rank

def recommend_sponsors(club_id: int, club_bucket: str,
                       max_distance: float = 50.0, top_n: int = 10):
    """
    Returns list of {id,name,lat,lon,distance,score} for top_n companies.
    """
    return score_and_rank(
        assoc_id=club_id,
        assoc_bucket=club_bucket,
        max_distance=max_distance,
        top_n=top_n
    )
