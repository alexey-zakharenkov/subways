DEFAULT_INTERVAL = 2.5 * 60  # seconds
KMPH_TO_MPS = 1 / 3.6  # km/h to m/s conversion multiplier
SPEED_ON_TRANSFER = 3.5 * KMPH_TO_MPS  # m/s
TRANSFER_PENALTY = 30  # seconds


def format_colour(colour):
    """Truncate leading # sign."""
    return colour[1:] if colour else None
