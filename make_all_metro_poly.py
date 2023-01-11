import argparse

import shapely.geometry
import shapely.ops

from process_subways import DEFAULT_CITIES_INFO_URL, get_cities_info


def make_disjoint_metro_polygons(cities_info_url: str) -> None:
    cities_info = get_cities_info(cities_info_url)

    polygons = []
    for ci in cities_info:
        bbox = tuple(map(float, ci["bbox"].split(",")))
        polygon = shapely.geometry.Polygon(
            [
                (bbox[0], bbox[1]),
                (bbox[0], bbox[3]),
                (bbox[2], bbox[3]),
                (bbox[2], bbox[1]),
            ]
        )
        polygons.append(polygon)

    union = shapely.ops.unary_union(polygons)

    print("all metro")
    for i, polygon in enumerate(union, start=1):
        assert len(polygon.interiors) == 0
        print(i)
        for point in polygon.exterior.coords:
            print("  {lon} {lat}".format(lon=point[0], lat=point[1]))
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
