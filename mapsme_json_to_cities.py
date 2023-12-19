"""
Generate sorted list of all cities, with [bad] mark for bad cities.

!!! Deprecated for use in validation cycle.
Use "process_subways.py --dump-city-list <filename>" instead.
"""


import argparse
import json

from process_subways import BAD_MARK, DEFAULT_CITIES_INFO_URL, get_cities_info


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description=(
            """This script generates a list of good/all network names. It is
            used by subway render to generate the list of network at frontend.
            It uses two sources: a mapsme.json validator output with good
            networks, and a google spreadsheet with networks for the
            process_subways.download_cities() function."""
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    arg_parser.add_argument(
        "subway_json_file",
        type=argparse.FileType("r"),
        help=(
            "Validator output defined by -o option "
            "of process_subways.py script",
        ),
    )

    arg_parser.add_argument(
        "--cities-info-url",
        default=DEFAULT_CITIES_INFO_URL,
        help=(
            "URL of CSV file with reference information about rapid transit "
            "networks. file:// protocol is also supported."
        ),
    )

    arg_parser.add_argument(
        "--with-bad",
        action="store_true",
        help="Whether to include cities validation of which was failed",
    )

    args = arg_parser.parse_args()

    with_bad = args.with_bad
    subway_json_file = args.subway_json_file
    subway_json = json.load(subway_json_file)

    good_cities = set(
        n.get("network", n.get("title")) for n in subway_json["networks"]
    )
    cities_info = get_cities_info(args.cities_info_url)

    lines = []
    for ci in cities_info:
        if ci["name"] in good_cities:
            lines.append(f"{ci['name']}, {ci['country']}")
        elif with_bad:
            lines.append(f"{ci['name']}, {ci['country']} {BAD_MARK}")

    for line in sorted(lines):
        print(line)
