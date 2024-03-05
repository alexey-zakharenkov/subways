import argparse
import inspect
import json
import logging
import os
import re
import sys

from subways import processors
from subways.overpass import multi_overpass
from subways.subway_io import (
    dump_yaml,
    load_xml,
    make_geojson,
    read_recovery_data,
    write_recovery_data,
)
from subways.structure.city import (
    find_transfers,
    get_unused_subway_entrances_geojson,
)
from subways.validation import (
    add_osm_elements_to_cities,
    BAD_MARK,
    calculate_centers,
    DEFAULT_CITIES_INFO_URL,
    prepare_cities,
    validate_cities,
)


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", "", name.lower().replace(" ", "_"))


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
    parser.add_argument(
        "--dump-city-list",
        type=argparse.FileType("w", encoding="utf-8"),
        help=(
            "Dump sorted list of all city names, possibly with "
            f"{BAD_MARK} mark"
        ),
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
    transfers = find_transfers(osm, good_cities)

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

    if options.dump_city_list:
        lines = sorted(
            f"{city.name}, {city.country}"
            f"{' ' + BAD_MARK if city.name in bad_city_names else ''}\n"
            for city in cities
        )
        options.dump_city_list.writelines(lines)

    if options.recovery_path:
        write_recovery_data(options.recovery_path, recovery_data, cities)

    if options.entrances:
        json.dump(get_unused_subway_entrances_geojson(osm), options.entrances)

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
