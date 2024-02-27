import json
import logging
import os
from collections import defaultdict
from collections.abc import Callable
from typing import Any, TypeAlias

from subway_structure import (
    City,
    DISPLACEMENT_TOLERANCE,
    distance,
    el_center,
    IdT,
    LonLat,
    OsmElementT,
    Station,
    StopArea,
    TransfersT,
)
from ._common import (
    DEFAULT_INTERVAL,
    format_colour,
    KMPH_TO_MPS,
    SPEED_ON_TRANSFER,
    TRANSFER_PENALTY,
)

OSM_TYPES = {"n": (0, "node"), "w": (2, "way"), "r": (3, "relation")}
ENTRANCE_PENALTY = 60  # seconds
SPEED_TO_ENTRANCE = 5 * KMPH_TO_MPS  # m/s
SPEED_ON_LINE = 40 * KMPH_TO_MPS  # m/s

# (stoparea1_uid, stoparea2_uid) -> seconds; stoparea1_uid < stoparea2_uid
TransferTimesT: TypeAlias = dict[tuple[int, int], int]


def uid(elid: IdT, typ: str | None = None) -> int:
    t = elid[0]
    osm_id = int(elid[1:])
    if not typ:
        osm_id = (osm_id << 2) + OSM_TYPES[t][0]
    elif typ != t:
        raise Exception("Got {}, expected {}".format(elid, typ))
    return osm_id << 1


class DummyCache:
    """This class may be used when you need to omit all cache processing"""

    def __init__(self, cache_path: str, cities: list[City]) -> None:
        pass

    def __getattr__(self, name: str) -> Callable[..., None]:
        """This results in that a call to any method effectively does nothing
        and does not generate exceptions."""

        def method(*args, **kwargs) -> None:
            return None

        return method


def if_object_is_used(method: Callable) -> Callable:
    """Decorator to skip method execution under certain condition.
    Relies on "is_used" object property."""

    def inner(self, *args, **kwargs) -> Any:
        if not self.is_used:
            return
        return method(self, *args, **kwargs)

    return inner


class MapsmeCache:
    def __init__(self, cache_path: str, cities: list[City]) -> None:
        if not cache_path:
            # Cache is not used,
            # all actions with cache must be silently skipped
            self.is_used = False
            return
        self.cache_path = cache_path
        self.is_used = True
        self.cache = {}
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
            except json.decoder.JSONDecodeError:
                logging.warning(
                    "City cache '%s' is not a valid json file. "
                    "Building cache from scratch.",
                    cache_path,
                )
        self.recovered_city_names = set()
        # One stoparea may participate in routes of different cities
        self.stop_cities = defaultdict(set)  # stoparea id -> city names
        self.city_dict = {c.name: c for c in cities}
        self.good_city_names = {c.name for c in cities if c.is_good}

    def _is_cached_city_usable(self, city: City) -> bool:
        """Check if cached stations still exist in osm data and
        not moved far away.
        """
        city_cache_data = self.cache[city.name]
        for stoparea_id, cached_stoparea in city_cache_data["stops"].items():
            station_id = cached_stoparea["osm_type"][0] + str(
                cached_stoparea["osm_id"]
            )
            city_station = city.elements.get(station_id)
            if not city_station or not Station.is_station(
                city_station, city.modes
            ):
                return False
            station_coords = el_center(city_station)
            cached_station_coords = (
                cached_stoparea["lon"],
                cached_stoparea["lat"],
            )
            displacement = distance(station_coords, cached_station_coords)
            if displacement > DISPLACEMENT_TOLERANCE:
                return False

        return True

    @if_object_is_used
    def provide_stops_and_networks(
        self, stops: dict, networks: list[dict]
    ) -> None:
        """Put stops and networks for bad cities into containers
        passed as arguments."""
        for city in self.city_dict.values():
            if not city.is_good and city.name in self.cache:
                city_cached_data = self.cache[city.name]
                if self._is_cached_city_usable(city):
                    stops.update(city_cached_data["stops"])
                    networks.append(city_cached_data["network"])
                    logging.info("Taking %s from cache", city.name)
                    self.recovered_city_names.add(city.name)

    @if_object_is_used
    def provide_transfers(self, transfers: TransferTimesT) -> None:
        """Add transfers from usable cached cities to 'transfers' dict
        passed as argument."""
        for city_name in self.recovered_city_names:
            city_cached_transfers = self.cache[city_name]["transfers"]
            for stop1_uid, stop2_uid, transfer_time in city_cached_transfers:
                if (stop1_uid, stop2_uid) not in transfers:
                    transfers[(stop1_uid, stop2_uid)] = transfer_time

    @if_object_is_used
    def initialize_good_city(self, city_name: str, network: dict) -> None:
        """Create/replace one cache element with new data container.
        This should be done for each good city."""
        self.cache[city_name] = {
            "network": network,
            "stops": {},  # stoparea el_id -> jsonified stop data
            "transfers": [],  # list of tuples
            # (stoparea1_uid, stoparea2_uid, time); uid1 < uid2
        }

    @if_object_is_used
    def link_stop_with_city(self, stoparea_id: IdT, city_name: str) -> None:
        """Remember that some stop_area is used in a city."""
        stoparea_uid = uid(stoparea_id)
        self.stop_cities[stoparea_uid].add(city_name)

    @if_object_is_used
    def add_stop(self, stoparea_id: IdT, st: dict) -> None:
        """Add stoparea to the cache of each city the stoparea is in."""
        stoparea_uid = uid(stoparea_id)
        for city_name in self.stop_cities[stoparea_uid]:
            self.cache[city_name]["stops"][stoparea_id] = st

    @if_object_is_used
    def add_transfer(
        self, stoparea1_uid: int, stoparea2_uid: int, transfer_time: int
    ) -> None:
        """If a transfer is inside a good city, add it to the city's cache."""
        for city_name in (
            self.good_city_names
            & self.stop_cities[stoparea1_uid]
            & self.stop_cities[stoparea2_uid]
        ):
            self.cache[city_name]["transfers"].append(
                (stoparea1_uid, stoparea2_uid, transfer_time)
            )

    @if_object_is_used
    def save(self) -> None:
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False)
        except Exception as e:
            logging.warning("Failed to save cache: %s", str(e))


def transit_data_to_mapsme(
    cities: list[City], transfers: TransfersT, cache_path: str | None
) -> dict:
    """Generate all output and save to file.
    :param cities: List of City instances
    :param transfers: List of sets of StopArea.id
    :param cache_path: Path to json-file with good cities cache or None.
    """

    def find_exits_for_platform(
        center: LonLat, nodes: list[OsmElementT]
    ) -> list[OsmElementT]:
        exits = []
        min_distance = None
        for n in nodes:
            d = distance(center, (n["lon"], n["lat"]))
            if not min_distance:
                min_distance = d * 2 / 3
            elif d < min_distance:
                continue
            too_close = False
            for e in exits:
                d = distance((e["lon"], e["lat"]), (n["lon"], n["lat"]))
                if d < min_distance:
                    too_close = True
                    break
            if not too_close:
                exits.append(n)
        return exits

    cache = MapsmeCache(cache_path, cities)

    stop_areas: dict[IdT, StopArea] = {}
    stops: dict[IdT, dict] = {}  # stoparea el_id -> stop jsonified data
    networks = []
    good_cities = [c for c in cities if c.is_good]
    platform_nodes = {}
    cache.provide_stops_and_networks(stops, networks)

    for city in good_cities:
        network = {"network": city.name, "routes": [], "agency_id": city.id}
        cache.initialize_good_city(city.name, network)
        for route in city:
            routes = {
                "type": route.mode,
                "ref": route.ref,
                "name": route.name,
                "colour": format_colour(route.colour),
                "route_id": uid(route.id, "r"),
                "itineraries": [],
            }
            if route.infill:
                routes["casing"] = routes["colour"]
                routes["colour"] = format_colour(route.infill)
            for i, variant in enumerate(route):
                itin = []
                for stop in variant:
                    stop_areas[stop.stoparea.id] = stop.stoparea
                    cache.link_stop_with_city(stop.stoparea.id, city.name)
                    itin.append(
                        [
                            uid(stop.stoparea.id),
                            round(stop.distance / SPEED_ON_LINE),
                        ]
                    )
                    # Make exits from platform nodes,
                    # if we don't have proper exits
                    if (
                        len(stop.stoparea.entrances) + len(stop.stoparea.exits)
                        == 0
                    ):
                        for pl in stop.stoparea.platforms:
                            pl_el = city.elements[pl]
                            if pl_el["type"] == "node":
                                pl_nodes = [pl_el]
                            elif pl_el["type"] == "way":
                                pl_nodes = [
                                    city.elements.get("n{}".format(n))
                                    for n in pl_el["nodes"]
                                ]
                            else:
                                pl_nodes = []
                                for m in pl_el["members"]:
                                    if m["type"] == "way":
                                        if (
                                            "{}{}".format(
                                                m["type"][0], m["ref"]
                                            )
                                            in city.elements
                                        ):
                                            pl_nodes.extend(
                                                [
                                                    city.elements.get(
                                                        "n{}".format(n)
                                                    )
                                                    for n in city.elements[
                                                        "{}{}".format(
                                                            m["type"][0],
                                                            m["ref"],
                                                        )
                                                    ]["nodes"]
                                                ]
                                            )
                            pl_nodes = [n for n in pl_nodes if n]
                            platform_nodes[pl] = find_exits_for_platform(
                                stop.stoparea.centers[pl], pl_nodes
                            )

                routes["itineraries"].append(
                    {
                        "stops": itin,
                        "interval": round(
                            variant.interval or DEFAULT_INTERVAL
                        ),
                    }
                )
            network["routes"].append(routes)
        networks.append(network)

    for stop_id, stop in stop_areas.items():
        st = {
            "name": stop.name,
            "int_name": stop.int_name,
            "lat": stop.center[1],
            "lon": stop.center[0],
            "osm_type": OSM_TYPES[stop.station.id[0]][1],
            "osm_id": int(stop.station.id[1:]),
            "id": uid(stop.id),
            "entrances": [],
            "exits": [],
        }
        for e_l, k in ((stop.entrances, "entrances"), (stop.exits, "exits")):
            for e in e_l:
                if e[0] == "n":
                    st[k].append(
                        {
                            "osm_type": "node",
                            "osm_id": int(e[1:]),
                            "lon": stop.centers[e][0],
                            "lat": stop.centers[e][1],
                            "distance": ENTRANCE_PENALTY
                            + round(
                                distance(stop.centers[e], stop.center)
                                / SPEED_TO_ENTRANCE
                            ),
                        }
                    )
        if len(stop.entrances) + len(stop.exits) == 0:
            if stop.platforms:
                for pl in stop.platforms:
                    for n in platform_nodes[pl]:
                        for k in ("entrances", "exits"):
                            st[k].append(
                                {
                                    "osm_type": n["type"],
                                    "osm_id": n["id"],
                                    "lon": n["lon"],
                                    "lat": n["lat"],
                                    "distance": ENTRANCE_PENALTY
                                    + round(
                                        distance(
                                            (n["lon"], n["lat"]), stop.center
                                        )
                                        / SPEED_TO_ENTRANCE
                                    ),
                                }
                            )
            else:
                for k in ("entrances", "exits"):
                    st[k].append(
                        {
                            "osm_type": OSM_TYPES[stop.station.id[0]][1],
                            "osm_id": int(stop.station.id[1:]),
                            "lon": stop.centers[stop.id][0],
                            "lat": stop.centers[stop.id][1],
                            "distance": 60,
                        }
                    )

        stops[stop_id] = st
        cache.add_stop(stop_id, st)

    pairwise_transfers: TransferTimesT = {}
    for stoparea_id_set in transfers:
        stoparea_ids = list(stoparea_id_set)
        for i_first in range(len(stoparea_ids) - 1):
            for i_second in range(i_first + 1, len(stoparea_ids)):
                stoparea1_id = stoparea_ids[i_first]
                stoparea2_id = stoparea_ids[i_second]
                if stoparea1_id in stops and stoparea2_id in stops:
                    uid1 = uid(stoparea1_id)
                    uid2 = uid(stoparea2_id)
                    uid1, uid2 = sorted([uid1, uid2])
                    transfer_time = TRANSFER_PENALTY + round(
                        distance(
                            stop_areas[stoparea1_id].center,
                            stop_areas[stoparea2_id].center,
                        )
                        / SPEED_ON_TRANSFER
                    )
                    pairwise_transfers[(uid1, uid2)] = transfer_time
                    cache.add_transfer(uid1, uid2, transfer_time)

    cache.provide_transfers(pairwise_transfers)
    cache.save()

    pairwise_transfers_list = [
        (stop1_uid, stop2_uid, transfer_time)
        for (stop1_uid, stop2_uid), transfer_time in pairwise_transfers.items()
    ]

    result = {
        "stops": list(stops.values()),
        "transfers": pairwise_transfers_list,
        "networks": networks,
    }
    return result


def process(
    cities: list[City],
    transfers: TransfersT,
    filename: str,
    cache_path: str | None,
) -> None:
    """Generate all output and save to file.
    :param cities: list of City instances
    :param transfers: all collected transfers in the world
    :param filename: Path to file to save the result
    :param cache_path: Path to json-file with good cities cache or None.
    """
    if not filename.lower().endswith("json"):
        filename = f"{filename}.json"

    mapsme_transit = transit_data_to_mapsme(cities, transfers, cache_path)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            mapsme_transit,
            f,
            indent=1,
            ensure_ascii=False,
        )
