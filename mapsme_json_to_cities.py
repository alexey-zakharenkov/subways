"""
This script generates a list of good/all network names.
It is used by subway render to generate the list of network at frontend.
It uses two sources: a mapsme.json validator output with good networks, and
a google spreadsheet with networks for the process_subways.download_cities()
function.
"""

import json
import sys

from process_subways import download_cities


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: {} <mapsme.json> [--with-bad]'.format(sys.argv[0]))
        sys.exit(1)

    with_bad = len(sys.argv) > 2 and sys.argv[2] == '--with-bad'

    subway_json_file = sys.argv[1]
    with open(subway_json_file) as f:
        subway_json = json.load(f)
    good_cities = set(n.get('network', n.get('title')) for n in subway_json['networks'])

    cities = download_cities()
    lines = []
    for c in cities:
        if c.name in good_cities:
            lines.append(f"{c.name}, {c.country}")
        elif with_bad:
            lines.append(f"{c.name}, {c.country} (Bad)")

    for line in sorted(lines):
        print(line)
