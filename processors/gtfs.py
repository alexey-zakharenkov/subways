import csv
from functools import partial
from io import BytesIO, StringIO
from itertools import permutations
from tarfile import TarFile, TarInfo
from typing import List, Optional, Set
from zipfile import ZipFile

from ._common import (
    DEFAULT_INTERVAL,
    format_colour,
    SPEED_ON_TRANSFER,
    TRANSFER_PENALTY,
    transit_to_dict,
)
from subway_structure import (
    City,
    distance,
    StopArea,
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


def round_coords(coords_tuple):
    return tuple(
        map(lambda coord: round(coord, COORDINATE_PRECISION), coords_tuple)
    )


def transit_data_to_gtfs(data):
    # Keys correspond GTFS file names
    gtfs_data = {key: [] for key in GTFS_COLUMNS.keys()}

    # GTFS calendar
    gtfs_data["calendar"].append(
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
        }
    )

    # GTFS stops
    for stoparea_id, stoparea_data in data["stopareas"].items():
        station_id = f"{stoparea_id}_st"
        station_name = stoparea_data["name"]
        station_center = round_coords(stoparea_data["center"])
        station_gtfs = {
            "stop_id": station_id,
            "stop_code": station_id,
            "stop_name": station_name,
            "stop_lat": station_center[1],
            "stop_lon": station_center[0],
            "location_type": 1,  # station in GTFS terms
        }
        gtfs_data["stops"].append(station_gtfs)

        platform_id = f"{stoparea_id}_plt"
        platform_gtfs = {
            "stop_id": platform_id,
            "stop_code": platform_id,
            "stop_name": station_name,
            "stop_lat": station_center[1],
            "stop_lon": station_center[0],
            "location_type": 0,  # stop/platform in GTFS terms
            "parent_station": station_id,
        }
        gtfs_data["stops"].append(platform_gtfs)

        if not stoparea_data["entrances"]:
            entrance_id = f"{stoparea_id}_egress"
            entrance_gtfs = {
                "stop_id": entrance_id,
                "stop_code": entrance_id,
                "stop_name": station_name,
                "stop_lat": station_center[1],
                "stop_lon": station_center[0],
                "location_type": 2,
                "parent_station": station_id,
            }
            gtfs_data["stops"].append(entrance_gtfs)
        else:
            for entrance in stoparea_data["entrances"]:
                entrance_id = f"{entrance['id']}_{stoparea_id}"
                entrance_name = entrance["name"]
                if not entrance["name"]:
                    entrance_name = station_name
                    ref = entrance["ref"]
                    if ref:
                        entrance_name += f" {ref}"
                center = round_coords(entrance["center"])
                entrance_gtfs = {
                    "stop_id": entrance_id,
                    "stop_code": entrance_id,
                    "stop_name": entrance_name,
                    "stop_lat": center[1],
                    "stop_lon": center[0],
                    "location_type": 2,
                    "parent_station": station_id,
                }
                gtfs_data["stops"].append(entrance_gtfs)

    # agency, routes, trips, stop_times, frequencies, shapes
    for network in data["networks"].values():
        agency = {
            "agency_id": network["id"],
            "agency_name": network["name"],
        }
        gtfs_data["agency"].append(agency)

        for route_master in network["routes"]:
            route = {
                "route_id": route_master["id"],
                "agency_id": network["id"],
                "route_type": 12 if route_master["mode"] == "monorail" else 1,
                "route_short_name": route_master["ref"],
                "route_long_name": route_master["name"],
                "route_color": format_colour(route_master["colour"]),
            }
            gtfs_data["routes"].append(route)

            for itinerary in route_master["itineraries"]:
                shape_id = itinerary["id"][1:]  # truncate leading 'r'
                trip = {
                    "trip_id": itinerary["id"],
                    "route_id": route_master["id"],
                    "service_id": "always",
                    "shape_id": shape_id,
                }
                gtfs_data["trips"].append(trip)

                for i, (lon, lat) in enumerate(itinerary["tracks"]):
                    lon, lat = round_coords((lon, lat))
                    gtfs_data["shapes"].append(
                        {
                            "shape_id": shape_id,
                            "trip_id": itinerary["id"],
                            "shape_pt_lat": lat,
                            "shape_pt_lon": lon,
                            "shape_pt_sequence": i,
                        }
                    )

                start_time = itinerary["start_time"] or DEFAULT_TRIP_START_TIME
                end_time = itinerary["end_time"] or DEFAULT_TRIP_END_TIME
                if end_time <= start_time:
                    end_time = (end_time[0] + 24, end_time[1])
                start_time = f"{start_time[0]:02d}:{start_time[1]:02d}:00"
                end_time = f"{end_time[0]:02d}:{end_time[1]:02d}:00"

                gtfs_data["frequencies"].append(
                    {
                        "trip_id": itinerary["id"],
                        "start_time": start_time,
                        "end_time": end_time,
                        "headway_secs": itinerary["interval"]
                        or DEFAULT_INTERVAL,
                    }
                )

                for i, route_stop in enumerate(itinerary["stops"]):
                    platform_id = f"{route_stop['stoparea_id']}_plt"

                    gtfs_data["stop_times"].append(
                        {
                            "trip_id": itinerary["id"],
                            "stop_sequence": i,
                            "shape_dist_traveled": route_stop["distance"],
                            "stop_id": platform_id,
                        }
                    )

    # transfers
    for stoparea1_id, stoparea2_id in data["transfers"]:
        stoparea1 = data["stopareas"][stoparea1_id]
        stoparea2 = data["stopareas"][stoparea2_id]
        transfer_time = TRANSFER_PENALTY + round(
            distance(stoparea1["center"], stoparea2["center"])
            / SPEED_ON_TRANSFER
        )
        gtfs_sa_id1 = f"{stoparea1['id']}_st"
        gtfs_sa_id2 = f"{stoparea2['id']}_st"
        for id1, id2 in permutations((gtfs_sa_id1, gtfs_sa_id2)):
            gtfs_data["transfers"].append(
                {
                    "from_stop_id": id1,
                    "to_stop_id": id2,
                    "transfer_type": 0,
                    "min_transfer_time": transfer_time,
                }
            )

    return gtfs_data


def process(
    cities: List[City],
    transfers: List[Set[StopArea]],
    filename: str,
    cache_path: str,
):
    """Generate all output and save to file.
    :param cities: List of City instances
    :param transfers: List of sets of StopArea.id
    :param filename: Path to file to save the result
    :param cache_path: Path to json-file with good cities cache or None.
    """

    transit_data = transit_to_dict(cities, transfers)
    gtfs_data = transit_data_to_gtfs(transit_data)

    # TODO: make universal cache for all processors,
    #       and apply the cache to GTFS

    make_gtfs(filename, gtfs_data)


def dict_to_row(dict_data: dict, record_type: str) -> list:
    """Given object stored in a dict and an array of columns,
    return a row to use in CSV.
    """
    return [
        "" if (v := dict_data.get(column)) is None else v
        for column in GTFS_COLUMNS[record_type]
    ]


def make_gtfs(
    filename: str, gtfs_data: dict, fmt: Optional[str] = None
) -> None:
    if not fmt:
        fmt = "tar" if filename.endswith(".tar") else "zip"

    if fmt == "zip":
        make_gtfs_zip(filename, gtfs_data)
    else:
        make_gtfs_tar(filename, gtfs_data)


def make_gtfs_zip(filename: str, gtfs_data: dict) -> None:
    if not filename.lower().endswith(".zip"):
        filename = f"{filename}.zip"

    with ZipFile(filename, "w") as zf:
        for gtfs_feature, columns in GTFS_COLUMNS.items():
            with StringIO(newline="") as string_io:
                writer = csv.writer(string_io, delimiter=",")
                writer.writerow(columns)
                writer.writerows(
                    map(
                        partial(dict_to_row, record_type=gtfs_feature),
                        gtfs_data[gtfs_feature],
                    )
                )
                zf.writestr(f"{gtfs_feature}.txt", string_io.getvalue())


def make_gtfs_tar(filename: str, gtfs_data: dict) -> None:
    if not filename.lower().endswith(".tar"):
        filename = f"{filename}.tar"

    with TarFile(filename, "w") as tf:
        for gtfs_feature, columns in GTFS_COLUMNS.items():
            with StringIO(newline="") as string_io:
                writer = csv.writer(string_io, delimiter=",")
                writer.writerow(columns)
                writer.writerows(
                    map(
                        partial(dict_to_row, record_type=gtfs_feature),
                        gtfs_data[gtfs_feature],
                    )
                )
                tarinfo = TarInfo(f"{gtfs_feature}.txt")
                data = string_io.getvalue().encode()
                tarinfo.size = len(data)
                tf.addfile(tarinfo, BytesIO(data))
