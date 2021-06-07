import shapely.geometry
import shapely.ops

from process_subways import download_cities


def make_disjoint_metro_polygons():
    cities = download_cities()

    polygons = []
    for c in cities:
        polygon = shapely.geometry.Polygon([
            (c.bbox[1], c.bbox[0]),
            (c.bbox[1], c.bbox[2]),
            (c.bbox[3], c.bbox[2]),
            (c.bbox[3], c.bbox[0]),
        ])
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


if __name__ == '__main__':
    make_disjoint_metro_polygons()
