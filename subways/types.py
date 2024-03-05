from typing import TypeAlias


OsmElementT: TypeAlias = dict
IdT: TypeAlias = str  # Type of feature ids
TransferT: TypeAlias = set[IdT]  # A transfer is a set of StopArea IDs
TransfersT: TypeAlias = list[TransferT]
LonLat: TypeAlias = tuple[float, float]
RailT: TypeAlias = list[LonLat]


class CriticalValidationError(Exception):
    """Is thrown if an error occurs
    that prevents further validation of a city."""
