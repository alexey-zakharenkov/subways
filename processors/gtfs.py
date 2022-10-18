import csv
import io
import zipfile

from itertools import permutations

from ._common import (
    DEFAULT_INTERVAL,
    format_colour,
    SPEED_ON_TRANSFER,
    TRANSFER_PENALTY,
)
from subway_structure import (
    distance,
    el_center,
)


DEFAULT_TRIP_START_TIME = (5, 0)  # 05:00
DEFAULT_TRIP_END_TIME = (1, 0)  # 01:00
COORDINATE_PRECISION = 7  # fractional digits. It's OSM precision, ~ 5 cm

GTFS_COLUMNS = {
    "agency": [
        "agency_id",
        "agency_name",
        "agency_url",
        "agency_timezone",
        "agency_lang",
        "agency_phone",
    ],
    "routes": [
        "route_id",
        "agency_id",
        "route_short_name",
        "route_long_name",
        "route_desc",
        "route_type",
        "route_url",
        "route_color",
        "route_text_color",
        "route_sort_order",
        "route_fare_class",
        "line_id",
        "listed_route",
    ],
    "trips": [
        "route_id",
        "service_id",
        "trip_id",
        "trip_headsign",
        "trip_short_name",
        "direction_id",
        "block_id",
        "shape_id",
        "wheelchair_accessible",
        "trip_route_type",
        "route_pattern_id",
        "bikes_allowed",
    ],
    "stops": [
        "stop_id",
        "stop_code",
        "stop_name",
        "stop_desc",
        "platform_code",
        "platform_name",
        "stop_lat",
        "stop_lon",
        "zone_id",
        "stop_address",
        "stop_url",
        "level_id",
        "location_type",
        "parent_station",
        "wheelchair_boarding",
        "municipality",
        "on_street",
        "at_street",
        "vehicle_type",
    ],
    "calendar": [
        "service_id",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "start_date",
        "end_date",
    ],
    "stop_times": [
        "trip_id",
        "arrival_time",
        "departure_time",
        "stop_id",
        "stop_sequence",
        "stop_headsign",
        "pickup_type",
        "drop_off_type",
        "shape_dist_traveled",
        "timepoint",
        "checkpoint_id",
        "continuous_pickup",
        "continuous_drop_off",
    ],
    "frequencies": [
        "trip_id",
        "start_time",
        "end_time",
        "headway_secs",
        "exact_times",
    ],
    "shapes": [
        "shape_id",
        "shape_pt_lat",
        "shape_pt_lon",
        "shape_pt_sequence",
        "shape_dist_traveled",
    ],
    "transfers": [
        "from_stop_id",
        "to_stop_id",
        "transfer_type",
        "min_transfer_time",
    ],
}


def dict_to_row(dict_data, record_type):
    """Given object stored in a dict and an array of columns,
    returns a row to use in CSV.
    """
    row = []
    for column in GTFS_COLUMNS[record_type]:
        value = dict_data.get(column)
        if value is None:
            value = ""
        row.append(value)
    return row


def round_coords(coords_tuple):
    return tuple(
        map(lambda coord: round(coord, COORDINATE_PRECISION), coords_tuple)
    )


def process(cities, transfers, filename, cache_path):
    """Generate all output and save to file.
    :param cities: List of City instances
    :param transfers: List of sets of StopArea.id
    :param filename: Path to file to save the result
    :param cache_path: Path to json-file with good cities cache or None.
    """

    # TODO: make universal cache for all processors, and apply the cache to GTFS

    # Keys correspond GTFS file names
    gtfs_data = {key: [] for key in GTFS_COLUMNS.keys()}

    gtfs_data["calendar"].append(
        dict_to_row(
            {
                "service_id": "always",
                "monday": 1,
                "tuesday": 1,
                "wednesday": 1,
                "thursday": 1,
                "friday": 1,
                "saturday": 1,
                "sunday": 1,
                "start_date": "19700101",
                "end_date": "30000101",
            },
            "calendar",
        )
    )

    all_stops = {}  # stop (stop area center or station) el_id -> stop data
    good_cities = [c for c in cities if c.is_good]

    def add_stop_gtfs(route_stop, city):
        """Add stop to all_stops.
        If it's not a station, also add parent station
        if it has not been added yet. Return gtfs stop_id.
        """

        # For the case a StopArea is derived solely from railway=station
        # object, we generate GTFS platform (stop), station and sometimes
        # an entrance from the same object, so use suffixes
        station_id = f"{route_stop.stoparea.id}_st"
        platform_id = f"{route_stop.stoparea.id}_plt"

        if station_id not in all_stops:
            station_name = route_stop.stoparea.station.name
            station_center = round_coords(route_stop.stoparea.center)

            station_gtfs = {
                "stop_id": station_id,
                "stop_code": station_id,
                "stop_name": station_name,
                "stop_lat": station_center[1],
                "stop_lon": station_center[0],
                "location_type": 1,  # station in GTFS terms
            }
            all_stops[station_id] = station_gtfs

            platform_gtfs = {
                "stop_id": platform_id,
                "stop_code": platform_id,
                "stop_name": station_name,
                "stop_lat": station_center[1],
                "stop_lon": station_center[0],
                "location_type": 0,  # stop/platform in GTFS terms
                "parent_station": station_id,
            }
            all_stops[platform_id] = platform_gtfs

            osm_entrance_ids = (
                route_stop.stoparea.entrances | route_stop.stoparea.exits
            )
            if not osm_entrance_ids:
                entrance_id = f"{route_stop.stoparea.id}_egress"
                entrance_gtfs = {
                    "stop_id": entrance_id,
                    "stop_code": entrance_id,
                    "stop_name": station_name,
                    "stop_lat": station_center[1],
                    "stop_lon": station_center[0],
                    "location_type": 2,
                    "parent_station": station_id,
                }
                all_stops[entrance_id] = entrance_gtfs
            else:
                for osm_entrance_id in osm_entrance_ids:
                    entrance = city.elements[osm_entrance_id]
                    entrance_id = f"{osm_entrance_id}_{route_stop.stoparea.id}"
                    entrance_name = entrance["tags"].get("name")
                    if not entrance_name:
                        entrance_name = station_name
                        ref = entrance["tags"].get("ref")
                        if ref:
                            entrance_name += f" {ref}"
                    center = el_center(entrance)
                    center = round_coords(center)
                    entrance_gtfs = {
                        "stop_id": entrance_id,
                        "stop_code": entrance_id,
                        "stop_name": entrance_name,
                        "stop_lat": center[1],
                        "stop_lon": center[0],
                        "location_type": 2,
                        "parent_station": station_id,
                    }
                    all_stops[entrance_id] = entrance_gtfs

        return platform_id

    # agency, routes, trips, stop_times, frequencies, shapes
    for city in good_cities:
        agency = {"agency_id": city.id, "agency_name": city.name}
        gtfs_data["agency"].append(dict_to_row(agency, "agency"))

        for city_route in city:
            route = {
                "route_id": city_route.id,
                "agency_id": agency["agency_id"],
                "route_type": 12 if city_route.mode == "monorail" else 1,
                "route_short_name": city_route.ref,
                "route_long_name": city_route.name,
                "route_color": format_colour(city_route.colour),
            }
            gtfs_data["routes"].append(dict_to_row(route, "routes"))

            for variant in city_route:
                shape_id = variant.id[1:]  # truncate leading 'r'
                trip = {
                    "trip_id": variant.id,
                    "route_id": route["route_id"],
                    "service_id": "always",
                    "shape_id": shape_id,
                }
                gtfs_data["trips"].append(dict_to_row(trip, "trips"))

                tracks = variant.get_extended_tracks()
                tracks = variant.get_truncated_tracks(tracks)

                for i, (lon, lat) in enumerate(tracks):
                    lon, lat = round_coords((lon, lat))
                    gtfs_data["shapes"].append(
                        dict_to_row(
                            {
                                "shape_id": shape_id,
                                "trip_id": variant.id,
                                "shape_pt_lat": lat,
                                "shape_pt_lon": lon,
                                "shape_pt_sequence": i,
                            },
                            "shapes",
                        )
                    )

                start_time = variant.start_time or DEFAULT_TRIP_START_TIME
                end_time = variant.end_time or DEFAULT_TRIP_END_TIME
                if end_time <= start_time:
                    end_time = (end_time[0] + 24, end_time[1])
                start_time = f"{start_time[0]:02d}:{start_time[1]:02d}:00"
                end_time = f"{end_time[0]:02d}:{end_time[1]:02d}:00"

                gtfs_data["frequencies"].append(
                    dict_to_row(
                        {
                            "trip_id": variant.id,
                            "start_time": start_time,
                            "end_time": end_time,
                            "headway_secs": variant.interval
                            or DEFAULT_INTERVAL,
                        },
                        "frequencies",
                    )
                )

                for stop_sequence, route_stop in enumerate(variant):
                    gtfs_platform_id = add_stop_gtfs(route_stop, city)

                    gtfs_data["stop_times"].append(
                        dict_to_row(
                            {
                                "trip_id": variant.id,
                                "stop_sequence": stop_sequence,
                                "shape_dist_traveled": route_stop.distance,
                                "stop_id": gtfs_platform_id,
                            },
                            "stop_times",
                        )
                    )

    # stops
    gtfs_data["stops"].extend(
        map(lambda row: dict_to_row(row, "stops"), all_stops.values())
    )

    # transfers
    for stoparea_set in transfers:
        for stoparea1 in stoparea_set:
            for stoparea2 in stoparea_set:
                if stoparea1.id < stoparea2.id:
                    stop1_id = f"{stoparea1.id}_st"
                    stop2_id = f"{stoparea2.id}_st"
                    if not {stop1_id, stop2_id}.issubset(all_stops):
                        continue
                    transfer_time = TRANSFER_PENALTY + round(
                        distance(stoparea1.center, stoparea2.center)
                        / SPEED_ON_TRANSFER
                    )
                    for id1, id2 in permutations((stop1_id, stop2_id)):
                        gtfs_data["transfers"].append(
                            dict_to_row(
                                {
                                    "from_stop_id": id1,
                                    "to_stop_id": id2,
                                    "transfer_type": 0,
                                    "min_transfer_time": transfer_time,
                                },
                                "transfers",
                            )
                        )

    make_gtfs(filename, gtfs_data)


def make_gtfs(filename, gtfs_data):
    if not filename.lower().endswith("zip"):
        filename = f"{filename}.zip"

    with zipfile.ZipFile(filename, "w") as zf:
        for gtfs_feature, columns in GTFS_COLUMNS.items():
            with io.StringIO(newline="") as string_io:
                writer = csv.writer(string_io, delimiter=",")
                writer.writerow(columns)
                writer.writerows(gtfs_data[gtfs_feature])
                zf.writestr(f"{gtfs_feature}.txt", string_io.getvalue())
