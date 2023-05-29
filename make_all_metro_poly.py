import argparse

from shapely import unary_union
from shapely.geometry import MultiPolygon, Polygon

from process_subways import DEFAULT_CITIES_INFO_URL, get_cities_info


def make_disjoint_metro_polygons(cities_info_url: str) -> None:
    """Make disjoint polygon from cities bboxes and write them
    in *.poly format to stdout.
    """
    cities_info = get_cities_info(cities_info_url)

    polygons = []
    for ci in cities_info:
        bbox = tuple(map(float, ci["bbox"].split(",")))
        polygon = Polygon(
            [
                (bbox[0], bbox[1]),
                (bbox[0], bbox[3]),
                (bbox[2], bbox[3]),
                (bbox[2], bbox[1]),
            ]
        )
        polygons.append(polygon)

    union = unary_union(polygons)

    if union.geom_type == "Polygon":
        union = MultiPolygon([union])

    print("all metro")
    for i, polygon in enumerate(union.geoms, start=1):
        assert len(polygon.interiors) == 0
        print(i)
        for lon, lat in polygon.exterior.coords:
            print(f"  {lon} {lat}")
        print("END")
    print("END")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cities-info-url",
        default=DEFAULT_CITIES_INFO_URL,
        help=(
            "URL of CSV file with reference information about rapid transit "
            "networks. file:// protocol is also supported."
        ),
    )
    options = parser.parse_args()
    make_disjoint_metro_polygons(options.cities_info_url)


if __name__ == "__main__":
    main()
