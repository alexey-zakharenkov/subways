from css_colours import normalize_colour
from structure.consts import ALL_MODES, CONSTRUCTION_KEYS
from structure.error_collector import ErrorCollectorGate
from structure.osm_element import el_center, el_id
from structure.types import IdT, OsmElementT


class Station(ErrorCollectorGate):
    def __init__(
        self, el: OsmElementT, error_collector: ErrorCollectorGate
    ) -> None:
        """Call this with a railway=station OSM feature."""
        ErrorCollectorGate.__init__(self, error_collector)

        self.id: IdT = el_id(el)
        self.element: OsmElementT = el
        self.modes = Station.get_modes(el)
        self.name = el["tags"].get("name", "?")
        self.int_name = el["tags"].get(
            "int_name", el["tags"].get("name:en", None)
        )
        try:
            self.colour = normalize_colour(el["tags"].get("colour", None))
        except ValueError as e:
            self.colour = None
            self.warn(str(e), el)
        self.center = el_center(el)
        if self.center is None:
            raise Exception("Could not find center of {}".format(el))

    @staticmethod
    def get_modes(el: OsmElementT) -> set[str]:
        modes = {m for m in ALL_MODES if el["tags"].get(m) == "yes"}
        if mode := el["tags"].get("station"):
            modes.add(mode)
        return modes

    @staticmethod
    def is_station(el: OsmElementT, modes: set[str]) -> bool:
        # public_transport=station is too ambiguous and unspecific to use,
        # so we expect for it to be backed by railway=station.
        if (
            "tram" in modes
            and el.get("tags", {}).get("railway") == "tram_stop"
        ):
            return True
        if el.get("tags", {}).get("railway") not in ("station", "halt"):
            return False
        for k in CONSTRUCTION_KEYS:
            if k in el["tags"]:
                return False
        # Not checking for station=train, obviously
        if "train" not in modes and Station.get_modes(el).isdisjoint(modes):
            return False
        return True

    def __repr__(self) -> str:
        return "Station(id={}, modes={}, name={}, center={})".format(
            self.id, ",".join(self.modes), self.name, self.center
        )
