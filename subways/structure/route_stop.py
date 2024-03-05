from __future__ import annotations

import typing

from subways.osm_element import el_center, el_id
from subways.structure.station import Station
from subways.structure.stop_area import StopArea
from subways.types import LonLat, OsmElementT

if typing.TYPE_CHECKING:
    from subways.structure.city import City


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
