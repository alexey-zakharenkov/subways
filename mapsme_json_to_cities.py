import argparse
import json

from process_subways import download_cities


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        description="""
            This script generates a list of good/all network names.
            It is used by subway render to generate the list of network at frontend.
            It uses two sources: a mapsme.json validator output with good networks, and
            a google spreadsheet with networks for the process_subways.download_cities()
            function.""",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    arg_parser.add_argument(
        'subway_json_file',
        type=argparse.FileType('r'),
        help="Validator output defined by -o option of process_subways.py script",
    )

    arg_parser.add_argument(
        '--with-bad',
        action="store_true",
        help="Whether to include cities validation of which was failed",
    )

    args = arg_parser.parse_args()

    with_bad = args.with_bad
    subway_json_file = args.subway_json_file
    subway_json = json.load(subway_json_file)

    good_cities = set(
        n.get('network', n.get('title')) for n in subway_json['networks']
    )
    cities = download_cities()

    lines = []
    for c in cities:
        if c.name in good_cities:
            lines.append(f"{c.name}, {c.country}")
        elif with_bad:
            lines.append(f"{c.name}, {c.country} (Bad)")

    for line in sorted(lines):
        print(line)
