import random
from unittest import TestCase

from subways.osm_element import el_id
from subways.structure.city import City
from subways.validation import add_osm_elements_to_cities


def make_city(name: str, bbox: str) -> City:
    return City(
        {
            "id": "1",
            "name": name,
            "country": "Country",
            "continent": "Continent",
            "num_stations": "1",
            "num_lines": "1",
            "num_light_lines": "0",
            "num_interchanges": "0",
            "bbox": bbox,
            "networks": "",
        }
    )


def node(node_id: int, lon: float, lat: float) -> dict:
    return {"type": "node", "id": node_id, "lon": lon, "lat": lat}


class TestAddOsmElementsToCities(TestCase):
    def test_edge_cases(self) -> None:
        # bbox in CSV order: lon_min,lat_min,lon_max,lat_max
        london = make_city("London", "-0.9747,51.1186,0.3315,51.8459")
        # Spans several grid cells
        moscow = make_city("Moscow", "37.1667,55.3869,38.2626,56.0136")
        # Overlaps with Moscow
        zelenograd = make_city("Zelenograd", "37.1,55.9,37.3,56.1")
        # Negative lat and lon: grid cells must be computed with floor(),
        # not int() which rounds towards zero
        santiago = make_city("Santiago", "-70.8,-33.6,-70.5,-33.3")
        # Bbox edges exactly on grid cell boundaries
        integer = make_city("Integer", "10,20,11,21")
        # Crosses the antimeridian: not supported by City.contains(),
        # so nothing should be added, but nothing should fail either
        fiji = make_city("Fiji", "177,-19,-179,-16")
        bad = make_city("Bad", "1,2,3")

        elements = [
            node(1, 0.0, 51.5),  # London, negative/positive lon boundary
            node(2, -0.5, 51.5),  # London, negative lon
            node(3, -0.9747, 51.1186),  # London, exactly on the corner
            node(4, 0.3315, 51.8459),  # London, exactly on the corner
            node(5, 0.3316, 51.5),  # just outside London
            node(6, 38.0, 55.5),  # Moscow, not in the first grid cell
            node(7, 37.2, 55.95),  # Moscow and Zelenograd
            node(8, 2.0, 3.0),  # nowhere, although inside "Bad" area
            {"type": "way", "id": 9, "nodes": [1, 2]},  # no center
            {
                "type": "relation",
                "id": 10,
                "members": [],
                "center": {"lon": 37.5, "lat": 55.7},
            },  # Moscow, center from "center" attribute
            node(11, -70.65, -33.45),  # Santiago
            node(12, 10.0, 20.0),  # Integer, exactly on the corner
            node(13, 11.0, 21.0),  # Integer, exactly on the opposite corner
            node(14, 11.0, 21.001),  # just outside Integer
            node(15, 178.0, -17.5),  # inside Fiji area, but not added
            node(16, -179.5, -17.5),  # inside Fiji area, but not added
        ]
        cities = [
            london,
            moscow,
            zelenograd,
            santiago,
            integer,
            fiji,
            bad,
        ]
        add_osm_elements_to_cities(elements, cities)

        self.assertListEqual(list(london.elements), ["n1", "n2", "n3", "n4"])
        self.assertListEqual(list(moscow.elements), ["n6", "n7", "r10"])
        self.assertListEqual(list(zelenograd.elements), ["n7"])
        self.assertListEqual(list(santiago.elements), ["n11"])
        self.assertListEqual(list(integer.elements), ["n12", "n13"])
        self.assertListEqual(list(fiji.elements), [])
        self.assertListEqual(list(bad.elements), [])

    def test_same_as_brute_force(self) -> None:
        rnd = random.Random(1)
        bboxes = []
        for _ in range(50):
            lon = rnd.uniform(-180, 178)
            lat = rnd.uniform(-85, 83)
            bboxes.append(
                f"{lon},{lat},"
                f"{lon + rnd.uniform(0, 2)},{lat + rnd.uniform(0, 2)}"
            )

        elements = []
        for i in range(5000):
            if i % 2:
                lon_min, lat_min, lon_max, lat_max = map(
                    float, rnd.choice(bboxes).split(",")
                )
                lon = rnd.uniform(lon_min - 0.1, lon_max + 0.1)
                lat = rnd.uniform(lat_min - 0.1, lat_max + 0.1)
            else:
                lon = rnd.uniform(-180, 180)
                lat = rnd.uniform(-85, 85)
            elements.append(node(i, lon, lat))

        cities = [make_city(f"City {i}", b) for i, b in enumerate(bboxes)]
        add_osm_elements_to_cities(elements, cities)

        for city in cities:
            expected = [el_id(el) for el in elements if city.contains(el)]
            self.assertListEqual(
                list(city.elements),
                expected,
                msg=f"{city.name}, bbox (lat, lon): {city.bbox}",
            )
