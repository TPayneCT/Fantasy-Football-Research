"""Score raw Sleeper stat lines with a league's scoring_settings."""


def score(stats, scoring_settings):
    """Sum of stat value x league weight for every stat the league scores."""
    return round(sum(stats.get(k, 0) * w for k, w in scoring_settings.items() if w), 2)
