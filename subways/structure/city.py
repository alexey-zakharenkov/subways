from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Collection, Iterator
from itertools import chain

from subways.consts import (
    DEFAULT_MODES_OVERGROUND,
    DEFAULT_MODES_RAPID,
)
from subways.osm_element import el_center, el_id, get_network
from subways.structure.route import Route
from subways.structure.route_master import RouteMaster
from subways.structure.station import Station
from subways.structure.stop_area import StopArea
from subways.types import (
    IdT,
    OsmElementT,
    TransfersT,
    TransferT,
)

ALLOWED_STATIONS_MISMATCH = 0.02  # part of total station count
ALLOWED_TRANSFERS_MISMATCH = 0.07  # part of total interchanges count

used_entrances = set()


def format_elid_list(ids: Collection[IdT]) -> str:
    msg = ", ".join(sorted(ids)[:20])
    if len(ids) > 20:
        msg += ", ..."
    return msg


class City:
    route_class = Route

    def __init__(self, city_data: dict, overground: bool = False) -> None:
        self.validate_called = False
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notices: list[str] = []
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

    def notice(self, message: str, el: OsmElementT | None = None) -> None:
        """This type of message may point to a potential problem."""
        msg = City.log_message(message, el)
        self.notices.append(msg)

    def warn(self, message: str, el: OsmElementT | None = None) -> None:
        """A warning is definitely a problem but is doesn't prevent
        from building a routing file and doesn't invalidate the city.
        """
        msg = City.log_message(message, el)
        self.warnings.append(msg)

    def error(self, message: str, el: OsmElementT | None = None) -> None:
        """Error is a critical problem that invalidates the city."""
        msg = City.log_message(message, el)
        self.errors.append(msg)

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
                master_element = self.masters.get(route_id, None)
                if self.networks:
                    network = get_network(el)
                    if master_element:
                        master_network = get_network(master_element)
                    else:
                        master_network = None
                    if (
                        network not in self.networks
                        and master_network not in self.networks
                    ):
                        continue

                route = self.route_class(el, self, master_element)
                if not route.stops:
                    self.warn("Route has no stops", el)
                    continue
                elif len(route.stops) == 1:
                    self.warn("Route has only one stop", el)
                    continue

                master_id = el_id(master_element) or route.ref
                route_master = self.routes.setdefault(
                    master_id, RouteMaster(self, master_element)
                )
                route_master.add(route)

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
        if not (self.errors or self.validate_called):
            raise RuntimeError(
                "You mustn't refer to City.is_good property before calling "
                "the City.validate() method unless an error already occurred."
            )
        return len(self.errors) == 0

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
