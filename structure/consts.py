MAX_DISTANCE_STOP_TO_LINE = 50  # in meters

MODES_RAPID = {"subway", "light_rail", "monorail", "train"}
MODES_OVERGROUND = {"tram", "bus", "trolleybus", "aerialway", "ferry"}
DEFAULT_MODES_RAPID = {"subway", "light_rail"}
DEFAULT_MODES_OVERGROUND = {"tram"}  # TODO: bus and trolleybus?
ALL_MODES = MODES_RAPID | MODES_OVERGROUND
RAILWAY_TYPES = {
    "rail",
    "light_rail",
    "subway",
    "narrow_gauge",
    "funicular",
    "monorail",
    "tram",
}
CONSTRUCTION_KEYS = (
    "construction",
    "proposed",
    "construction:railway",
    "proposed:railway",
)
