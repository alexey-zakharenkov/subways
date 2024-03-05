import csv
import logging
import urllib.request
from functools import partial

from subways.structure.city import City
from subways.types import CriticalValidationError, LonLat, OsmElementT

DEFAULT_SPREADSHEET_ID = "1SEW1-NiNOnA2qDwievcxYV1FOaQl1mb1fdeyqAxHu3k"
DEFAULT_CITIES_INFO_URL = (
    "https://docs.google.com/spreadsheets/d/"
    f"{DEFAULT_SPREADSHEET_ID}/export?format=csv"
)
BAD_MARK = "[bad]"


def get_way_center(
    element: OsmElementT, node_centers: dict[int, LonLat]
) -> LonLat | None:
    """
    :param element: dict describing OSM element
    :param node_centers: osm_id => LonLat
    :return: tuple with center coordinates, or None
    """

    # If elements have been queried via overpass-api with
    # 'out center;' clause then ways already have 'center' attribute
    if "center" in element:
        return element["center"]["lon"], element["center"]["lat"]

    if "nodes" not in element:
        return None

    center = [0, 0]
    count = 0
    way_nodes = element["nodes"]
    way_nodes_len = len(element["nodes"])
    for i, nd in enumerate(way_nodes):
        if nd not in node_centers:
            continue
        # Don't count the first node of a closed way twice
        if (
            i == way_nodes_len - 1
            and way_nodes_len > 1
            and way_nodes[0] == way_nodes[-1]
        ):
            break
        center[0] += node_centers[nd][0]
        center[1] += node_centers[nd][1]
        count += 1
    if count == 0:
        return None
    element["center"] = {"lat": center[1] / count, "lon": center[0] / count}
    return element["center"]["lon"], element["center"]["lat"]


def get_relation_center(
    element: OsmElementT,
    node_centers: dict[int, LonLat],
    way_centers: dict[int, LonLat],
    relation_centers: dict[int, LonLat],
    ignore_unlocalized_child_relations: bool = False,
) -> LonLat | None:
    """
    :param element: dict describing OSM element
    :param node_centers: osm_id => LonLat
    :param way_centers: osm_id => LonLat
    :param relation_centers: osm_id => LonLat
    :param ignore_unlocalized_child_relations: if a member that is a relation
        has no center, skip it and calculate center based on member nodes,
        ways and other, "localized" (with known centers), relations
    :return: tuple with center coordinates, or None
    """

    # If elements have been queried via overpass-api with
    # 'out center;' clause then some relations already have 'center'
    # attribute. But this is not the case for relations composed only
    # of other relations (e.g., route_master, stop_area_group or
    # stop_area with only members that are multipolygons)
    if "center" in element:
        return element["center"]["lon"], element["center"]["lat"]

    center = [0, 0]
    count = 0
    for m in element.get("members", list()):
        m_id = m["ref"]
        m_type = m["type"]
        if m_type == "relation" and m_id not in relation_centers:
            if ignore_unlocalized_child_relations:
                continue
            else:
                # Cannot calculate fair center because the center
                # of a child relation is not known yet
                return None
        member_container = (
            node_centers
            if m_type == "node"
            else way_centers
            if m_type == "way"
            else relation_centers
        )
        if m_id in member_container:
            center[0] += member_container[m_id][0]
            center[1] += member_container[m_id][1]
            count += 1
    if count == 0:
        return None
    element["center"] = {"lat": center[1] / count, "lon": center[0] / count}
    return element["center"]["lon"], element["center"]["lat"]


def calculate_centers(elements: list[OsmElementT]) -> None:
    """Adds 'center' key to each way/relation in elements,
    except for empty ways or relations.
    Relies on nodes-ways-relations order in the elements list.
    """
    nodes: dict[int, LonLat] = {}  # id => LonLat
    ways: dict[int, LonLat] = {}  # id => approx center LonLat
    relations: dict[int, LonLat] = {}  # id => approx center LonLat

    unlocalized_relations: list[OsmElementT] = []  # 'unlocalized' means
    # the center of the relation has not been calculated yet

    for el in elements:
        if el["type"] == "node":
            nodes[el["id"]] = (el["lon"], el["lat"])
        elif el["type"] == "way":
            if center := get_way_center(el, nodes):
                ways[el["id"]] = center
        elif el["type"] == "relation":
            if center := get_relation_center(el, nodes, ways, relations):
                relations[el["id"]] = center
            else:
                unlocalized_relations.append(el)

    def iterate_relation_centers_calculation(
        ignore_unlocalized_child_relations: bool,
    ) -> list[OsmElementT]:
        unlocalized_relations_upd = []
        for rel in unlocalized_relations:
            if center := get_relation_center(
                rel, nodes, ways, relations, ignore_unlocalized_child_relations
            ):
                relations[rel["id"]] = center
            else:
                unlocalized_relations_upd.append(rel)
        return unlocalized_relations_upd

    # Calculate centers for relations that have no one yet
    while unlocalized_relations:
        unlocalized_relations_upd = iterate_relation_centers_calculation(False)
        progress = len(unlocalized_relations_upd) < len(unlocalized_relations)
        if not progress:
            unlocalized_relations_upd = iterate_relation_centers_calculation(
                True
            )
            progress = len(unlocalized_relations_upd) < len(
                unlocalized_relations
            )
            if not progress:
                break
        unlocalized_relations = unlocalized_relations_upd


def add_osm_elements_to_cities(
    osm_elements: list[OsmElementT], cities: list[City]
) -> None:
    for el in osm_elements:
        for c in cities:
            if c.contains(el):
                c.add(el)


def validate_cities(cities: list[City]) -> list[City]:
    """Validate cities. Return list of good cities."""
    good_cities = []
    for c in cities:
        try:
            c.extract_routes()
        except CriticalValidationError as e:
            logging.error(
                "Critical validation error while processing %s: %s",
                c.name,
                e,
            )
            c.error(str(e))
        except AssertionError as e:
            logging.error(
                "Validation logic error while processing %s: %s",
                c.name,
                e,
            )
            c.error(f"Validation logic error: {e}")
        else:
            c.validate()
            if c.is_good:
                c.calculate_distances()
                good_cities.append(c)

    return good_cities


def get_cities_info(
    cities_info_url: str = DEFAULT_CITIES_INFO_URL,
) -> list[dict]:
    response = urllib.request.urlopen(cities_info_url)
    if (
        not cities_info_url.startswith("file://")
        and (r_code := response.getcode()) != 200
    ):
        raise Exception(
            f"Failed to download cities spreadsheet: HTTP {r_code}"
        )
    data = response.read().decode("utf-8")
    reader = csv.DictReader(
        data.splitlines(),
        fieldnames=(
            "id",
            "name",
            "country",
            "continent",
            "num_stations",
            "num_lines",
            "num_light_lines",
            "num_interchanges",
            "bbox",
            "networks",
        ),
    )

    cities_info = list()
    names = set()
    next(reader)  # skipping the header
    for city_info in reader:
        if city_info["id"] and city_info["bbox"]:
            cities_info.append(city_info)
            name = city_info["name"].strip()
            if name in names:
                logging.warning(
                    "Duplicate city name in city list: %s",
                    city_info,
                )
            names.add(name)
    return cities_info


def prepare_cities(
    cities_info_url: str = DEFAULT_CITIES_INFO_URL, overground: bool = False
) -> list[City]:
    if overground:
        raise NotImplementedError("Overground transit not implemented yet")
    cities_info = get_cities_info(cities_info_url)
    return list(map(partial(City, overground=overground), cities_info))
