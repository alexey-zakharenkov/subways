#!/bin/bash
set -e -u

if [ $# -gt 0 -a \( "${1-}" = "-h" -o "${1-}" = '--help' \) ]; then
  cat << EOF
This script updates a planet or an extract, processes metro networks in it
and produces a set of HTML files with validation results.

Usage: $0 [<local/planet.{pbf,o5m} | http://mirror.osm.ru/planet.{pbf,o5m}>]

OSM data is processed with osmium-tool if it is available, otherwise with
osmctools (osmconvert, osmupdate, osmfilter). See \$OSM_TOOLS below.

In more detail, the script does the following:
  - If \$PLANET is a remote file, downloads it.
  - If \$BBOX variable is set, proceeds with this setting for the planet clipping. Otherwise uses \$POLY:
    unless \$POLY variable is set and the file exists, generates a *.poly file with union of bboxes of all cities having metro.
  - Makes an extract of the \$PLANET using the *.poly file.
  - Updates the extract.
  - Filters railway infrastructure from the extract.
  - Uses filtered file for validation and generates a bunch of output files.
  - Copies results onto remote server, if it is set up.

During this procedure, as many steps are skipped as possible. Namely:
  - Generation of metro extract is skipped if \$PLANET_METRO variable is set and the file exists.
  - Update of the extract is skipped if \$SKIP_PLANET_UPDATE or \$SKIP_FILTERING is set.
  - Filtering is skipped if \$SKIP_FILTERING is set and \$FILTERED_DATA is set and the file exists.

Generated files \$POLY, \$PLANET_METRO, \$FILTERED_DATA are deleted if the corresponding
variable is not defined or is null, otherwise they are kept.
The \$PLANET file from remote URL is saved to a tempfile and is removed at the end.

Environment variable reference:
  - PLANET: path to a local or remote pbf or o5m source file (the entire planet or an extract)
  - PLANET_METRO: path to a local file with extract of cities having metro
    It's used instead of \$PLANET if exists otherwise it's created first.
    Supported formats: pbf or osm with osmium-tool, o5m or osm with osmctools.
    An existing o5m file implies osmctools since osmium cannot write o5m.
  - PLANET_UPDATE_SERVER: server to get replication data from. Defaults to
    https://planet.openstreetmap.org/replication/hour/ for osmium-tool (a specific replication stream is required) and
    https://planet.openstreetmap.org/replication/ for osmctools
  - OSM_TOOLS: "osmium" or "osmctools" to force the toolset. By default osmium-tool is used
    if found, otherwise osmctools
  - OSMIUM: path to osmium executable. Defaults to "osmium" from \$PATH
  - OSMCTOOLS: path to a directory with osmconvert, osmupdate and osmfilter binaries.
    Defaults to \$HOME/osmctools or the directory of osmupdate from \$PATH
  - CITIES_INFO_URL: one or more space-separated http(s) or "file://" URLs to CSV files with reference information about rapid transit systems.
    Cities from all sources are concatenated; for records sharing the same id or name, the later URL wins (useful for "base + local override").
    A default value is hammered into python code. URLs/paths must not contain spaces.
  - CITY: name of a city/country to process
  - BBOX: bounding box of an extract; x1,y1,x2,y2. Has precedence over \$POLY
  - POLY: *.poly file with [multi]polygon comprising cities with metro
    If neither \$BBOX nor \$POLY is set, then \$POLY is generated
  - SKIP_PLANET_UPDATE: skip \$PLANET_METRO file update. Any non-empty string is True
  - SKIP_FILTERING: skip filtering railway data. Any non-empty string is True
  - FILTERED_DATA: path to filtered data. Defaults to \$TMPDIR/subways.osm
  - MAPSME: file name for maps.me json output
  - GTFS: file name for GTFS output
  - DUMP: directory/file name to dump YAML city data. Do not set to omit dump
  - GEOJSON: directory/file name to dump GeoJSON data. Do not set to omit dump
  - ELEMENTS_CACHE: file name to elements cache. Allows OSM xml processing phase
  - CITY_CACHE: json file with good cities obtained on previous validation runs
  - RECOVERY_PATH: file with some data collected at previous validation runs that
    may help to recover some simple validation errors
  - PYTHON: python 3 executable
  - GIT_PULL: set to 1 to update the scripts
  - TMPDIR: path to temporary files
  - HTML_DIR: target path for generated HTML files
  - DUMP_CITY_LIST: file name to save sorted list of cities, with [bad] mark for bad cities
  - SERVER: server name and path to upload HTML files (e.g. ilya@osmz.ru:/var/www/)
  - SERVER_KEY: rsa key to supply for uploading the files
  - REMOVE_HTML: set to 1 to remove \$HTML_DIR after uploading
  - QUIET: set to any non-empty value to use WARNING log level in process_subways.py. Default is INFO.
EOF
  exit
fi


function activate_venv_at_path() {
  path=$1

  if [ ! -d "$path/".venv ]; then
    "${PYTHON:-python3.11}" -m venv "$path"/.venv
  fi

  source "$path"/.venv/bin/activate

  if [ -f "$path"/requirements.txt ]; then
    # Invoke pip via "python -m" to sidestep macOS's 80-byte shebang limit:
    # when the repo lives under a long path, pip's shebang gets truncated
    # mid-path ("python3.11" -> "py") and direct invocation fails.
    python -m pip install --upgrade pip
    python -m pip install -r "$path"/requirements.txt
  fi
}


function find_osmium() {
  OSMIUM="${OSMIUM:-osmium}"
  command -v "$OSMIUM" > /dev/null
}


function find_osmctools() {
  OSMCTOOLS="${OSMCTOOLS:-$HOME/osmctools}"
  if [ ! -f "$OSMCTOOLS/osmupdate" ]; then
    if command -v osmupdate > /dev/null; then
      OSMCTOOLS="$(dirname "$(command -v osmupdate)")"
    else
      return 1
    fi
  fi
}


function select_osm_tools() {
  # Chooses between osmium-tool (preferred) and osmctools (fallback);
  # does this only once during script run.

  if [ -n "${OSM_TOOLS_SELECTED-}" ]; then
    return
  fi

  local planet_metro_ext=""
  if [ -n "${PLANET_METRO-}" ]; then
    planet_metro_ext="${PLANET_METRO##*.}"
  fi

  case "${OSM_TOOLS-}" in
    osmium)
      if ! find_osmium; then
        echo "osmium-tool not found. Install it (see README) or set OSMIUM=/path/to/osmium"
        exit 1
      fi
      ;;
    osmctools)
      if ! find_osmctools; then
        echo "Please compile osmctools to $OSMCTOOLS"
        exit 1
      fi
      ;;
    "")
      # osmium cannot write o5m, so an existing o5m extract
      # can only be maintained with osmctools
      if [ "$planet_metro_ext" = "o5m" ]; then
        if ! find_osmctools; then
          echo "PLANET_METRO is an o5m file, which requires osmctools."
          echo "Compile osmctools to $OSMCTOOLS or convert PLANET_METRO to pbf."
          exit 1
        fi
        OSM_TOOLS=osmctools
      elif find_osmium; then
        OSM_TOOLS=osmium
      elif find_osmctools; then
        OSM_TOOLS=osmctools
      else
        echo "Neither osmium-tool nor osmctools found."
        echo "Install osmium-tool (see README) or set OSMIUM=/path/to/osmium."
        exit 1
      fi
      ;;
    *)
      echo "OSM_TOOLS must be 'osmium' or 'osmctools', got '$OSM_TOOLS'"
      exit 1
      ;;
  esac

  # Supported PLANET_METRO formats: osmium cannot write o5m,
  # osmfilter cannot read pbf
  if [ -n "$planet_metro_ext" ]; then
    if [ "$OSM_TOOLS" = "osmium" ]; then
      supported_exts="pbf osm"
    else
      supported_exts="o5m osm xml"
    fi
    if [[ " $supported_exts " != *" $planet_metro_ext "* ]]; then
      echo "PLANET_METRO format '$planet_metro_ext' is not supported with $OSM_TOOLS."
      echo "Supported formats: $supported_exts"
      exit 3
    fi
  fi

  echo "Using $OSM_TOOLS for OSM data processing"
  OSM_TOOLS_SELECTED=1
}


function extract_area() {
  # Usage: extract_area <input file> <output file> [keep_replication_headers]
  # Cuts out the area defined by $BBOX or $POLY. With the third argument
  # set, osmium copies replication headers from the input file so that
  # pyosmium-up-to-date can continue updates from the right place.
  if [ "$OSM_TOOLS" = "osmium" ]; then
    local header_args=()
    if [ -n "${3-}" ]; then
      for option in osmosis_replication_base_url \
                    osmosis_replication_sequence_number \
                    osmosis_replication_timestamp; do
        header_args+=("--output-header=$option!")
      done
    fi
    "$OSMIUM" extract "$1" \
        ${BBOX:+"--bbox=$BBOX"} ${POLY:+"--polygon=$POLY"} \
        ${header_args[@]+"${header_args[@]}"} -O -o "$2"
  else
    mkdir -p $TMPDIR/osmconvert_temp/
    "$OSMCTOOLS"/osmconvert "$1" \
        -t=$TMPDIR/osmconvert_temp/temp \
        ${BBOX:+"-b=$BBOX"} ${POLY:+"-B=$POLY"} -o="$2"
  fi
}


function update_planet_metro_osmium() {
  PLANET_UPDATE_SERVER=${PLANET_UPDATE_SERVER:-https://planet.openstreetmap.org/replication/hour/}
  # pyosmium needs a specific replication stream, while osmupdate accepts
  # the base replication URL: use hourly diffs for the latter
  case "$PLANET_UPDATE_SERVER" in
    */replication|*/replication/)
      PLANET_UPDATE_SERVER="${PLANET_UPDATE_SERVER%/}/hour/"
      ;;
  esac
  PLANET_METRO_ABS="$(cd "$(dirname "$PLANET_METRO")"; pwd)/$(basename "$PLANET_METRO")"
  PLANET_METRO_ABS_NEW="$PLANET_METRO_ABS.new.osm.pbf"
  mkdir -p "$TMPDIR/osmupdate_temp"
  rm -f "$PLANET_METRO_ABS_NEW"

  activate_venv_at_path "$SUBWAYS_REPO_PATH/scripts"

  # pyosmium-up-to-date downloads at most ~1 GB of diffs (about 3 days
  # of hourly diffs) per call and returns 1 if more data is available,
  # so call it repeatedly. It refuses to update files older than 3 months,
  # so the number of iterations is bounded.
  local max_iterations=40
  local iteration
  local update_rc=1
  local update_output
  for ((iteration = 1; iteration <= max_iterations; iteration++)); do
    local update_args=()
    if [ -f "$PLANET_METRO_ABS_NEW" ]; then
      # Continue updating the partially updated file in place
      update_args=("$PLANET_METRO_ABS_NEW")
    else
      update_args=("$PLANET_METRO_ABS" -o "$PLANET_METRO_ABS_NEW")
    fi
    update_rc=0
    update_output=$(pyosmium-up-to-date "${update_args[@]}" \
                        --server "$PLANET_UPDATE_SERVER" \
                        --tmpdir "$TMPDIR/osmupdate_temp" 2>&1) || update_rc=$?
    if [ -n "$update_output" ]; then
      echo "$update_output"
    fi
    # Exit code 1 also results from an uncaught exception
    if [ "$update_rc" -eq 1 ] && [[ "$update_output" == *Traceback* ]]; then
      update_rc=254
    fi
    if [ "$update_rc" -ne 1 ]; then
      break
    fi
    echo "Partial update applied, downloading more diffs"
  done
  deactivate

  if [ "$update_rc" -ne 0 ]; then
    rm -f "$PLANET_METRO_ABS_NEW"
    if [ "$update_rc" -eq 1 ]; then
      echo "pyosmium-up-to-date failed: the extract is still not up to date after $max_iterations iterations"
    else
      echo "pyosmium-up-to-date failed with exit code $update_rc"
    fi
    exit 7
  fi

  if [ ! -f "$PLANET_METRO_ABS_NEW" ]; then
    # Nothing to update, the file was already up to date
    return
  fi

  # Since updating adds things outside the area, trim those again.
  extract_area "$PLANET_METRO_ABS_NEW" "$PLANET_METRO_ABS" keep_replication_headers
  rm -f "$PLANET_METRO_ABS_NEW"
}


function update_planet_metro_osmctools() {
  PLANET_UPDATE_SERVER=${PLANET_UPDATE_SERVER:-https://planet.openstreetmap.org/replication/}
  PLANET_METRO_ABS="$(cd "$(dirname "$PLANET_METRO")"; pwd)/$(basename "$PLANET_METRO")"
  mkdir -p $TMPDIR/osmupdate_temp/
  pushd $TMPDIR/osmupdate_temp/
  export PATH="$PATH:$OSMCTOOLS"
  OSMUPDATE_ERRORS=$(osmupdate --drop-author --out-o5m ${BBOX:+"-b=$BBOX"} \
                                 ${POLY:+"-B=$POLY"} "$PLANET_METRO_ABS" \
                                 --base-url=$PLANET_UPDATE_SERVER \
                                 --tempfiles=$TMPDIR/osmupdate_temp/temp \
                                 "$PLANET_METRO_ABS.new.o5m" 2>&1 || :)
  if [ -n "$OSMUPDATE_ERRORS" ]; then
    echo "osmupdate failed: $OSMUPDATE_ERRORS"
    exit 7
  fi
  popd
  mv "$PLANET_METRO_ABS.new.o5m" "$PLANET_METRO_ABS"
}


function filter_planet_metro() {
  if [ "$OSM_TOOLS" = "osmium" ]; then
    QRELATIONS="r/route,route_master=subway,light_rail,monorail,train r/public_transport=stop_area,stop_area_group"
    QNODES="n/railway=station,subway_entrance,train_station_entrance n/station=subway,light_rail,monorail n/subway=yes n/light_rail=yes n/monorail=yes n/train=yes"
    # Metadata (versions, timestamps, users) is not used by the validator
    "$OSMIUM" tags-filter "$PLANET_METRO" $QRELATIONS $QNODES \
        -f osm,add_metadata=false -o "$FILTERED_DATA" -O
  else
    mkdir -p $TMPDIR/osmfilter_temp/
    QRELATIONS="route=subway =light_rail =monorail =train route_master=subway =light_rail =monorail =train public_transport=stop_area =stop_area_group"
    QNODES="railway=station =subway_entrance =train_station_entrance station=subway =light_rail =monorail subway=yes light_rail=yes monorail=yes train=yes"
    "$OSMCTOOLS/osmfilter" "$PLANET_METRO" \
        --keep= \
        --keep-relations="$QRELATIONS" \
        --keep-nodes="$QNODES" \
        --drop-author \
        -t=$TMPDIR/osmfilter_temp/temp \
        -o="$FILTERED_DATA"
  fi
}


function check_poly() {
  # Checks or generates *.poly file covering cities where
  # there is a metro; does this only once during script run.

  if [ -z "${POLY_CHECKED-}" ]; then
    if [ -n "${BBOX-}" ]; then
      # If BBOX is set, then exclude POLY at all from processing
      POLY=""
    else
      if [ -z "${POLY-}" ]; then
        NEED_TO_REMOVE_POLY=1
      fi

      if [ -z "${POLY-}" -o ! -f "${POLY-}" ]; then
        POLY=${POLY:-$(mktemp "$TMPDIR/all-metro.XXXXXXXX.poly")}
        activate_venv_at_path "$SUBWAYS_REPO_PATH/tools/make_poly"
        python "$SUBWAYS_REPO_PATH"/tools/make_poly/make_all_metro_poly.py \
            ${CITIES_INFO_URL:+--cities-info-url $CITIES_INFO_URL} > "$POLY"
        deactivate
      fi
    fi
    POLY_CHECKED=1
  fi
}

# "readlink -f" echoes canonicalized absolute path to a file/directory
SUBWAYS_REPO_PATH="$(readlink -f $(dirname "$0")/..)"

if [ ! -f "$SUBWAYS_REPO_PATH/scripts/process_subways.py" ]; then
  echo "Please clone the subways repo to $SUBWAYS_REPO_PATH"
  exit 2
fi

# Contains 'subways' dir and is required by the main validator python script
# as well as by some tools
export PYTHONPATH="$SUBWAYS_REPO_PATH"

# Downloading the latest version of the subways script
if [ -n "${GIT_PULL-}" ]; then (
  pushd "$SUBWAYS_REPO_PATH"
  git pull origin master
  popd
) fi


TMPDIR="${TMPDIR:-"$SUBWAYS_REPO_PATH"}"
mkdir -p "$TMPDIR"

if [ -z "${FILTERED_DATA-}" ]; then
  FILTERED_DATA="$TMPDIR/subways.osm"
  NEED_TO_REMOVE_FILTERED_DATA=1
fi

if [ -z "${SKIP_FILTERING-}" -o ! -f "$FILTERED_DATA" ]; then
  NEED_FILTER=1
fi


if [ -n "${NEED_FILTER-}" ]; then

  select_osm_tools

  # If $PLANET_METRO file doesn't exist, create it

  if [ ! -f "${PLANET_METRO-}" ]; then
    check_poly

    PLANET="${PLANET:-${1-}}"
    EXT="${PLANET##*.}"
    if [ ! "$EXT" = "pbf" -a ! "$EXT" = "o5m" ]; then
      echo "Cannot process '$PLANET' planet file."
      echo "Only pbf/o5m source planet files are supported."
      exit 4
    fi

    if [ "${PLANET:0:7}" = "http://" -o \
         "${PLANET:0:8}" = "https://" -o \
         "${PLANET:0:6}" = "ftp://" ]; then
      PLANET_TEMP=$(mktemp "$TMPDIR/planet.XXXXXXXX.$EXT")
      wget -O "$PLANET_TEMP" "$PLANET"
      PLANET="$PLANET_TEMP"
    elif [ ! -f "$PLANET" ]; then
      echo "Cannot find planet file '$PLANET'";
      exit 5
    fi

    if [ -z "${PLANET_METRO-}" ]; then
      if [ "$OSM_TOOLS" = "osmium" ]; then
        PLANET_METRO=$(mktemp "$TMPDIR/planet-metro.XXXXXXXX.osm.pbf")
      else
        PLANET_METRO=$(mktemp "$TMPDIR/planet-metro.XXXXXXXX.o5m")
      fi
      NEED_TO_REMOVE_PLANET_METRO=1
    fi

    if [ "$PLANET" = "$PLANET_METRO" ]; then
      echo "PLANET_METRO parameter shouldn't point to PLANET."
      exit 6
    fi

    extract_area "$PLANET" "$PLANET_METRO"
  fi
fi

if [ -n "${PLANET_TEMP-}" ]; then
  rm "$PLANET_TEMP"
fi

# Updating the planet-metro file

# If there's no need to filter, then update is also unnecessary
if [ -z "${SKIP_PLANET_UPDATE-}" -a -n "${NEED_FILTER-}" ]; then
  check_poly
  update_planet_metro_$OSM_TOOLS
fi

# Filtering planet-metro

if [ -n "${NEED_FILTER-}" ]; then
  filter_planet_metro
fi

if [ -n "${NEED_TO_REMOVE_PLANET_METRO-}" ]; then
  rm $PLANET_METRO
fi
if [ -n "${NEED_TO_REMOVE_POLY-}" ]; then
  rm $POLY
fi

# Running the validation

if [ -n "${DUMP-}" ]; then
   mkdir -p "$DUMP"
fi

VALIDATION="$TMPDIR/validation.json"

activate_venv_at_path "$SUBWAYS_REPO_PATH/scripts"
python "$SUBWAYS_REPO_PATH/scripts/process_subways.py" ${QUIET:+-q} \
    -x "$FILTERED_DATA" -l "$VALIDATION" \
    ${CITIES_INFO_URL:+--cities-info-url $CITIES_INFO_URL} \
    ${MAPSME:+--output-mapsme "$MAPSME"} \
    ${GTFS:+--output-gtfs "$GTFS"} \
    ${CITY:+-c "$CITY"} \
    ${DUMP:+-d "$DUMP"} \
    ${GEOJSON:+-j "$GEOJSON"} \
    ${DUMP_CITY_LIST:+--dump-city-list "$DUMP_CITY_LIST"} \
    ${ELEMENTS_CACHE:+-i "$ELEMENTS_CACHE"} \
    ${CITY_CACHE:+--cache "$CITY_CACHE"} \
    ${RECOVERY_PATH:+-r "$RECOVERY_PATH"}
deactivate


if [ -n "${NEED_TO_REMOVE_FILTERED_DATA-}" ]; then
  rm "$FILTERED_DATA"
fi

# Preparing HTML files

if [ -z "${HTML_DIR-}" ]; then
  HTML_DIR="$SUBWAYS_REPO_PATH/html"
  REMOVE_HTML=1
fi

mkdir -p $HTML_DIR
rm -f "$HTML_DIR"/*.html

activate_venv_at_path "$SUBWAYS_REPO_PATH/tools/v2h"
python "$SUBWAYS_REPO_PATH/tools/v2h/validation_to_html.py" \
    "$VALIDATION" "$HTML_DIR" \
    ${CITIES_INFO_URL:+--cities-info-url $CITIES_INFO_URL}
deactivate

# Uploading files to the server

if [ -n "${SERVER-}" ]; then
  scp -q ${SERVER_KEY+-i "$SERVER_KEY"} "$HTML_DIR"/* "$SERVER"
  if [ -n "${REMOVE_HTML-}" ]; then
    rm -r "$HTML_DIR"
  fi
fi

