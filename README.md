# Subway Preprocessor

Here you see a list of scripts that can be used for preprocessing all the metro
systems in the world from OpenStreetMap. `subway_structure.py` produces
a list of disjunct systems that can be used for routing and for displaying
of metro maps.


## How To Validate

* Choose transport data source:
  1. Download or update a planet file in o5m format (using `osmconvert` and `osmupdate`).
     Run `osmfilter` to extract a portion of data for all subways. Or
  2. If you don't specify `--xml` or `--source` option to the `process_subways.py` script
     it tries to fetch data over [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API).
     **Not suitable for the whole planet or large countries.**
* Run `process_subways.py` with appropriate set of command line arguments
  to build metro structures and receive a validation log.
* Run `validation_to_html.py` on that log to create readable HTML tables.


## Validating of all metro networks

There is a `process_subways.sh` in the `scripts` directory that is suitable
for validation of all or many metro networks. It relies on a bunch of
environment variables and takes advantage of previous validation runs
for effective recurring validations. See
```bash
./scripts/process_subways.sh --help
```
for details. Here is an example of the script usage:

```bash
export PLANET=https://ftp5.gwdg.de/pub/misc/openstreetmap/planet.openstreetmap.org/pbf/planet-latest.osm.pbf
export PLANET_METRO="$HOME/metro/planet-metro.o5m
export OSMCTOOLS="$HOME/osmctools"
export TMPDIR="$HOME/metro/tmp"
export HTML_DIR="$HOME/metro/tmp_html"
export DUMP="$HTML_DIR"

scripts/process_subways.sh
```

Set the PLANET_METRO variable to avoid the whole planet processing each time.
Delete the file (but not the variable) to re-generate it if a new city has been added or
a city's bbox has been extended.


## Validating of a single city

A single city or a country with few metro networks can be validated much faster
if you allow the `process_subway.py` to fetch data from Overpass API. Here are the steps:

1. Python3 interpreter required (3.8+)
2. Clone the repo
    ```
    git clone https://github.com/alexey-zakharenkov/subways.git subways_validator
    cd subways_validator
   ```
3. Execute
    ```bash
    python3 ./process_subways.py -c "London" \
        -l validation.log -d London.yaml
    ```
    here
    - `-c` stands for "city" i.e. network name from the google spreadsheet
    - `-l`  - path to validation log file
    - `-d` (optional) - path to dump network info in YAML format
    - `-i` (optional) - path to save overpass-api JSON response
    - `-j` (optional) - path to output network GeoJSON (used for rendering)

    `validation.log` would contain the list of errors and warnings.
    To convert it into pretty HTML format
4. do
    ```bash
    mkdir html
    python3 ./validation_to_html.py validation.log html
    ```

## Related external resources

Summary information about all metro networks that are monitored is gathered in the
[Google Spreadsheet](https://docs.google.com/spreadsheets/d/1SEW1-NiNOnA2qDwievcxYV1FOaQl1mb1fdeyqAxHu3k).

Regular updates of validation results are available at
[this website](https://maps.mail.ru/osm/tools/subways/latest/).
You can find more info about this validator instance in
[OSM Wiki](https://wiki.openstreetmap.org/wiki/Quality_assurance#subway-preprocessor).


## Adding Stop Areas To OSM

To quickly add `stop_area` relations for the entire city, use the `make_stop_areas.py` script
from the `stop_area` directory. Give it a bounding box or a `.json` file download from Overpass API.
It would produce an JOSM XML file that you should manually check in JOSM. After that
just upload it.

## Author and License

The main scripts were originally written by Ilya Zverev for MAPS.ME
and were published under Apache Licence 2.0 at https://github.com/mapsme/subways/.

This fork is maintained by Alexey Zakharenkov and is also published under Apache Licence 2.0.
