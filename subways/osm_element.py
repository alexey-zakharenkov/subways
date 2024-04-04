from subways.types import IdT, LonLat, OsmElementT


def el_id(el: OsmElementT) -> IdT | None:
    if not el:
        return None
    if "type" not in el:
        raise Exception("What is this element? {}".format(el))
    return el["type"][0] + str(el.get("id", el.get("ref", "")))


def el_center(el: OsmElementT) -> LonLat | None:
    if not el:
        return None
    if "lat" in el:
        return el["lon"], el["lat"]
    elif "center" in el:
        return el["center"]["lon"], el["center"]["lat"]
    return None


def get_network(relation: OsmElementT) -> str | None:
    for k in ("network:metro", "network", "operator"):
        if k in relation["tags"]:
            return relation["tags"][k]
    return None
