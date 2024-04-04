from __future__ import annotations

import typing
from collections.abc import Iterator
from typing import TypeVar

from subways.consts import MAX_DISTANCE_STOP_TO_LINE
from subways.css_colours import normalize_colour
from subways.geom_utils import distance, project_on_line
from subways.osm_element import el_id, get_network
from subways.structure.route import get_route_duration, get_route_interval
from subways.structure.stop_area import StopArea
from subways.types import IdT, OsmElementT

if typing.TYPE_CHECKING:
    from subways.structure.city import City
    from subways.structure.route_stop import RouteStop


SUGGEST_TRANSFER_MIN_DISTANCE = 100  # in meters

T = TypeVar("T")


class RouteMaster:
    def __init__(self, city: City, master: OsmElementT = None) -> None:
        self.city = city
        self.routes = []
        self.best: Route = None  # noqa: F821
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
            self.network = get_network(master)
            self.mode = master["tags"].get(
                "route_master", None
            )  # This tag is required, but okay
            self.name = master["tags"].get("name", None)
            self.interval = get_route_interval(master["tags"])
            self.interval_from_master = self.interval is not None
            self.duration = get_route_duration(master["tags"])
        else:
            self.ref = None
            self.colour = None
            self.infill = None
            self.network = None
            self.mode = None
            self.name = None
            self.interval = None
            self.duration = None

    def stopareas(self) -> Iterator[StopArea]:
        yielded_stopareas = set()
        for route in self:
            for stoparea in route.stopareas():
                if stoparea not in yielded_stopareas:
                    yield stoparea
                    yielded_stopareas.add(stoparea)

    def add(self, route: Route) -> None:  # noqa: F821
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

    def get_meaningful_routes(self) -> list[Route]:  # noqa: F821
        return [route for route in self if len(route) >= 2]

    def find_twin_routes(self) -> dict[Route, Route]:  # noqa: F821
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

    def alert_twin_routes_differ(
        self,
        route1: Route,  # noqa: F821
        route2: Route,  # noqa: F821
    ) -> None:
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
    def calculate_twin_routes_diff(
        route1: Route,  # noqa: F821
        route2: Route,  # noqa: F821
    ) -> tuple:
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

    def __getitem__(self, i) -> Route:  # noqa: F821
        return self.routes[i]

    def __iter__(self) -> Iterator[Route]:  # noqa: F821
        return iter(self.routes)

    def __repr__(self) -> str:
        return (
            f"RouteMaster(id={self.id}, mode={self.mode}, ref={self.ref}, "
            f"name={self.name}, network={self.network}, "
            f"num_variants={len(self.routes)}"
        )
