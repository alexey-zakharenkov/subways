from __future__ import annotations

import re
import typing
from collections.abc import Callable, Collection, Iterator
from itertools import islice

from subways.consts import (
    CONSTRUCTION_KEYS,
    DISPLACEMENT_TOLERANCE,
    MAX_DISTANCE_STOP_TO_LINE,
)
from subways.css_colours import normalize_colour
from subways.geom_utils import (
    angle_between,
    distance,
    distance_on_line,
    find_segment,
    project_on_line,
)
from subways.osm_element import el_id, el_center, get_network
from subways.structure.route_stop import RouteStop
from subways.structure.station import Station
from subways.structure.stop_area import StopArea
from subways.types import CriticalValidationError, IdT, OsmElementT, RailT

if typing.TYPE_CHECKING:
    from subways.structure.city import City

START_END_TIMES_RE = re.compile(r".*?(\d{2}):(\d{2})-(\d{2}):(\d{2}).*")

ALLOWED_ANGLE_BETWEEN_STOPS = 45  # in degrees
DISALLOWED_ANGLE_BETWEEN_STOPS = 20  # in degrees


def parse_time_range(
    opening_hours: str,
) -> tuple[tuple[int, int], tuple[int, int]] | None:
    """Very simplified method to parse OSM opening_hours tag.
    We simply take the first HH:MM-HH:MM substring which is the most probable
    opening hours interval for the most of the weekdays.
    """
    if opening_hours == "24/7":
        return (0, 0), (24, 0)

    m = START_END_TIMES_RE.match(opening_hours)
    if not m:
        return None
    ints = tuple(map(int, m.groups()))
    if ints[1] > 59 or ints[3] > 59:
        return None
    start_time = (ints[0], ints[1])
    end_time = (ints[2], ints[3])
    return start_time, end_time


def osm_interval_to_seconds(interval_str: str) -> int | None:
    """Convert to int an OSM value for 'interval'/'headway'/'duration' tag
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

    if seconds < 0 or minutes < 0 or hours < 0:
        return None
    if semicolon_count > 0 and (seconds >= 60 or minutes >= 60):
        return None

    interval = seconds + 60 * minutes + 60 * 60 * hours
    if interval == 0:
        return None
    return interval


def get_interval_in_seconds_from_tags(
    tags: dict, keys: str | Collection[str]
) -> int | None:
    """Extract time interval value from tags for keys among "keys".
    E.g., "interval" and "headway" means the same in OSM.
    Examples:
        interval=5                => 300
        headway:peak=00:01:30     => 90
    """
    if isinstance(keys, str):
        keys = (keys,)

    value = None
    for key in keys:
        if key in tags:
            value = tags[key]
            break
    if value is None:
        for key in keys:
            if value:
                break
            for tag_name in tags:
                if tag_name.startswith(key + ":"):
                    value = tags[tag_name]
                    break
    if not value:
        return None
    return osm_interval_to_seconds(value)


def get_route_interval(tags: dict) -> int | None:
    return get_interval_in_seconds_from_tags(tags, ("interval", "headway"))


def get_route_duration(tags: dict) -> int | None:
    return get_interval_in_seconds_from_tags(tags, "duration")


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
        self.duration = None
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
        tags = relation["tags"]
        master_tags = {} if not master else master["tags"]
        if "ref" not in tags and "ref" not in master_tags:
            self.city.notice("Missing ref on a route", relation)
        self.ref = tags.get(
            "ref", master_tags.get("ref", tags.get("name", None))
        )
        self.name = tags.get("name", None)
        self.mode = tags["route"]
        if (
            "colour" not in tags
            and "colour" not in master_tags
            and self.mode != "tram"
        ):
            self.city.notice("Missing colour on a route", relation)
        try:
            self.colour = normalize_colour(
                tags.get("colour", master_tags.get("colour", None))
            )
        except ValueError as e:
            self.colour = None
            self.city.warn(str(e), relation)
        try:
            self.infill = normalize_colour(
                tags.get(
                    "colour:infill", master_tags.get("colour:infill", None)
                )
            )
        except ValueError as e:
            self.infill = None
            self.city.warn(str(e), relation)
        self.network = get_network(relation)
        self.interval = get_route_interval(tags) or get_route_interval(
            master_tags
        )
        self.duration = get_route_duration(tags) or get_route_duration(
            master_tags
        )
        parsed_time_range = parse_time_range(
            tags.get("opening_hours", master_tags.get("opening_hours", ""))
        )
        if parsed_time_range:
            self.start_time, self.end_time = parsed_time_range

        if tags.get("public_transport:version") == "1":
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
