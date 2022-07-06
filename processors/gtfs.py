import csv
import io
import zipfile

from ._common import (
    DEFAULT_INTERVAL,
    format_colour,
    SPEED_ON_TRANSFER,
    TRANSFER_PENALTY,
)
from subway_structure import (
    distance,
)


DEFAULT_TRIP_START_TIME = "05:00:00"
DEFAULT_TRIP_END_TIME = "01:00:00"
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
    good_cities = [c for c in cities if c.is_good()]

    def add_stop_gtfs(route_stop):
        """Add stop to all_stops.
        If it's not a station, also add parent station
        if it has not been added yet. Return gtfs stop_id.
        """
        is_real_stop_area = (
            route_stop.stoparea.element["tags"].get("public_transport")
            == "stop_area"
        )
        el_id_ = route_stop.stoparea.id

        if el_id_ not in all_stops:
            station_name = route_stop.stoparea.station.name
            center = route_stop.stoparea.center
            location_type = 1 if is_real_stop_area else 0
            stop_gtfs = {
                "stop_id": el_id_,
                "stop_code": el_id_,
                "stop_name": station_name,
                "stop_lat": round(center[1], COORDINATE_PRECISION),
                "stop_lon": round(center[0], COORDINATE_PRECISION),
                "location_type": location_type,
            }
            if is_real_stop_area:
                station_id = route_stop.stoparea.station.id
                stop_gtfs["parent_station"] = station_id
                if station_id not in all_stops:
                    center = route_stop.stoparea.station.center
                    station_gtfs = {
                        "stop_id": station_id,
                        "stop_code": station_id,
                        "stop_name": station_name,
                        "stop_lat": round(center[1], COORDINATE_PRECISION),
                        "stop_lon": round(center[0], COORDINATE_PRECISION),
                        "location_type": 1,
                    }
                    all_stops[station_id] = station_gtfs
            all_stops[el_id_] = stop_gtfs
        return el_id_

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
                trip = {
                    "trip_id": variant.id,
                    "route_id": route["route_id"],
                    "service_id": "always",
                    "shape_id": None,
                }
                gtfs_data["trips"].append(dict_to_row(trip, "trips"))

                tracks = variant.get_extended_tracks()
                tracks = variant.get_truncated_tracks(tracks)

                for i, (lon, lat) in enumerate(tracks):
                    gtfs_data["shapes"].append(
                        dict_to_row(
                            {
                                "shape_id": variant.id,
                                "trip_id": variant.id,
                                "shape_pt_lat": round(
                                    lat, COORDINATE_PRECISION
                                ),
                                "shape_pt_lon": round(
                                    lon, COORDINATE_PRECISION
                                ),
                                "shape_pt_sequence": i,
                            },
                            "shapes",
                        )
                    )

                gtfs_data["frequencies"].append(
                    dict_to_row(
                        {
                            "trip_id": variant.id,
                            "start_time": variant.start_time
                            or DEFAULT_TRIP_START_TIME,
                            "end_time": variant.end_time
                            or DEFAULT_TRIP_END_TIME,
                            "headway_secs": variant.interval
                            or DEFAULT_INTERVAL,
                        },
                        "frequencies",
                    )
                )

                for stop_sequence, route_stop in enumerate(variant):
                    gtfs_stop_id = add_stop_gtfs(route_stop)

                    stop_time = {
                        "trip_id": variant.id,
                        "stop_sequence": stop_sequence,
                        "shape_dist_traveled": route_stop.distance,
                        "stop_id": gtfs_stop_id,
                    }

                    gtfs_data["stop_times"].append(
                        dict_to_row(stop_time, "stop_times")
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
                    transfer_time = TRANSFER_PENALTY + round(
                        distance(stoparea1.center, stoparea2.center)
                        / SPEED_ON_TRANSFER
                    )
                    for id1, id2 in (
                        (stoparea1.id, stoparea2.id),
                        (stoparea2.id, stoparea1.id),
                    ):
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
