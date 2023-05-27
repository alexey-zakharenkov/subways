#!/usr/bin/env python3
import argparse
import csv
import inspect
import json
import logging
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from functools import partial

import processors
from subway_io import (
    dump_yaml,
    load_xml,
    make_geojson,
    read_recovery_data,
    write_recovery_data,
)
from subway_structure import (
    City,
    CriticalValidationError,
    find_transfers,
    get_unused_entrances_geojson,
    MODES_OVERGROUND,
    MODES_RAPID,
)

DEFAULT_SPREADSHEET_ID = "1SEW1-NiNOnA2qDwievcxYV1FOaQl1mb1fdeyqAxHu3k"
DEFAULT_CITIES_INFO_URL = (
    "https://docs.google.com/spreadsheets/d/"
    f"{DEFAULT_SPREADSHEET_ID}/export?format=csv"
)

Point = tuple[float, float]


def overpass_request(
    overground: bool, overpass_api: str, bboxes: list[list[float]]
) -> list[dict]:
    query = "[out:json][timeout:1000];("
    modes = MODES_OVERGROUND if overground else MODES_RAPID
    for bbox in bboxes:
        bbox_part = "({})".format(",".join(str(coord) for coord in bbox))
        query += "("
        for mode in modes:
            query += 'rel[route="{}"]{};'.format(mode, bbox_part)
        query += ");"
        query += "rel(br)[type=route_master];"
        if not overground:
            query += "node[railway=subway_entrance]{};".format(bbox_part)
        query += "rel[public_transport=stop_area]{};".format(bbox_part)
        query += (
            "rel(br)[type=public_transport][public_transport=stop_area_group];"
        )
    query += ");(._;>>;);out body center qt;"
    logging.debug("Query: %s", query)
    url = "{}?data={}".format(overpass_api, urllib.parse.quote(query))
    response = urllib.request.urlopen(url, timeout=1000)
    if (r_code := response.getcode()) != 200:
        raise Exception(f"Failed to query Overpass API: HTTP {r_code}")
    return json.load(response)["elements"]


def multi_overpass(
    overground: bool, overpass_api: str, bboxes: list[list[float]]
) -> list[dict]:
    SLICE_SIZE = 10
    INTERREQUEST_WAIT = 5  # in seconds
    result = []
    for i in range(0, len(bboxes) + SLICE_SIZE - 1, SLICE_SIZE):
        if i > 0:
            time.sleep(INTERREQUEST_WAIT)
        bboxes_i = bboxes[i : i + SLICE_SIZE]  # noqa E203
        result.extend(overpass_request(overground, overpass_api, bboxes_i))
    return result


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", "", name.lower().replace(" ", "_"))


def get_way_center(
    element: dict, node_centers: dict[int, Point]
) -> Point | None:
    """
    :param element: dict describing OSM element
    :param node_centers: osm_id => (lat, lon)
    :return: tuple with center coordinates, or None
    """

    # If elements have been queried via overpass-api with
    # 'out center;' clause then ways already have 'center' attribute
    if "center" in element:
        return element["center"]["lat"], element["center"]["lon"]

    if "nodes" not in element:
        return None

    center = [0, 0]
    count = 0
    way_nodes = element["nodes"]
    way_nodes_len = len(element["nodes"])
    for i, nd in enumerate(way_nodes):
        if nd not in node_centers:
            continue
        # Don't count the first node of a closed way twice
        if (
            i == way_nodes_len - 1
            and way_nodes_len > 1
            and way_nodes[0] == way_nodes[-1]
        ):
            break
        center[0] += node_centers[nd][0]
        center[1] += node_centers[nd][1]
        count += 1
    if count == 0:
        return None
    element["center"] = {"lat": center[0] / count, "lon": center[1] / count}
    return element["center"]["lat"], element["center"]["lon"]


def get_relation_center(
    element: dict,
    node_centers: dict[int, Point],
    way_centers: dict[int, Point],
    relation_centers: dict[int, Point],
    ignore_unlocalized_child_relations: bool = False,
) -> Point | None:
    """
    :param element: dict describing OSM element
    :param node_centers: osm_id => (lat, lon)
    :param way_centers: osm_id => (lat, lon)
    :param relation_centers: osm_id => (lat, lon)
    :param ignore_unlocalized_child_relations: if a member that is a relation
        has no center, skip it and calculate center based on member nodes,
        ways and other, "localized" (with known centers), relations
    :return: tuple with center coordinates, or None
    """

    # If elements have been queried via overpass-api with
    # 'out center;' clause then some relations already have 'center'
    # attribute. But this is not the case for relations composed only
    # of other relations (e.g., route_master, stop_area_group or
    # stop_area with only members that are multipolygons)
    if "center" in element:
        return element["center"]["lat"], element["center"]["lon"]

    center = [0, 0]
    count = 0
    for m in element.get("members", list()):
        m_id = m["ref"]
        m_type = m["type"]
        if m_type == "relation" and m_id not in relation_centers:
            if ignore_unlocalized_child_relations:
                continue
            else:
                # Cannot calculate fair center because the center
                # of a child relation is not known yet
                return None
        member_container = (
            node_centers
            if m_type == "node"
            else way_centers
            if m_type == "way"
            else relation_centers
        )
        if m_id in member_container:
            center[0] += member_container[m_id][0]
            center[1] += member_container[m_id][1]
            count += 1
    if count == 0:
        return None
    element["center"] = {"lat": center[0] / count, "lon": center[1] / count}
    return element["center"]["lat"], element["center"]["lon"]


def calculate_centers(elements: list[dict]) -> None:
    """Adds 'center' key to each way/relation in elements,
    except for empty ways or relations.
    Relies on nodes-ways-relations order in the elements list.
    """
    nodes: dict[int, Point] = {}  # id => (lat, lon)
    ways: dict[int, Point] = {}  # id => (lat, lon)
    relations: dict[int, Point] = {}  # id => (lat, lon)

    unlocalized_relations = []  # 'unlocalized' means the center of the
    # relation has not been calculated yet

    for el in elements:
        if el["type"] == "node":
            nodes[el["id"]] = (el["lat"], el["lon"])
        elif el["type"] == "way":
            if center := get_way_center(el, nodes):
                ways[el["id"]] = center
        elif el["type"] == "relation":
            if center := get_relation_center(el, nodes, ways, relations):
                relations[el["id"]] = center
            else:
                unlocalized_relations.append(el)

    def iterate_relation_centers_calculation(
        ignore_unlocalized_child_relations: bool,
    ) -> list[dict]:
        unlocalized_relations_upd = []
        for rel in unlocalized_relations:
            if center := get_relation_center(
                rel, nodes, ways, relations, ignore_unlocalized_child_relations
            ):
                relations[rel["id"]] = center
            else:
                unlocalized_relations_upd.append(rel)
        return unlocalized_relations_upd

    # Calculate centers for relations that have no one yet
    while unlocalized_relations:
        unlocalized_relations_upd = iterate_relation_centers_calculation(False)
        progress = len(unlocalized_relations_upd) < len(unlocalized_relations)
        if not progress:
            unlocalized_relations_upd = iterate_relation_centers_calculation(
                True
            )
            progress = len(unlocalized_relations_upd) < len(
                unlocalized_relations
            )
            if not progress:
                break
        unlocalized_relations = unlocalized_relations_upd


def add_osm_elements_to_cities(
    osm_elements: list[dict], cities: list[City]
) -> None:
    for el in osm_elements:
        for c in cities:
            if c.contains(el):
                c.add(el)


def validate_cities(cities: list[City]) -> list[City]:
    """Validate cities. Return list of good cities."""
    good_cities = []
    for c in cities:
        try:
            c.extract_routes()
        except CriticalValidationError as e:
            logging.error(
                "Critical validation error while processing %s: %s",
                c.name,
                e,
            )
            c.error(str(e))
        except AssertionError as e:
            logging.error(
                "Validation logic error while processing %s: %s",
                c.name,
                e,
            )
            c.error(f"Validation logic error: {e}")
        else:
            c.validate()
            if c.is_good:
                c.calculate_distances()
                good_cities.append(c)

    return good_cities


def get_cities_info(
    cities_info_url: str = DEFAULT_CITIES_INFO_URL,
) -> list[dict]:
    response = urllib.request.urlopen(cities_info_url)
    if (
        not cities_info_url.startswith("file://")
        and (r_code := response.getcode()) != 200
    ):
        raise Exception(
            f"Failed to download cities spreadsheet: HTTP {r_code}"
        )
    data = response.read().decode("utf-8")
    reader = csv.DictReader(
        data.splitlines(),
        fieldnames=(
            "id",
            "name",
            "country",
            "continent",
            "num_stations",
            "num_lines",
            "num_light_lines",
            "num_interchanges",
            "bbox",
            "networks",
        ),
    )

    cities_info = list()
    names = set()
    next(reader)  # skipping the header
    for city_info in reader:
        if city_info["id"] and city_info["bbox"]:
            cities_info.append(city_info)
            name = city_info["name"].strip()
            if name in names:
                logging.warning(
                    "Duplicate city name in city list: %s",
                    city_info,
                )
            names.add(name)
    return cities_info


def prepare_cities(
    cities_info_url: str = DEFAULT_CITIES_INFO_URL, overground: bool = False
) -> list[City]:
    if overground:
        raise NotImplementedError("Overground transit not implemented yet")
    cities_info = get_cities_info(cities_info_url)
    return list(map(partial(City, overground=overground), cities_info))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cities-info-url",
        default=DEFAULT_CITIES_INFO_URL,
        help=(
            "URL of CSV file with reference information about rapid transit "
            "networks. file:// protocol is also supported."
        ),
    )
    parser.add_argument(
        "-i",
        "--source",
        help="File to write backup of OSM data, or to read data from",
    )
    parser.add_argument(
        "-x", "--xml", help="OSM extract with routes, to read data from"
    )
    parser.add_argument(
        "--overpass-api",
        default="http://overpass-api.de/api/interpreter",
        help="Overpass API URL",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Show only warnings and errors",
    )
    parser.add_argument(
        "-c", "--city", help="Validate only a single city or a country"
    )
    parser.add_argument(
        "-t",
        "--overground",
        action="store_true",
        help="Process overground transport instead of subways",
    )
    parser.add_argument(
        "-e",
        "--entrances",
        type=argparse.FileType("w", encoding="utf-8"),
        help="Export unused subway entrances as GeoJSON here",
    )
    parser.add_argument(
        "-l",
        "--log",
        type=argparse.FileType("w", encoding="utf-8"),
        help="Validation JSON file name",
    )

    for processor_name, processor in inspect.getmembers(
        processors, inspect.ismodule
    ):
        if not processor_name.startswith("_"):
            parser.add_argument(
                f"--output-{processor_name}",
                help=(
                    "Processed metro systems output filename "
                    f"in {processor_name.upper()} format"
                ),
            )

    parser.add_argument("--cache", help="Cache file name for processed data")
    parser.add_argument(
        "-r", "--recovery-path", help="Cache file name for error recovery"
    )
    parser.add_argument(
        "-d", "--dump", help="Make a YAML file for a city data"
    )
    parser.add_argument(
        "-j", "--geojson", help="Make a GeoJSON file for a city data"
    )
    parser.add_argument(
        "--crude",
        action="store_true",
        help="Do not use OSM railway geometry for GeoJSON",
    )
    options = parser.parse_args()

    if options.quiet:
        log_level = logging.WARNING
    else:
        log_level = logging.INFO
    logging.basicConfig(
        level=log_level,
        datefmt="%H:%M:%S",
        format="%(asctime)s %(levelname)-7s  %(message)s",
    )

    cities = prepare_cities(options.cities_info_url, options.overground)
    if options.city:
        cities = [
            c
            for c in cities
            if c.name == options.city or c.country == options.city
        ]
    if not cities:
        logging.error("No cities to process")
        sys.exit(2)

    # Augment cities with recovery data
    recovery_data = None
    if options.recovery_path:
        recovery_data = read_recovery_data(options.recovery_path)
        for city in cities:
            city.recovery_data = recovery_data.get(city.name, None)

    logging.info("Read %s metro networks", len(cities))

    # Reading cached json, loading XML or querying Overpass API
    if options.source and os.path.exists(options.source):
        logging.info("Reading %s", options.source)
        with open(options.source, "r") as f:
            osm = json.load(f)
            if "elements" in osm:
                osm = osm["elements"]
            calculate_centers(osm)
    elif options.xml:
        logging.info("Reading %s", options.xml)
        osm = load_xml(options.xml)
        calculate_centers(osm)
        if options.source:
            with open(options.source, "w", encoding="utf-8") as f:
                json.dump(osm, f)
    else:
        if len(cities) > 10:
            logging.error(
                "Would not download that many cities from Overpass API, "
                "choose a smaller set"
            )
            sys.exit(3)
        bboxes = [c.bbox for c in cities]
        logging.info("Downloading data from Overpass API")
        osm = multi_overpass(options.overground, options.overpass_api, bboxes)
        calculate_centers(osm)
        if options.source:
            with open(options.source, "w", encoding="utf-8") as f:
                json.dump(osm, f)
    logging.info("Downloaded %s elements", len(osm))

    logging.info("Sorting elements by city")
    add_osm_elements_to_cities(osm, cities)

    logging.info("Building routes for each city")
    good_cities = validate_cities(cities)

    logging.info("Finding transfer stations")
    transfers = find_transfers(osm, cities)

    good_city_names = set(c.name for c in good_cities)
    logging.info(
        "%s good cities: %s",
        len(good_city_names),
        ", ".join(sorted(good_city_names)),
    )
    bad_city_names = set(c.name for c in cities) - good_city_names
    logging.info(
        "%s bad cities: %s",
        len(bad_city_names),
        ", ".join(sorted(bad_city_names)),
    )

    if options.recovery_path:
        write_recovery_data(options.recovery_path, recovery_data, cities)

    if options.entrances:
        json.dump(get_unused_entrances_geojson(osm), options.entrances)

    if options.dump:
        if os.path.isdir(options.dump):
            for c in cities:
                with open(
                    os.path.join(options.dump, slugify(c.name) + ".yaml"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    dump_yaml(c, f)
        elif len(cities) == 1:
            with open(options.dump, "w", encoding="utf-8") as f:
                dump_yaml(cities[0], f)
        else:
            logging.error("Cannot dump %s cities at once", len(cities))

    if options.geojson:
        if os.path.isdir(options.geojson):
            for c in cities:
                with open(
                    os.path.join(
                        options.geojson, slugify(c.name) + ".geojson"
                    ),
                    "w",
                    encoding="utf-8",
                ) as f:
                    json.dump(make_geojson(c, not options.crude), f)
        elif len(cities) == 1:
            with open(options.geojson, "w", encoding="utf-8") as f:
                json.dump(make_geojson(cities[0], not options.crude), f)
        else:
            logging.error(
                "Cannot make a geojson of %s cities at once", len(cities)
            )

    if options.log:
        res = []
        for c in cities:
            v = c.get_validation_result()
            v["slug"] = slugify(c.name)
            res.append(v)
        json.dump(res, options.log, indent=2, ensure_ascii=False)

    for processor_name, processor in inspect.getmembers(
        processors, inspect.ismodule
    ):
        option_name = f"output_{processor_name}"

        if not getattr(options, option_name, None):
            continue

        filename = getattr(options, option_name)
        processor.process(cities, transfers, filename, options.cache)


if __name__ == "__main__":
    main()
