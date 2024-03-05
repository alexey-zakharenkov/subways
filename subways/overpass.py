import json
import logging
import time
import urllib.parse
import urllib.request

from subways.consts import MODES_OVERGROUND, MODES_RAPID
from subways.types import OsmElementT


def compose_overpass_request(
    overground: bool, bboxes: list[list[float]]
) -> str:
    if not bboxes:
        raise RuntimeError("No bboxes given for overpass request")

    query = "[out:json][timeout:1000];("
    modes = MODES_OVERGROUND if overground else MODES_RAPID
    for bbox in bboxes:
        bbox_part = f"({','.join(str(coord) for coord in bbox)})"
        query += "("
        for mode in sorted(modes):
            query += f'rel[route="{mode}"]{bbox_part};'
        query += ");"
        query += "rel(br)[type=route_master];"
        if not overground:
            query += f"node[railway=subway_entrance]{bbox_part};"
            query += f"node[railway=train_station_entrance]{bbox_part};"
        query += f"rel[public_transport=stop_area]{bbox_part};"
        query += (
            "rel(br)[type=public_transport][public_transport=stop_area_group];"
        )
    query += ");(._;>>;);out body center qt;"
    logging.debug("Query: %s", query)
    return query


def overpass_request(
    overground: bool, overpass_api: str, bboxes: list[list[float]]
) -> list[OsmElementT]:
    query = compose_overpass_request(overground, bboxes)
    url = f"{overpass_api}?data={urllib.parse.quote(query)}"
    response = urllib.request.urlopen(url, timeout=1000)
    if (r_code := response.getcode()) != 200:
        raise Exception(f"Failed to query Overpass API: HTTP {r_code}")
    return json.load(response)["elements"]


def multi_overpass(
    overground: bool, overpass_api: str, bboxes: list[list[float]]
) -> list[OsmElementT]:
    SLICE_SIZE = 10
    INTERREQUEST_WAIT = 5  # in seconds
    result = []
    for i in range(0, len(bboxes), SLICE_SIZE):
        if i > 0:
            time.sleep(INTERREQUEST_WAIT)
        bboxes_i = bboxes[i : i + SLICE_SIZE]  # noqa E203
        result.extend(overpass_request(overground, overpass_api, bboxes_i))
    return result
