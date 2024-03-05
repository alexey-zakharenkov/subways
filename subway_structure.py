from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Callable, Collection, Iterator
from itertools import chain, islice
from typing import TypeVar

from css_colours import normalize_colour
from structure.consts import (
    CONSTRUCTION_KEYS,
    DEFAULT_MODES_OVERGROUND,
    DEFAULT_MODES_RAPID,
    MAX_DISTANCE_STOP_TO_LINE,
    RAILWAY_TYPES,
)
from structure.error_collector import (
    ErrorCollectorGate,
    ErrorCollectorHolder,
)
from structure.geom_utils import (
    angle_between,
    distance,
    find_segment,
    distance_on_line,
    project_on_line,
)
from structure.osm_element import el_center, el_id
from structure.station import Station
from structure.types import (
    CriticalValidationError,
    IdT,
    LonLat,
    OsmElementT,
    RailT,
    TransfersT,
    TransferT,
)

MAX_DISTANCE_TO_ENTRANCES = 300  # in meters
ALLOWED_STATIONS_MISMATCH = 0.02  # part of total station count
ALLOWED_TRANSFERS_MISMATCH = 0.07  # part of total interchanges count
ALLOWED_ANGLE_BETWEEN_STOPS = 45  # in degrees
DISALLOWED_ANGLE_BETWEEN_STOPS = 20  # in degrees
SUGGEST_TRANSFER_MIN_DISTANCE = 100  # in meters

# If an object was moved not too far compared to previous script run,
# it is likely the same object
DISPLACEMENT_TOLERANCE = 300  # in meters


used_entrances = set()


START_END_TIMES_RE = re.compile(r".*?(\d{2}):(\d{2})-(\d{2}):(\d{2}).*")

T = TypeVar("T")


def get_start_end_times(
    opening_hours: str,
) -> tuple[tuple[int, int], tuple[int, int]] | tuple[None, None]:
    """Very simplified method to parse OSM opening_hours tag.
    We simply take the first HH:MM-HH:MM substring which is the most probable
    opening hours interval for the most of the weekdays.
    """
    start_time, end_time = None, None
    m = START_END_TIMES_RE.match(opening_hours)
    if m:
        ints = tuple(map(int, m.groups()))
        start_time = (ints[0], ints[1])
        end_time = (ints[2], ints[3])
    return start_time, end_time


def osm_interval_to_seconds(interval_str: str) -> int | None:
    """Convert to int an OSM value for 'interval'/'headway' tag
    which may be in these formats:
    HH:MM:SS,
    HH:MM,
    MM,
    M
    (https://wiki.openstreetmap.org/wiki/Key:interval#Format)
    """
    hours, minutes, seconds = 0, 0, 0
    semicolon_count = interval_str.count(":")
    try:
        if semicolon_count == 0:
            minutes = int(interval_str)
        elif semicolon_count == 1:
            hours, minutes = map(int, interval_str.split(":"))
        elif semicolon_count == 2:
            hours, minutes, seconds = map(int, interval_str.split(":"))
        else:
            return None
    except ValueError:
        return None
    return seconds + 60 * minutes + 60 * 60 * hours


def format_elid_list(ids: Collection[IdT]) -> str:
    msg = ", ".join(sorted(ids)[:20])
    if len(ids) > 20:
        msg += ", ..."
    return msg


class StopArea:
    @staticmethod
    def is_stop(el: OsmElementT) -> bool:
        if "tags" not in el:
            return False
        if el["tags"].get("railway") == "stop":
            return True
        if el["tags"].get("public_transport") == "stop_position":
            return True
        return False

    @staticmethod
    def is_platform(el: OsmElementT) -> bool:
        if "tags" not in el:
            return False
        if el["tags"].get("railway") in ("platform", "platform_edge"):
            return True
        if el["tags"].get("public_transport") == "platform":
            return True
        return False

    @staticmethod
    def is_track(el: OsmElementT) -> bool:
        if el["type"] != "way" or "tags" not in el:
            return False
        return el["tags"].get("railway") in RAILWAY_TYPES

    def __init__(
        self,
        station: Station,
        city: City,
        stop_area: OsmElementT | None = None,
    ) -> None:
        """Call this with a Station object."""

        self.element: OsmElementT = stop_area or station.element
        self.id: IdT = el_id(self.element)
        self.station: Station = station
        self.stops = set()  # set of el_ids of stop_positions
        self.platforms = set()  # set of el_ids of platforms
        self.exits = set()  # el_id of subway_entrance/train_station_entrance
        # for leaving the platform
        self.entrances = set()  # el_id of subway/train_station entrance
        # for entering the platform
        self.center = None  # lon, lat of the station centre point
        self.centers = {}  # el_id -> (lon, lat) for all elements
        self.transfer = None  # el_id of a transfer relation

        self.modes = station.modes
        self.name = station.name
        self.int_name = station.int_name
        self.colour = station.colour

        if stop_area:
            self.name = stop_area["tags"].get("name", self.name)
            self.int_name = stop_area["tags"].get(
                "int_name", stop_area["tags"].get("name:en", self.int_name)
            )
            try:
                self.colour = (
                    normalize_colour(stop_area["tags"].get("colour"))
                    or self.colour
                )
            except ValueError as e:
                city.warn(str(e), stop_area)

            self._process_members(station, city, stop_area)
        else:
            self._add_nearby_entrances(station, city)

        if self.exits and not self.entrances:
            city.warn(
                "Only exits for a station, no entrances",
                stop_area or station.element,
            )
        if self.entrances and not self.exits:
            city.warn("No exits for a station", stop_area or station.element)

        for el in self.get_elements():
            self.centers[el] = el_center(city.elements[el])

        """Calculate the center point of the station. This algorithm
        cannot rely on a station node, since many stop_areas can share one.
        Basically it averages center points of all platforms
        and stop positions."""
        if len(self.stops) + len(self.platforms) == 0:
            self.center = station.center
        else:
            self.center = [0, 0]
            for sp in chain(self.stops, self.platforms):
                spc = self.centers[sp]
                for i in range(2):
                    self.center[i] += spc[i]
            for i in range(2):
                self.center[i] /= len(self.stops) + len(self.platforms)

    def _process_members(
        self, station: Station, city: City, stop_area: OsmElementT
    ) -> None:
        # If we have a stop area, add all elements from it
        tracks_detected = False
        for m in stop_area["members"]:
            k = el_id(m)
            m_el = city.elements.get(k)
            if not m_el or "tags" not in m_el:
                continue
            if Station.is_station(m_el, city.modes):
                if k != station.id:
                    city.error("Stop area has multiple stations", stop_area)
            elif StopArea.is_stop(m_el):
                self.stops.add(k)
            elif StopArea.is_platform(m_el):
                self.platforms.add(k)
            elif (entrance_type := m_el["tags"].get("railway")) in (
                "subway_entrance",
                "train_station_entrance",
            ):
                if m_el["type"] != "node":
                    city.warn(f"{entrance_type} is not a node", m_el)
                if (
                    m_el["tags"].get("entrance") != "exit"
                    and m["role"] != "exit_only"
                ):
                    self.entrances.add(k)
                if (
                    m_el["tags"].get("entrance") != "entrance"
                    and m["role"] != "entry_only"
                ):
                    self.exits.add(k)
            elif StopArea.is_track(m_el):
                tracks_detected = True

        if tracks_detected:
            city.warn("Tracks in a stop_area relation", stop_area)

    def _add_nearby_entrances(self, station: Station, city: City) -> None:
        center = station.center
        for entrance_el in (
            el
            for el in city.elements.values()
            if "tags" in el
            and (entrance_type := el["tags"].get("railway"))
            in ("subway_entrance", "train_station_entrance")
        ):
            entrance_id = el_id(entrance_el)
            if entrance_id in city.stop_areas:
                continue  # This entrance belongs to some stop_area
            c_center = el_center(entrance_el)
            if (
                c_center
                and distance(center, c_center) <= MAX_DISTANCE_TO_ENTRANCES
            ):
                if entrance_el["type"] != "node":
                    city.warn(f"{entrance_type} is not a node", entrance_el)
                etag = entrance_el["tags"].get("entrance")
                if etag != "exit":
                    self.entrances.add(entrance_id)
                if etag != "entrance":
                    self.exits.add(entrance_id)

    def get_elements(self) -> set[IdT]:
        result = {self.id, self.station.id}
        result.update(self.entrances)
        result.update(self.exits)
        result.update(self.stops)
        result.update(self.platforms)
        return result

    def __repr__(self) -> str:
        return (
            f"StopArea(id={self.id}, name={self.name}, station={self.station},"
            f" transfer={self.transfer}, center={self.center})"
        )


class RouteStop:
    def __init__(self, stoparea: StopArea) -> None:
        self.stoparea: StopArea = stoparea
        self.stop: LonLat = None  # Stop position, possibly projected
        self.distance = 0  # In meters from the start of the route
        self.platform_entry = None  # Platform el_id
        self.platform_exit = None  # Platform el_id
        self.can_enter = False
        self.can_exit = False
        self.seen_stop = False
        self.seen_platform_entry = False
        self.seen_platform_exit = False
        self.seen_station = False

    @property
    def seen_platform(self) -> bool:
        return self.seen_platform_entry or self.seen_platform_exit

    @staticmethod
    def get_actual_role(
        el: OsmElementT, role: str, modes: set[str]
    ) -> str | None:
        if StopArea.is_stop(el):
            return "stop"
        elif StopArea.is_platform(el):
            return "platform"
        elif Station.is_station(el, modes):
            if "platform" in role:
                return "platform"
            else:
                return "stop"
        return None

    def add(self, member: dict, relation: OsmElementT, city: City) -> None:
        el = city.elements[el_id(member)]
        role = member["role"]

        if StopArea.is_stop(el):
            if "platform" in role:
                city.warn("Stop position in a platform role in a route", el)
            if el["type"] != "node":
                city.error("Stop position is not a node", el)
            self.stop = el_center(el)
            if "entry_only" not in role:
                self.can_exit = True
            if "exit_only" not in role:
                self.can_enter = True

        elif Station.is_station(el, city.modes):
            if el["type"] != "node":
                city.notice("Station in route is not a node", el)

            if not self.seen_stop and not self.seen_platform:
                self.stop = el_center(el)
                self.can_enter = True
                self.can_exit = True

        elif StopArea.is_platform(el):
            if "stop" in role:
                city.warn("Platform in a stop role in a route", el)
            if "exit_only" not in role:
                self.platform_entry = el_id(el)
                self.can_enter = True
            if "entry_only" not in role:
                self.platform_exit = el_id(el)
                self.can_exit = True
            if not self.seen_stop:
                self.stop = el_center(el)

        multiple_check = False
        actual_role = RouteStop.get_actual_role(el, role, city.modes)
        if actual_role == "platform":
            if role == "platform_entry_only":
                multiple_check = self.seen_platform_entry
                self.seen_platform_entry = True
            elif role == "platform_exit_only":
                multiple_check = self.seen_platform_exit
                self.seen_platform_exit = True
            else:
                if role != "platform" and "stop" not in role:
                    city.warn(
                        f'Platform "{el["tags"].get("name", "")}" '
                        f'({el_id(el)}) with invalid role "{role}" in route',
                        relation,
                    )
                multiple_check = self.seen_platform
                self.seen_platform_entry = True
                self.seen_platform_exit = True
        elif actual_role == "stop":
            multiple_check = self.seen_stop
            self.seen_stop = True
        if multiple_check:
            log_function = city.error if actual_role == "stop" else city.notice
            log_function(
                f'Multiple {actual_role}s for a station "'
                f'{el["tags"].get("name", "")} '
                f"({el_id(el)}) in a route relation",
                relation,
            )

    def __repr__(self) -> str:
        return (
            "RouteStop(stop={}, pl_entry={}, pl_exit={}, stoparea={})".format(
                self.stop,
                self.platform_entry,
                self.platform_exit,
                self.stoparea,
            )
        )


class Route:
    """The longest route for a city with a unique ref."""

    @staticmethod
    def is_route(el: OsmElementT, modes: set[str]) -> bool:
        if (
            el["type"] != "relation"
            or el.get("tags", {}).get("type") != "route"
        ):
            return False
        if "members" not in el:
            return False
        if el["tags"].get("route") not in modes:
            return False
        for k in CONSTRUCTION_KEYS:
            if k in el["tags"]:
                return False
        if "ref" not in el["tags"] and "name" not in el["tags"]:
            return False
        return True

    @staticmethod
    def get_network(relation: OsmElementT) -> str | None:
        for k in ("network:metro", "network", "operator"):
            if k in relation["tags"]:
                return relation["tags"][k]
        return None

    @staticmethod
    def get_interval(tags: dict) -> int | None:
        v = None
        for k in ("interval", "headway"):
            if k in tags:
                v = tags[k]
                break
            else:
                for kk in tags:
                    if kk.startswith(k + ":"):
                        v = tags[kk]
                        break
        if not v:
            return None
        return osm_interval_to_seconds(v)

    def stopareas(self) -> Iterator[StopArea]:
        yielded_stopareas = set()
        for route_stop in self:
            stoparea = route_stop.stoparea
            if stoparea not in yielded_stopareas:
                yield stoparea
                yielded_stopareas.add(stoparea)

    def __init__(
        self,
        relation: OsmElementT,
        city: City,
        master: OsmElementT | None = None,
    ) -> None:
        assert Route.is_route(
            relation, city.modes
        ), f"The relation does not seem to be a route: {relation}"
        self.city = city
        self.element: OsmElementT = relation
        self.id: IdT = el_id(relation)

        self.ref = None
        self.name = None
        self.mode = None
        self.colour = None
        self.infill = None
        self.network = None
        self.interval = None
        self.start_time = None
        self.end_time = None
        self.is_circular = False
        self.stops: list[RouteStop] = []
        # Would be a list of (lon, lat) for the longest stretch. Can be empty.
        self.tracks = None
        # Index of the first stop that is located on/near the self.tracks
        self.first_stop_on_rails_index = None
        # Index of the last stop that is located on/near the self.tracks
        self.last_stop_on_rails_index = None

        self.process_tags(master)
        stop_position_elements = self.process_stop_members()
        self.process_tracks(stop_position_elements)

    def build_longest_line(self) -> tuple[list[IdT], set[IdT]]:
        line_nodes: set[IdT] = set()
        last_track: list[IdT] = []
        track: list[IdT] = []
        warned_about_holes = False
        for m in self.element["members"]:
            el = self.city.elements.get(el_id(m), None)
            if not el or not StopArea.is_track(el):
                continue
            if "nodes" not in el or len(el["nodes"]) < 2:
                self.city.error("Cannot find nodes in a railway", el)
                continue
            nodes: list[IdT] = ["n{}".format(n) for n in el["nodes"]]
            if m["role"] == "backward":
                nodes.reverse()
            line_nodes.update(nodes)
            if not track:
                is_first = True
                track.extend(nodes)
            else:
                new_segment = list(nodes)  # copying
                if new_segment[0] == track[-1]:
                    track.extend(new_segment[1:])
                elif new_segment[-1] == track[-1]:
                    track.extend(reversed(new_segment[:-1]))
                elif is_first and track[0] in (
                    new_segment[0],
                    new_segment[-1],
                ):
                    # We can reverse the track and try again
                    track.reverse()
                    if new_segment[0] == track[-1]:
                        track.extend(new_segment[1:])
                    else:
                        track.extend(reversed(new_segment[:-1]))
                else:
                    # Store the track if it is long and clean it
                    if not warned_about_holes:
                        self.city.warn(
                            "Hole in route rails near node {}".format(
                                track[-1]
                            ),
                            self.element,
                        )
                        warned_about_holes = True
                    if len(track) > len(last_track):
                        last_track = track
                    track = []
                is_first = False
        if len(track) > len(last_track):
            last_track = track
        # Remove duplicate points
        last_track = [
            last_track[i]
            for i in range(0, len(last_track))
            if i == 0 or last_track[i - 1] != last_track[i]
        ]
        return last_track, line_nodes

    def get_stop_projections(self) -> tuple[list[dict], Callable[[int], bool]]:
        projected = [project_on_line(x.stop, self.tracks) for x in self.stops]

        def stop_near_tracks_criterion(stop_index: int) -> bool:
            return (
                projected[stop_index]["projected_point"] is not None
                and distance(
                    self.stops[stop_index].stop,
                    projected[stop_index]["projected_point"],
                )
                <= MAX_DISTANCE_STOP_TO_LINE
            )

        return projected, stop_near_tracks_criterion

    def project_stops_on_line(self) -> dict:
        projected, stop_near_tracks_criterion = self.get_stop_projections()

        projected_stops_data = {
            "first_stop_on_rails_index": None,
            "last_stop_on_rails_index": None,
            "stops_on_longest_line": [],  # list [{'route_stop': RouteStop,
            #        'coords': LonLat,
            #        'positions_on_rails': [] }
        }
        first_index = 0
        while first_index < len(self.stops) and not stop_near_tracks_criterion(
            first_index
        ):
            first_index += 1
        projected_stops_data["first_stop_on_rails_index"] = first_index

        last_index = len(self.stops) - 1
        while last_index > projected_stops_data[
            "first_stop_on_rails_index"
        ] and not stop_near_tracks_criterion(last_index):
            last_index -= 1
        projected_stops_data["last_stop_on_rails_index"] = last_index

        for i, route_stop in enumerate(self.stops):
            if not first_index <= i <= last_index:
                continue

            if projected[i]["projected_point"] is None:
                self.city.error(
                    'Stop "{}" {} is nowhere near the tracks'.format(
                        route_stop.stoparea.name, route_stop.stop
                    ),
                    self.element,
                )
            else:
                stop_data = {
                    "route_stop": route_stop,
                    "coords": None,
                    "positions_on_rails": None,
                }
                projected_point = projected[i]["projected_point"]
                # We've got two separate stations with a good stretch of
                # railway tracks between them. Put these on tracks.
                d = round(distance(route_stop.stop, projected_point))
                if d > MAX_DISTANCE_STOP_TO_LINE:
                    self.city.notice(
                        'Stop "{}" {} is {} meters from the tracks'.format(
                            route_stop.stoparea.name, route_stop.stop, d
                        ),
                        self.element,
                    )
                else:
                    stop_data["coords"] = projected_point
                stop_data["positions_on_rails"] = projected[i][
                    "positions_on_line"
                ]
                projected_stops_data["stops_on_longest_line"].append(stop_data)
        return projected_stops_data

    def calculate_distances(self) -> None:
        dist = 0
        vertex = 0
        for i, stop in enumerate(self.stops):
            if i > 0:
                direct = distance(stop.stop, self.stops[i - 1].stop)
                d_line = None
                if (
                    self.first_stop_on_rails_index
                    <= i
                    <= self.last_stop_on_rails_index
                ):
                    d_line = distance_on_line(
                        self.stops[i - 1].stop, stop.stop, self.tracks, vertex
                    )
                if d_line and direct - 10 <= d_line[0] <= direct * 2:
                    vertex = d_line[1]
                    dist += round(d_line[0])
                else:
                    dist += round(direct)
            stop.distance = dist

    def process_tags(self, master: OsmElementT) -> None:
        relation = self.element
        master_tags = {} if not master else master["tags"]
        if "ref" not in relation["tags"] and "ref" not in master_tags:
            self.city.notice("Missing ref on a route", relation)
        self.ref = relation["tags"].get(
            "ref", master_tags.get("ref", relation["tags"].get("name", None))
        )
        self.name = relation["tags"].get("name", None)
        self.mode = relation["tags"]["route"]
        if (
            "colour" not in relation["tags"]
            and "colour" not in master_tags
            and self.mode != "tram"
        ):
            self.city.notice("Missing colour on a route", relation)
        try:
            self.colour = normalize_colour(
                relation["tags"].get("colour", master_tags.get("colour", None))
            )
        except ValueError as e:
            self.colour = None
            self.city.warn(str(e), relation)
        try:
            self.infill = normalize_colour(
                relation["tags"].get(
                    "colour:infill", master_tags.get("colour:infill", None)
                )
            )
        except ValueError as e:
            self.infill = None
            self.city.warn(str(e), relation)
        self.network = Route.get_network(relation)
        self.interval = Route.get_interval(
            relation["tags"]
        ) or Route.get_interval(master_tags)
        self.start_time, self.end_time = get_start_end_times(
            relation["tags"].get(
                "opening_hours", master_tags.get("opening_hours", "")
            )
        )
        if relation["tags"].get("public_transport:version") == "1":
            self.city.warn(
                "Public transport version is 1, which means the route "
                "is an unsorted pile of objects",
                relation,
            )

    def process_stop_members(self) -> list[OsmElementT]:
        stations: set[StopArea] = set()  # temporary for recording stations
        seen_stops = False
        seen_platforms = False
        repeat_pos = None
        stop_position_elements: list[OsmElementT] = []
        for m in self.element["members"]:
            if "inactive" in m["role"]:
                continue
            k = el_id(m)
            if k in self.city.stations:
                st_list = self.city.stations[k]
                st = st_list[0]
                if len(st_list) > 1:
                    self.city.error(
                        f"Ambiguous station {st.name} in route. Please "
                        "use stop_position or split interchange stations",
                        self.element,
                    )
                el = self.city.elements[k]
                actual_role = RouteStop.get_actual_role(
                    el, m["role"], self.city.modes
                )
                if actual_role:
                    if m["role"] and actual_role not in m["role"]:
                        self.city.warn(
                            "Wrong role '{}' for {} {}".format(
                                m["role"], actual_role, k
                            ),
                            self.element,
                        )
                    if repeat_pos is None:
                        if not self.stops or st not in stations:
                            stop = RouteStop(st)
                            self.stops.append(stop)
                            stations.add(st)
                        elif self.stops[-1].stoparea.id == st.id:
                            stop = self.stops[-1]
                        else:
                            # We've got a repeat
                            if (
                                (seen_stops and seen_platforms)
                                or (
                                    actual_role == "stop"
                                    and not seen_platforms
                                )
                                or (
                                    actual_role == "platform"
                                    and not seen_stops
                                )
                            ):
                                # Circular route!
                                stop = RouteStop(st)
                                self.stops.append(stop)
                                stations.add(st)
                            else:
                                repeat_pos = 0
                    if repeat_pos is not None:
                        if repeat_pos >= len(self.stops):
                            continue
                        # Check that the type matches
                        if (actual_role == "stop" and seen_stops) or (
                            actual_role == "platform" and seen_platforms
                        ):
                            self.city.error(
                                'Found an out-of-place {}: "{}" ({})'.format(
                                    actual_role, el["tags"].get("name", ""), k
                                ),
                                self.element,
                            )
                            continue
                        # Find the matching stop starting with index repeat_pos
                        while (
                            repeat_pos < len(self.stops)
                            and self.stops[repeat_pos].stoparea.id != st.id
                        ):
                            repeat_pos += 1
                        if repeat_pos >= len(self.stops):
                            self.city.error(
                                "Incorrect order of {}s at {}".format(
                                    actual_role, k
                                ),
                                self.element,
                            )
                            continue
                        stop = self.stops[repeat_pos]

                    stop.add(m, self.element, self.city)
                    if repeat_pos is None:
                        seen_stops |= stop.seen_stop or stop.seen_station
                        seen_platforms |= stop.seen_platform

                    if StopArea.is_stop(el):
                        stop_position_elements.append(el)

                    continue

            if k not in self.city.elements:
                if "stop" in m["role"] or "platform" in m["role"]:
                    raise CriticalValidationError(
                        f"{m['role']} {m['type']} {m['ref']} for route "
                        f"relation {self.element['id']} is not in the dataset"
                    )
                continue
            el = self.city.elements[k]
            if "tags" not in el:
                self.city.error(
                    f"Untagged object {k} in a route", self.element
                )
                continue

            is_under_construction = False
            for ck in CONSTRUCTION_KEYS:
                if ck in el["tags"]:
                    self.city.warn(
                        f"Under construction {m['role'] or 'feature'} {k} "
                        "in route. Consider setting 'inactive' role or "
                        "removing construction attributes",
                        self.element,
                    )
                    is_under_construction = True
                    break
            if is_under_construction:
                continue

            if Station.is_station(el, self.city.modes):
                # A station may be not included in this route due to previous
                # 'stop area has multiple stations' error. No other error
                # message is needed.
                pass
            elif el["tags"].get("railway") in ("station", "halt"):
                self.city.error(
                    "Missing station={} on a {}".format(self.mode, m["role"]),
                    el,
                )
            else:
                actual_role = RouteStop.get_actual_role(
                    el, m["role"], self.city.modes
                )
                if actual_role:
                    self.city.error(
                        f"{actual_role} {m['type']} {m['ref']} is not "
                        "connected to a station in route",
                        self.element,
                    )
                elif not StopArea.is_track(el):
                    self.city.warn(
                        "Unknown member type for {} {} in route".format(
                            m["type"], m["ref"]
                        ),
                        self.element,
                    )
        return stop_position_elements

    def process_tracks(
        self, stop_position_elements: list[OsmElementT]
    ) -> None:
        tracks, line_nodes = self.build_longest_line()

        for stop_el in stop_position_elements:
            stop_id = el_id(stop_el)
            if stop_id not in line_nodes:
                self.city.warn(
                    'Stop position "{}" ({}) is not on tracks'.format(
                        stop_el["tags"].get("name", ""), stop_id
                    ),
                    self.element,
                )

        # self.tracks would be a list of (lon, lat) for the longest stretch.
        # Can be empty.
        self.tracks = [el_center(self.city.elements.get(k)) for k in tracks]
        if (
            None in self.tracks
        ):  # usually, extending BBOX for the city is needed
            self.tracks = []
            for n in filter(lambda x: x not in self.city.elements, tracks):
                self.city.warn(
                    f"The dataset is missing the railway tracks node {n}",
                    self.element,
                )
                break

        if len(self.stops) > 1:
            self.is_circular = (
                self.stops[0].stoparea == self.stops[-1].stoparea
            )
            if (
                self.is_circular
                and self.tracks
                and self.tracks[0] != self.tracks[-1]
            ):
                self.city.warn(
                    "Non-closed rail sequence in a circular route",
                    self.element,
                )

            projected_stops_data = self.project_stops_on_line()
            self.check_and_recover_stops_order(projected_stops_data)
            self.apply_projected_stops_data(projected_stops_data)

    def apply_projected_stops_data(self, projected_stops_data: dict) -> None:
        """Store better stop coordinates and indexes of first/last stops
        that lie on a continuous track line, to the instance attributes.
        """
        for attr in ("first_stop_on_rails_index", "last_stop_on_rails_index"):
            setattr(self, attr, projected_stops_data[attr])

        for stop_data in projected_stops_data["stops_on_longest_line"]:
            route_stop = stop_data["route_stop"]
            route_stop.positions_on_rails = stop_data["positions_on_rails"]
            if stop_coords := stop_data["coords"]:
                route_stop.stop = stop_coords

    def get_extended_tracks(self) -> RailT:
        """Amend tracks with points of leading/trailing self.stops
        that were not projected onto the longest tracks line.
        Return a new array.
        """
        if self.first_stop_on_rails_index >= len(self.stops):
            tracks = [route_stop.stop for route_stop in self.stops]
        else:
            tracks = (
                [
                    route_stop.stop
                    for i, route_stop in enumerate(self.stops)
                    if i < self.first_stop_on_rails_index
                ]
                + self.tracks
                + [
                    route_stop.stop
                    for i, route_stop in enumerate(self.stops)
                    if i > self.last_stop_on_rails_index
                ]
            )
        return tracks

    def get_truncated_tracks(self, tracks: RailT) -> RailT:
        """Truncate leading/trailing segments of `tracks` param
        that are beyond the first and last stop locations.
        Return a new array.
        """
        if self.is_circular:
            return tracks.copy()

        first_stop_location = find_segment(self.stops[0].stop, tracks, 0)
        last_stop_location = find_segment(self.stops[-1].stop, tracks, 0)

        if last_stop_location != (None, None):
            seg2, u2 = last_stop_location
            if u2 == 0.0:
                # Make seg2 the segment the last_stop_location is
                # at the middle or end of
                seg2 -= 1
                # u2 = 1.0
            if seg2 + 2 < len(tracks):
                tracks = tracks[0 : seg2 + 2]  # noqa E203
            tracks[-1] = self.stops[-1].stop

        if first_stop_location != (None, None):
            seg1, u1 = first_stop_location
            if u1 == 1.0:
                # Make seg1 the segment the first_stop_location is
                # at the beginning or middle of
                seg1 += 1
                # u1 = 0.0
            if seg1 > 0:
                tracks = tracks[seg1:]
            tracks[0] = self.stops[0].stop

        return tracks

    def are_tracks_complete(self) -> bool:
        return (
            self.first_stop_on_rails_index == 0
            and self.last_stop_on_rails_index == len(self) - 1
        )

    def get_tracks_geometry(self) -> RailT:
        tracks = self.get_extended_tracks()
        tracks = self.get_truncated_tracks(tracks)
        return tracks

    def check_stops_order_by_angle(self) -> tuple[list[str], list[str]]:
        disorder_warnings = []
        disorder_errors = []
        for i, route_stop in enumerate(
            islice(self.stops, 1, len(self.stops) - 1), start=1
        ):
            angle = angle_between(
                self.stops[i - 1].stop,
                route_stop.stop,
                self.stops[i + 1].stop,
            )
            if angle < ALLOWED_ANGLE_BETWEEN_STOPS:
                msg = (
                    "Angle between stops around "
                    f'"{route_stop.stoparea.name}" {route_stop.stop} '
                    f"is too narrow, {angle} degrees"
                )
                if angle < DISALLOWED_ANGLE_BETWEEN_STOPS:
                    disorder_errors.append(msg)
                else:
                    disorder_warnings.append(msg)
        return disorder_warnings, disorder_errors

    def check_stops_order_on_tracks_direct(
        self, stop_sequence: Iterator[dict]
    ) -> str | None:
        """Checks stops order on tracks, following stop_sequence
        in direct order only.
        :param stop_sequence: list of dict{'route_stop', 'positions_on_rails',
            'coords'} for RouteStops that belong to the longest contiguous
            sequence of tracks in a route.
        :return: error message on the first order violation or None.
        """
        allowed_order_violations = 1 if self.is_circular else 0
        max_position_on_rails = -1
        for stop_data in stop_sequence:
            positions_on_rails = stop_data["positions_on_rails"]
            suitable_occurrence = 0
            while (
                suitable_occurrence < len(positions_on_rails)
                and positions_on_rails[suitable_occurrence]
                < max_position_on_rails
            ):
                suitable_occurrence += 1
            if suitable_occurrence == len(positions_on_rails):
                if allowed_order_violations > 0:
                    suitable_occurrence -= 1
                    allowed_order_violations -= 1
                else:
                    route_stop = stop_data["route_stop"]
                    return (
                        "Stops on tracks are unordered near "
                        f'"{route_stop.stoparea.name}" {route_stop.stop}'
                    )
            max_position_on_rails = positions_on_rails[suitable_occurrence]

    def check_stops_order_on_tracks(
        self, projected_stops_data: dict
    ) -> str | None:
        """Checks stops order on tracks, trying direct and reversed
            order of stops in the stop_sequence.
        :param projected_stops_data: info about RouteStops that belong to the
        longest contiguous sequence of tracks in a route. May be changed
        if tracks reversing is performed.
        :return: error message on the first order violation or None.
        """
        error_message = self.check_stops_order_on_tracks_direct(
            projected_stops_data["stops_on_longest_line"]
        )
        if error_message:
            error_message_reversed = self.check_stops_order_on_tracks_direct(
                reversed(projected_stops_data["stops_on_longest_line"])
            )
            if error_message_reversed is None:
                error_message = None
                self.city.warn(
                    "Tracks seem to go in the opposite direction to stops",
                    self.element,
                )
                self.tracks.reverse()
                new_projected_stops_data = self.project_stops_on_line()
                projected_stops_data.update(new_projected_stops_data)

        return error_message

    def check_stops_order(
        self, projected_stops_data: dict
    ) -> tuple[list[str], list[str]]:
        (
            angle_disorder_warnings,
            angle_disorder_errors,
        ) = self.check_stops_order_by_angle()
        disorder_on_tracks_error = self.check_stops_order_on_tracks(
            projected_stops_data
        )
        disorder_warnings = angle_disorder_warnings
        disorder_errors = angle_disorder_errors
        if disorder_on_tracks_error:
            disorder_errors.append(disorder_on_tracks_error)
        return disorder_warnings, disorder_errors

    def check_and_recover_stops_order(
        self, projected_stops_data: dict
    ) -> None:
        """
        :param projected_stops_data: may change if we need to reverse tracks
        """
        disorder_warnings, disorder_errors = self.check_stops_order(
            projected_stops_data
        )
        if disorder_warnings or disorder_errors:
            resort_success = False
            if self.city.recovery_data:
                resort_success = self.try_resort_stops()
                if resort_success:
                    for msg in disorder_warnings:
                        self.city.notice(msg, self.element)
                    for msg in disorder_errors:
                        self.city.warn(
                            "Fixed with recovery data: " + msg, self.element
                        )

            if not resort_success:
                for msg in disorder_warnings:
                    self.city.notice(msg, self.element)
                for msg in disorder_errors:
                    self.city.error(msg, self.element)

    def try_resort_stops(self) -> bool:
        """Precondition: self.city.recovery_data is not None.
        Return success of station order recovering."""
        self_stops = {}  # station name => RouteStop
        for stop in self.stops:
            station = stop.stoparea.station
            stop_name = station.name
            if stop_name == "?" and station.int_name:
                stop_name = station.int_name
            # We won't programmatically recover routes with repeating stations:
            # such cases are rare and deserves manual verification
            if stop_name in self_stops:
                return False
            self_stops[stop_name] = stop

        route_id = (self.colour, self.ref)
        if route_id not in self.city.recovery_data:
            return False

        stop_names = list(self_stops.keys())
        suitable_itineraries = []
        for itinerary in self.city.recovery_data[route_id]:
            itinerary_stop_names = [
                stop["name"] for stop in itinerary["stations"]
            ]
            if not (
                len(stop_names) == len(itinerary_stop_names)
                and sorted(stop_names) == sorted(itinerary_stop_names)
            ):
                continue
            big_station_displacement = False
            for it_stop in itinerary["stations"]:
                name = it_stop["name"]
                it_stop_center = it_stop["center"]
                self_stop_center = self_stops[name].stoparea.station.center
                if (
                    distance(it_stop_center, self_stop_center)
                    > DISPLACEMENT_TOLERANCE
                ):
                    big_station_displacement = True
                    break
            if not big_station_displacement:
                suitable_itineraries.append(itinerary)

        if len(suitable_itineraries) == 0:
            return False
        elif len(suitable_itineraries) == 1:
            matching_itinerary = suitable_itineraries[0]
        else:
            from_tag = self.element["tags"].get("from")
            to_tag = self.element["tags"].get("to")
            if not from_tag and not to_tag:
                return False
            matching_itineraries = [
                itin
                for itin in suitable_itineraries
                if from_tag
                and itin["from"] == from_tag
                or to_tag
                and itin["to"] == to_tag
            ]
            if len(matching_itineraries) != 1:
                return False
            matching_itinerary = matching_itineraries[0]
        self.stops = [
            self_stops[stop["name"]] for stop in matching_itinerary["stations"]
        ]
        return True

    def get_end_transfers(self) -> tuple[IdT, IdT]:
        """Using transfer ids because a train can arrive at different
        stations within a transfer. But disregard transfer that may give
        an impression of a circular route (for example,
        Simonis / Elisabeth station and route 2 in Brussels).
        """
        return (
            (self[0].stoparea.id, self[-1].stoparea.id)
            if (
                self[0].stoparea.transfer is not None
                and self[0].stoparea.transfer == self[-1].stoparea.transfer
            )
            else (
                self[0].stoparea.transfer or self[0].stoparea.id,
                self[-1].stoparea.transfer or self[-1].stoparea.id,
            )
        )

    def get_transfers_sequence(self) -> list[IdT]:
        """Return a list of stoparea or transfer (if not None) ids."""
        transfer_seq = [
            stop.stoparea.transfer or stop.stoparea.id for stop in self
        ]
        if (
            self[0].stoparea.transfer is not None
            and self[0].stoparea.transfer == self[-1].stoparea.transfer
        ):
            transfer_seq[0], transfer_seq[-1] = self.get_end_transfers()
        return transfer_seq

    def __len__(self) -> int:
        return len(self.stops)

    def __getitem__(self, i) -> RouteStop:
        return self.stops[i]

    def __iter__(self) -> Iterator[RouteStop]:
        return iter(self.stops)

    def __repr__(self) -> str:
        return (
            "Route(id={}, mode={}, ref={}, name={}, network={}, interval={}, "
            "circular={}, num_stops={}, line_length={} m, from={}, to={}"
        ).format(
            self.id,
            self.mode,
            self.ref,
            self.name,
            self.network,
            self.interval,
            self.is_circular,
            len(self.stops),
            self.stops[-1].distance,
            self.stops[0],
            self.stops[-1],
        )


class RouteMaster:
    def __init__(self, city: City, master: OsmElementT = None) -> None:
        self.city = city
        self.routes = []
        self.best: Route = None
        self.id: IdT = el_id(master)
        self.has_master = master is not None
        self.interval_from_master = False
        if master:
            self.ref = master["tags"].get(
                "ref", master["tags"].get("name", None)
            )
            try:
                self.colour = normalize_colour(
                    master["tags"].get("colour", None)
                )
            except ValueError:
                self.colour = None
            try:
                self.infill = normalize_colour(
                    master["tags"].get("colour:infill", None)
                )
            except ValueError:
                self.infill = None
            self.network = Route.get_network(master)
            self.mode = master["tags"].get(
                "route_master", None
            )  # This tag is required, but okay
            self.name = master["tags"].get("name", None)
            self.interval = Route.get_interval(master["tags"])
            self.interval_from_master = self.interval is not None
        else:
            self.ref = None
            self.colour = None
            self.infill = None
            self.network = None
            self.mode = None
            self.name = None
            self.interval = None

    def stopareas(self) -> Iterator[StopArea]:
        yielded_stopareas = set()
        for route in self:
            for stoparea in route.stopareas():
                if stoparea not in yielded_stopareas:
                    yield stoparea
                    yielded_stopareas.add(stoparea)

    def add(self, route: Route) -> None:
        if not self.network:
            self.network = route.network
        elif route.network and route.network != self.network:
            self.city.error(
                'Route has different network ("{}") from master "{}"'.format(
                    route.network, self.network
                ),
                route.element,
            )

        if not self.colour:
            self.colour = route.colour
        elif route.colour and route.colour != self.colour:
            self.city.notice(
                'Route "{}" has different colour from master "{}"'.format(
                    route.colour, self.colour
                ),
                route.element,
            )

        if not self.infill:
            self.infill = route.infill
        elif route.infill and route.infill != self.infill:
            self.city.notice(
                (
                    f'Route "{route.infill}" has different infill colour '
                    f'from master "{self.infill}"'
                ),
                route.element,
            )

        if not self.ref:
            self.ref = route.ref
        elif route.ref != self.ref:
            self.city.notice(
                'Route "{}" has different ref from master "{}"'.format(
                    route.ref, self.ref
                ),
                route.element,
            )

        if not self.name:
            self.name = route.name

        if not self.mode:
            self.mode = route.mode
        elif route.mode != self.mode:
            self.city.error(
                "Incompatible PT mode: master has {} and route has {}".format(
                    self.mode, route.mode
                ),
                route.element,
            )
            return

        if not self.interval_from_master and route.interval:
            if not self.interval:
                self.interval = route.interval
            else:
                self.interval = min(self.interval, route.interval)

        # Choose minimal id for determinancy
        if not self.has_master and (not self.id or self.id > route.id):
            self.id = route.id

        self.routes.append(route)
        if (
            not self.best
            or len(route.stops) > len(self.best.stops)
            or (
                # Choose route with minimal id for determinancy
                len(route.stops) == len(self.best.stops)
                and route.element["id"] < self.best.element["id"]
            )
        ):
            self.best = route

    def get_meaningful_routes(self) -> list[Route]:
        return [route for route in self if len(route) >= 2]

    def find_twin_routes(self) -> dict[Route, Route]:
        """Two non-circular routes are twins if they have the same end
        stations and opposite directions, and the number of stations is
        the same or almost the same. We'll then find stops that are present
        in one direction and is missing in another direction - to warn.
        """

        twin_routes = {}  # route => "twin" route

        for route in self.get_meaningful_routes():
            if route.is_circular:
                continue  # Difficult to calculate. TODO(?) in the future
            if route in twin_routes:
                continue

            route_transfer_ids = set(route.get_transfers_sequence())
            ends = route.get_end_transfers()
            ends_reversed = ends[::-1]

            twin_candidates = [
                r
                for r in self
                if not r.is_circular
                and r not in twin_routes
                and r.get_end_transfers() == ends_reversed
                # If absolute or relative difference in station count is large,
                # possibly it's an express version of a route - skip it.
                and (
                    abs(len(r) - len(route)) <= 2
                    or abs(len(r) - len(route)) / max(len(r), len(route))
                    <= 0.2
                )
            ]

            if not twin_candidates:
                continue

            twin_route = min(
                twin_candidates,
                key=lambda r: len(
                    route_transfer_ids ^ set(r.get_transfers_sequence())
                ),
            )
            twin_routes[route] = twin_route
            twin_routes[twin_route] = route

        return twin_routes

    def check_return_routes(self) -> None:
        """Check if a route has return direction, and if twin routes
        miss stations.
        """
        meaningful_routes = self.get_meaningful_routes()

        if len(meaningful_routes) == 0:
            self.city.error(
                f"An empty route master {self.id}. "
                "Please set construction:route if it is under construction"
            )
        elif len(meaningful_routes) == 1:
            log_function = (
                self.city.error
                if not self.best.is_circular
                else self.city.notice
            )
            log_function(
                "Only one route in route_master. "
                "Please check if it needs a return route",
                self.best.element,
            )
        else:
            self.check_return_circular_routes()
            self.check_return_noncircular_routes()

    def check_return_noncircular_routes(self) -> None:
        routes = [
            route
            for route in self.get_meaningful_routes()
            if not route.is_circular
        ]
        all_ends = {route.get_end_transfers(): route for route in routes}
        for route in routes:
            ends = route.get_end_transfers()
            if ends[::-1] not in all_ends:
                self.city.notice(
                    "Route does not have a return direction", route.element
                )

        twin_routes = self.find_twin_routes()
        for route1, route2 in twin_routes.items():
            if route1.id > route2.id:
                continue  # to process a pair of routes only once
                # and to ensure the order of routes in the pair
            self.alert_twin_routes_differ(route1, route2)

    def check_return_circular_routes(self) -> None:
        routes = {
            route
            for route in self.get_meaningful_routes()
            if route.is_circular
        }
        routes_having_backward = set()

        for route in routes:
            if route in routes_having_backward:
                continue
            transfer_sequence1 = [
                stop.stoparea.transfer or stop.stoparea.id for stop in route
            ]
            transfer_sequence1.pop()
            for potential_backward_route in routes - {route}:
                transfer_sequence2 = [
                    stop.stoparea.transfer or stop.stoparea.id
                    for stop in potential_backward_route
                ][
                    -2::-1
                ]  # truncate repeated first stop and reverse
                common_subsequence = self.find_common_circular_subsequence(
                    transfer_sequence1, transfer_sequence2
                )
                if len(common_subsequence) >= 0.8 * min(
                    len(transfer_sequence1), len(transfer_sequence2)
                ):
                    routes_having_backward.add(route)
                    routes_having_backward.add(potential_backward_route)
                    break

        for route in routes - routes_having_backward:
            self.city.notice(
                "Route does not have a return direction", route.element
            )

    @staticmethod
    def find_common_circular_subsequence(
        seq1: list[T], seq2: list[T]
    ) -> list[T]:
        """seq1 and seq2 are supposed to be stops of some circular routes.
        Prerequisites to rely on the result:
         - elements of each sequence are not repeated
         - the order of stations is not violated.
        Under these conditions we don't need LCS algorithm. Linear scan is
        sufficient.
        """
        i1, i2 = -1, -1
        for i1, x in enumerate(seq1):
            try:
                i2 = seq2.index(x)
            except ValueError:
                continue
            else:
                # x is found both in seq1 and seq2
                break

        if i2 == -1:
            return []

        # Shift cyclically so that the common element takes the first position
        # both in seq1 and seq2
        seq1 = seq1[i1:] + seq1[:i1]
        seq2 = seq2[i2:] + seq2[:i2]

        common_subsequence = []
        i2 = 0
        for x in seq1:
            try:
                i2 = seq2.index(x, i2)
            except ValueError:
                continue
            common_subsequence.append(x)
            i2 += 1
            if i2 >= len(seq2):
                break
        return common_subsequence

    def alert_twin_routes_differ(self, route1: Route, route2: Route) -> None:
        """Arguments are that route1.id < route2.id"""
        (
            stops_missing_from_route1,
            stops_missing_from_route2,
            stops_that_dont_match,
        ) = self.calculate_twin_routes_diff(route1, route2)

        for st in stops_missing_from_route1:
            if (
                not route1.are_tracks_complete()
                or (
                    projected_point := project_on_line(
                        st.stoparea.center, route1.tracks
                    )["projected_point"]
                )
                is not None
                and distance(st.stoparea.center, projected_point)
                <= MAX_DISTANCE_STOP_TO_LINE
            ):
                self.city.notice(
                    f"Stop {st.stoparea.station.name} {st.stop} is included "
                    f"in the {route2.id} but not included in {route1.id}",
                    route1.element,
                )

        for st in stops_missing_from_route2:
            if (
                not route2.are_tracks_complete()
                or (
                    projected_point := project_on_line(
                        st.stoparea.center, route2.tracks
                    )["projected_point"]
                )
                is not None
                and distance(st.stoparea.center, projected_point)
                <= MAX_DISTANCE_STOP_TO_LINE
            ):
                self.city.notice(
                    f"Stop {st.stoparea.station.name} {st.stop} is included "
                    f"in the {route1.id} but not included in {route2.id}",
                    route2.element,
                )

        for st1, st2 in stops_that_dont_match:
            if (
                st1.stoparea.station == st2.stoparea.station
                or distance(st1.stop, st2.stop) < SUGGEST_TRANSFER_MIN_DISTANCE
            ):
                self.city.notice(
                    "Should there be one stoparea or a transfer between "
                    f"{st1.stoparea.station.name} {st1.stop} and "
                    f"{st2.stoparea.station.name} {st2.stop}?",
                    route1.element,
                )

    @staticmethod
    def calculate_twin_routes_diff(route1: Route, route2: Route) -> tuple:
        """Wagner–Fischer algorithm for stops diff in two twin routes."""

        stops1 = route1.stops
        stops2 = route2.stops[::-1]

        def stops_match(stop1: RouteStop, stop2: RouteStop) -> bool:
            return (
                stop1.stoparea == stop2.stoparea
                or stop1.stoparea.transfer is not None
                and stop1.stoparea.transfer == stop2.stoparea.transfer
            )

        d = [[0] * (len(stops2) + 1) for _ in range(len(stops1) + 1)]
        d[0] = list(range(len(stops2) + 1))
        for i in range(len(stops1) + 1):
            d[i][0] = i

        for i in range(1, len(stops1) + 1):
            for j in range(1, len(stops2) + 1):
                d[i][j] = (
                    d[i - 1][j - 1]
                    if stops_match(stops1[i - 1], stops2[j - 1])
                    else min((d[i - 1][j], d[i][j - 1], d[i - 1][j - 1])) + 1
                )

        stops_missing_from_route1: list[RouteStop] = []
        stops_missing_from_route2: list[RouteStop] = []
        stops_that_dont_match: list[tuple[RouteStop, RouteStop]] = []

        i = len(stops1)
        j = len(stops2)
        while not (i == 0 and j == 0):
            action = None
            if i > 0 and j > 0:
                match = stops_match(stops1[i - 1], stops2[j - 1])
                if match and d[i - 1][j - 1] == d[i][j]:
                    action = "no"
                elif not match and d[i - 1][j - 1] + 1 == d[i][j]:
                    action = "change"
            if not action and i > 0 and d[i - 1][j] + 1 == d[i][j]:
                action = "add_2"
            if not action and j > 0 and d[i][j - 1] + 1 == d[i][j]:
                action = "add_1"

            match action:
                case "add_1":
                    stops_missing_from_route1.append(stops2[j - 1])
                    j -= 1
                case "add_2":
                    stops_missing_from_route2.append(stops1[i - 1])
                    i -= 1
                case _:
                    if action == "change":
                        stops_that_dont_match.append(
                            (stops1[i - 1], stops2[j - 1])
                        )
                    i -= 1
                    j -= 1
        return (
            stops_missing_from_route1,
            stops_missing_from_route2,
            stops_that_dont_match,
        )

    def __len__(self) -> int:
        return len(self.routes)

    def __getitem__(self, i) -> Route:
        return self.routes[i]

    def __iter__(self) -> Iterator[Route]:
        return iter(self.routes)

    def __repr__(self) -> str:
        return (
            f"RouteMaster(id={self.id}, mode={self.mode}, ref={self.ref}, "
            f"name={self.name}, network={self.network}, "
            f"num_variants={len(self.routes)}"
        )


class City(ErrorCollectorHolder, ErrorCollectorGate):
    route_class = Route

    def __init__(self, city_data: dict, overground: bool = False) -> None:
        ErrorCollectorHolder.__init__(self)
        self.validate_called = False
        self.id = None
        self.try_fill_int_attribute(city_data, "id")
        self.name = city_data["name"]
        self.country = city_data["country"]
        self.continent = city_data["continent"]
        self.overground = overground
        if not overground:
            self.try_fill_int_attribute(city_data, "num_stations")
            self.try_fill_int_attribute(city_data, "num_lines", "0")
            self.try_fill_int_attribute(city_data, "num_light_lines", "0")
            self.try_fill_int_attribute(city_data, "num_interchanges", "0")
        else:
            self.try_fill_int_attribute(city_data, "num_tram_lines", "0")
            self.try_fill_int_attribute(city_data, "num_trolleybus_lines", "0")
            self.try_fill_int_attribute(city_data, "num_bus_lines", "0")
            self.try_fill_int_attribute(city_data, "num_other_lines", "0")

        # Acquiring list of networks and modes
        networks = (
            None
            if not city_data["networks"]
            else city_data["networks"].split(":")
        )
        if not networks or len(networks[-1]) == 0:
            self.networks = []
        else:
            self.networks = set(
                filter(None, [x.strip() for x in networks[-1].split(";")])
            )
        if not networks or len(networks) < 2 or len(networks[0]) == 0:
            if self.overground:
                self.modes = DEFAULT_MODES_OVERGROUND
            else:
                self.modes = DEFAULT_MODES_RAPID
        else:
            self.modes = {x.strip() for x in networks[0].split(",")}

        # Reversing bbox so it is (xmin, ymin, xmax, ymax)
        bbox = city_data["bbox"].split(",")
        if len(bbox) == 4:
            self.bbox = [float(bbox[i]) for i in (1, 0, 3, 2)]
        else:
            self.bbox = None

        self.elements: dict[IdT, OsmElementT] = {}
        self.stations: dict[IdT, list[StopArea]] = defaultdict(list)
        self.routes: dict[str, RouteMaster] = {}  # keys are route_master refs
        self.masters: dict[IdT, OsmElementT] = {}  # Route id → master element
        self.stop_areas: [IdT, list[OsmElementT]] = defaultdict(list)
        self.transfers: list[set[StopArea]] = []
        self.station_ids: set[IdT] = set()
        self.stops_and_platforms: set[IdT] = set()
        self.recovery_data = None

    def try_fill_int_attribute(
        self, city_data: dict, attr: str, default: str | None = None
    ) -> None:
        """Try to convert string value to int. Conversion is considered
        to fail if one of the following is true:
        * attr is not empty and data type casting fails;
        * attr is empty and no default value is given.
        In such cases the city is marked as bad by adding an error
        to the city validation log.
        """
        attr_value = city_data[attr]
        if not attr_value and default is not None:
            attr_value = default

        try:
            attr_int = int(attr_value)
        except ValueError:
            print_value = (
                f"{city_data[attr]}" if city_data[attr] else "<empty>"
            )
            self.error(
                f"Configuration error: wrong value for {attr}: {print_value}"
            )
            setattr(self, attr, 0)
        else:
            setattr(self, attr, attr_int)

    @staticmethod
    def log_message(message: str, el: OsmElementT) -> str:
        if el:
            tags = el.get("tags", {})
            message += ' ({} {}, "{}")'.format(
                el["type"],
                el.get("id", el.get("ref")),
                tags.get("name", tags.get("ref", "")),
            )
        return message

    def contains(self, el: OsmElementT) -> bool:
        center = el_center(el)
        if center:
            return (
                self.bbox[0] <= center[1] <= self.bbox[2]
                and self.bbox[1] <= center[0] <= self.bbox[3]
            )
        return False

    def add(self, el: OsmElementT) -> None:
        if el["type"] == "relation" and "members" not in el:
            return

        self.elements[el_id(el)] = el
        if not (el["type"] == "relation" and "tags" in el):
            return

        relation_type = el["tags"].get("type")
        if relation_type == "route_master":
            for m in el["members"]:
                if m["type"] != "relation":
                    continue

                if el_id(m) in self.masters:
                    self.error("Route in two route_masters", m)
                self.masters[el_id(m)] = el

        elif el["tags"].get("public_transport") == "stop_area":
            if relation_type != "public_transport":
                self.warn(
                    "stop_area relation with "
                    f"type={relation_type}, needed type=public_transport",
                    el,
                )
                return

            warned_about_duplicates = False
            for m in el["members"]:
                stop_areas = self.stop_areas[el_id(m)]
                if el in stop_areas and not warned_about_duplicates:
                    self.warn("Duplicate element in a stop area", el)
                    warned_about_duplicates = True
                else:
                    stop_areas.append(el)

    def make_transfer(self, stoparea_group: OsmElementT) -> None:
        transfer: set[StopArea] = set()
        for m in stoparea_group["members"]:
            k = el_id(m)
            el = self.elements.get(k)
            if not el:
                # A stoparea_group member may validly not belong to the city
                # while the stoparea_group does - near the city bbox boundary
                continue
            if "tags" not in el:
                self.warn(
                    "An untagged object {} in a stop_area_group".format(k),
                    stoparea_group,
                )
                continue
            if (
                el["type"] != "relation"
                or el["tags"].get("type") != "public_transport"
                or el["tags"].get("public_transport") != "stop_area"
            ):
                continue
            if k in self.stations:
                stoparea = self.stations[k][0]
                transfer.add(stoparea)
                if stoparea.transfer:
                    # TODO: properly process such cases.
                    # Counterexample 1: Paris,
                    #            Châtelet subway station <->
                    #            "Châtelet - Les Halles" railway station <->
                    #            Les Halles subway station
                    # Counterexample 2: Saint-Petersburg, transfers
                    #             Витебский вокзал <->
                    #             Пушкинская <->
                    #             Звенигородская
                    self.warn(
                        "Stop area {} belongs to multiple interchanges".format(
                            k
                        )
                    )
                stoparea.transfer = el_id(stoparea_group)
        if len(transfer) > 1:
            self.transfers.append(transfer)

    def extract_routes(self) -> None:
        # Extract stations
        processed_stop_areas = set()
        for el in self.elements.values():
            if Station.is_station(el, self.modes):
                # See PR https://github.com/mapsme/subways/pull/98
                if (
                    el["type"] == "relation"
                    and el["tags"].get("type") != "multipolygon"
                ):
                    rel_type = el["tags"].get("type")
                    self.warn(
                        "A railway station cannot be a relation of type "
                        f"{rel_type}",
                        el,
                    )
                    continue
                st = Station(el, self)
                self.station_ids.add(st.id)
                if st.id in self.stop_areas:
                    stations = []
                    for sa in self.stop_areas[st.id]:
                        stations.append(StopArea(st, self, sa))
                else:
                    stations = [StopArea(st, self)]

                for station in stations:
                    if station.id not in processed_stop_areas:
                        processed_stop_areas.add(station.id)
                        for st_el in station.get_elements():
                            self.stations[st_el].append(station)

                        # Check that stops and platforms belong to
                        # a single stop_area
                        for sp in chain(station.stops, station.platforms):
                            if sp in self.stops_and_platforms:
                                self.notice(
                                    f"A stop or a platform {sp} belongs to "
                                    "multiple stop areas, might be correct"
                                )
                            else:
                                self.stops_and_platforms.add(sp)

        # Extract routes
        for el in self.elements.values():
            if Route.is_route(el, self.modes):
                if el["tags"].get("access") in ("no", "private"):
                    continue
                route_id = el_id(el)
                master = self.masters.get(route_id, None)
                if self.networks:
                    network = Route.get_network(el)
                    if master:
                        master_network = Route.get_network(master)
                    else:
                        master_network = None
                    if (
                        network not in self.networks
                        and master_network not in self.networks
                    ):
                        continue

                route = self.route_class(el, self, master)
                if not route.stops:
                    self.warn("Route has no stops", el)
                    continue
                elif len(route.stops) == 1:
                    self.warn("Route has only one stop", el)
                    continue

                k = el_id(master) if master else route.ref
                if k not in self.routes:
                    self.routes[k] = RouteMaster(self, master)
                self.routes[k].add(route)

                # Sometimes adding a route to a newly initialized RouteMaster
                # can fail
                if len(self.routes[k]) == 0:
                    del self.routes[k]

            # And while we're iterating over relations, find interchanges
            if (
                el["type"] == "relation"
                and el.get("tags", {}).get("public_transport", None)
                == "stop_area_group"
            ):
                self.make_transfer(el)

        # Filter transfers, leaving only stations that belong to routes
        own_stopareas = set(self.stopareas())

        self.transfers = [
            inner_transfer
            for inner_transfer in (
                own_stopareas.intersection(transfer)
                for transfer in self.transfers
            )
            if len(inner_transfer) > 1
        ]

    def __iter__(self) -> Iterator[RouteMaster]:
        return iter(self.routes.values())

    def stopareas(self) -> Iterator[StopArea]:
        yielded_stopareas = set()
        for route_master in self:
            for stoparea in route_master.stopareas():
                if stoparea not in yielded_stopareas:
                    yield stoparea
                    yielded_stopareas.add(stoparea)

    @property
    def is_good(self) -> bool:
        if not (self.has_errors or self.validate_called):
            raise RuntimeError(
                "You mustn't refer to City.is_good property before calling "
                "the City.validate() method unless an error already occurred."
            )
        return not self.has_errors

    def get_validation_result(self) -> dict:
        result = {
            "name": self.name,
            "country": self.country,
            "continent": self.continent,
            "stations_found": getattr(self, "found_stations", 0),
            "transfers_found": getattr(self, "found_interchanges", 0),
            "unused_entrances": getattr(self, "unused_entrances", 0),
            "networks": getattr(self, "found_networks", 0),
        }
        if not self.overground:
            result.update(
                {
                    "subwayl_expected": getattr(self, "num_lines", 0),
                    "lightrl_expected": getattr(self, "num_light_lines", 0),
                    "subwayl_found": getattr(self, "found_lines", 0),
                    "lightrl_found": getattr(self, "found_light_lines", 0),
                    "stations_expected": getattr(self, "num_stations", 0),
                    "transfers_expected": getattr(self, "num_interchanges", 0),
                }
            )
        else:
            result.update(
                {
                    "stations_expected": 0,
                    "transfers_expected": 0,
                    "busl_expected": getattr(self, "num_bus_lines", 0),
                    "trolleybusl_expected": getattr(
                        self, "num_trolleybus_lines", 0
                    ),
                    "traml_expected": getattr(self, "num_tram_lines", 0),
                    "otherl_expected": getattr(self, "num_other_lines", 0),
                    "busl_found": getattr(self, "found_bus_lines", 0),
                    "trolleybusl_found": getattr(
                        self, "found_trolleybus_lines", 0
                    ),
                    "traml_found": getattr(self, "found_tram_lines", 0),
                    "otherl_found": getattr(self, "found_other_lines", 0),
                }
            )
        result["warnings"] = self.warnings
        result["errors"] = self.errors
        result["notices"] = self.notices
        return result

    def count_unused_entrances(self) -> None:
        global used_entrances
        stop_areas = set()
        for el in self.elements.values():
            if (
                el["type"] == "relation"
                and "tags" in el
                and el["tags"].get("public_transport") == "stop_area"
                and "members" in el
            ):
                stop_areas.update([el_id(m) for m in el["members"]])
        unused = []
        not_in_sa = []
        for el in self.elements.values():
            if (
                el["type"] == "node"
                and "tags" in el
                and el["tags"].get("railway") == "subway_entrance"
            ):
                i = el_id(el)
                if i in self.stations:
                    used_entrances.add(i)
                if i not in stop_areas:
                    not_in_sa.append(i)
                    if i not in self.stations:
                        unused.append(i)
        self.unused_entrances = len(unused)
        self.entrances_not_in_stop_areas = len(not_in_sa)
        if unused:
            self.notice(
                f"{len(unused)} subway entrances are not connected to a "
                f"station: {format_elid_list(unused)}"
            )
        if not_in_sa:
            self.notice(
                f"{len(not_in_sa)} subway entrances are not in stop_area "
                f"relations: {format_elid_list(not_in_sa)}"
            )

    def validate_lines(self) -> None:
        self.found_light_lines = len(
            [x for x in self.routes.values() if x.mode != "subway"]
        )
        self.found_lines = len(self.routes) - self.found_light_lines
        if self.found_lines != self.num_lines:
            self.error(
                "Found {} subway lines, expected {}".format(
                    self.found_lines, self.num_lines
                )
            )
        if self.found_light_lines != self.num_light_lines:
            self.error(
                "Found {} light rail lines, expected {}".format(
                    self.found_light_lines, self.num_light_lines
                )
            )

    def validate_overground_lines(self) -> None:
        self.found_tram_lines = len(
            [x for x in self.routes.values() if x.mode == "tram"]
        )
        self.found_bus_lines = len(
            [x for x in self.routes.values() if x.mode == "bus"]
        )
        self.found_trolleybus_lines = len(
            [x for x in self.routes.values() if x.mode == "trolleybus"]
        )
        self.found_other_lines = len(
            [
                x
                for x in self.routes.values()
                if x.mode not in ("bus", "trolleybus", "tram")
            ]
        )
        if self.found_tram_lines != self.num_tram_lines:
            log_function = (
                self.error if self.found_tram_lines == 0 else self.notice
            )
            log_function(
                "Found {} tram lines, expected {}".format(
                    self.found_tram_lines, self.num_tram_lines
                ),
            )

    def validate(self) -> None:
        networks = Counter()
        self.found_stations = 0
        unused_stations = set(self.station_ids)
        for rmaster in self.routes.values():
            networks[str(rmaster.network)] += 1
            if not self.overground:
                rmaster.check_return_routes()
            route_stations = set()
            for sa in rmaster.stopareas():
                route_stations.add(sa.transfer or sa.id)
                unused_stations.discard(sa.station.id)
            self.found_stations += len(route_stations)
        if unused_stations:
            self.unused_stations = len(unused_stations)
            self.notice(
                "{} unused stations: {}".format(
                    self.unused_stations, format_elid_list(unused_stations)
                )
            )
        self.count_unused_entrances()
        self.found_interchanges = len(self.transfers)

        if self.overground:
            self.validate_overground_lines()
        else:
            self.validate_lines()

            if self.found_stations != self.num_stations:
                msg = "Found {} stations in routes, expected {}".format(
                    self.found_stations, self.num_stations
                )
                log_function = (
                    self.error
                    if self.num_stations > 0
                    and not (
                        0
                        <= (self.num_stations - self.found_stations)
                        / self.num_stations
                        <= ALLOWED_STATIONS_MISMATCH
                    )
                    else self.warn
                )
                log_function(msg)

            if self.found_interchanges != self.num_interchanges:
                msg = "Found {} interchanges, expected {}".format(
                    self.found_interchanges, self.num_interchanges
                )
                log_function = (
                    self.error
                    if self.num_interchanges != 0
                    and not (
                        (self.num_interchanges - self.found_interchanges)
                        / self.num_interchanges
                        <= ALLOWED_TRANSFERS_MISMATCH
                    )
                    else self.warn
                )
                log_function(msg)

        self.found_networks = len(networks)
        if len(networks) > max(1, len(self.networks)):
            n_str = "; ".join(
                ["{} ({})".format(k, v) for k, v in networks.items()]
            )
            self.notice("More than one network: {}".format(n_str))

        self.validate_called = True

    def calculate_distances(self) -> None:
        for route_master in self:
            for route in route_master:
                route.calculate_distances()


def find_transfers(
    elements: list[OsmElementT], cities: Collection[City]
) -> TransfersT:
    """As for now, two Cities may contain the same stoparea, but those
    StopArea instances would have different python id. So we don't store
    references to StopAreas, but only their ids. This is important at
    inter-city interchanges.
    """
    stop_area_groups = [
        el
        for el in elements
        if el["type"] == "relation"
        and "members" in el
        and el.get("tags", {}).get("public_transport") == "stop_area_group"
    ]

    stopareas_in_cities_ids = set(
        stoparea.id
        for city in cities
        if city.is_good
        for stoparea in city.stopareas()
    )

    transfers = []
    for stop_area_group in stop_area_groups:
        transfer: TransferT = set(
            member_id
            for member_id in (
                el_id(member) for member in stop_area_group["members"]
            )
            if member_id in stopareas_in_cities_ids
        )
        if len(transfer) > 1:
            transfers.append(transfer)
    return transfers


def get_unused_subway_entrances_geojson(elements: list[OsmElementT]) -> dict:
    global used_entrances
    features = []
    for el in elements:
        if (
            el["type"] == "node"
            and "tags" in el
            and el["tags"].get("railway") == "subway_entrance"
        ):
            if el_id(el) not in used_entrances:
                geometry = {"type": "Point", "coordinates": el_center(el)}
                properties = {
                    k: v
                    for k, v in el["tags"].items()
                    if k not in ("railway", "entrance")
                }
                features.append(
                    {
                        "type": "Feature",
                        "geometry": geometry,
                        "properties": properties,
                    }
                )
    return {"type": "FeatureCollection", "features": features}
