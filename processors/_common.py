from typing import List, Set

from subway_structure import City, el_center, StopArea

DEFAULT_INTERVAL = 2.5 * 60  # seconds
KMPH_TO_MPS = 1 / 3.6  # km/h to m/s conversion multiplier
SPEED_ON_TRANSFER = 3.5 * KMPH_TO_MPS  # m/s
TRANSFER_PENALTY = 30  # seconds


def format_colour(colour):
    """Truncate leading # sign."""
    return colour[1:] if colour else None


def transit_to_dict(
    cities: List[City], transfers: List[Set[StopArea]]
) -> dict:
    """Get data for good cities as a dictionary."""
    data = {
        "stopareas": {},  # stoparea id => stoparea data
        "networks": {},  # city name => city data
        "transfers": {},  # set(tuple(stoparea_id1, stoparea_id2)), id1<id2
    }

    for city in (c for c in cities if c.is_good):
        network = {
            "id": city.id,
            "name": city.name,
            "routes": [],
        }

        for route_master in city:
            route_data = {
                "id": route_master.id,
                "mode": route_master.mode,
                "ref": route_master.ref,
                "name": route_master.name,
                "colour": route_master.colour,
                "infill": route_master.infill,
                "itineraries": [],
            }

            for route in route_master:
                variant_data = {
                    "id": route.id,
                    "tracks": route.get_tracks_geometry(),
                    "start_time": route.start_time,
                    "end_time": route.end_time,
                    "interval": route.interval,
                    "stops": [
                        {
                            "stoparea_id": route_stop.stoparea.id,
                            "distance": route_stop.distance,
                        }
                        for route_stop in route.stops
                    ],
                }

                # Store stopareas participating in the route
                # and that have not been stored yet
                for route_stop in route.stops:
                    stoparea = route_stop.stoparea
                    if stoparea.id in data["stopareas"]:
                        continue
                    stoparea_data = {
                        "id": stoparea.id,
                        "center": stoparea.center,
                        "name": stoparea.station.name,
                        "entrances": [
                            {
                                "id": egress_id,
                                "name": egress["tags"].get("name"),
                                "ref": egress["tags"].get("ref"),
                                "center": el_center(egress),
                            }
                            for (egress_id, egress) in (
                                (egress_id, city.elements[egress_id])
                                for egress_id in stoparea.entrances
                                | stoparea.exits
                            )
                        ],
                    }
                    data["stopareas"][stoparea.id] = stoparea_data

                route_data["itineraries"].append(variant_data)

            network["routes"].append(route_data)

        data["networks"][city.name] = network

    # transfers
    pairwise_transfers = set()
    for stoparea_id_set in transfers:
        stoparea_ids = sorted(stoparea_id_set)
        for first_i in range(len(stoparea_ids) - 1):
            for second_i in range(first_i + 1, len(stoparea_ids)):
                stoparea1_id = stoparea_ids[first_i]
                stoparea2_id = stoparea_ids[second_i]
                if all(
                    st_id in data["stopareas"]
                    for st_id in (stoparea1_id, stoparea2_id)
                ):
                    pairwise_transfers.add((stoparea1_id, stoparea2_id))

    data["transfers"] = pairwise_transfers
    return data
