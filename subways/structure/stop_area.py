from __future__ import annotations

import typing
from itertools import chain

from subways.consts import RAILWAY_TYPES
from subways.css_colours import normalize_colour
from subways.geom_utils import distance
from subways.osm_element import el_id, el_center
from subways.structure.station import Station
from subways.types import IdT, OsmElementT

if typing.TYPE_CHECKING:
    from subways.structure.city import City

MAX_DISTANCE_TO_ENTRANCES = 300  # in meters


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
