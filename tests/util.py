import io
from unittest import TestCase as unittestTestCase

from subway_io import load_xml
from subway_structure import City


class TestCase(unittestTestCase):
    """TestCase class for testing the Subway Validator"""

    CITY_TEMPLATE = {
        "id": 1,
        "name": "Null Island",
        "country": "World",
        "continent": "Africa",
        "bbox": "-179, -89, 179, 89",
        "networks": "",
        "num_stations": None,
        "num_lines": 1,
        "num_light_lines": 0,
        "num_interchanges": 0,
    }

    def validate_city(self, network) -> City:
        city_data = self.CITY_TEMPLATE.copy()
        for attr in self.CITY_TEMPLATE.keys():
            if attr in network:
                city_data[attr] = network[attr]

        city = City(city_data)
        elements = load_xml(io.BytesIO(network["xml"].encode("utf-8")))
        for el in elements:
            city.add(el)
        city.extract_routes()
        city.validate()
        return city

    def assertListAlmostEqual(self, list1, list2, places=10) -> None:
        if not (isinstance(list1, list) and isinstance(list2, list)):
            raise RuntimeError(
                f"Not lists passed to the '{self.__class__.__name__}."
                "assertListAlmostEqual' method"
            )
        self.assertEqual(len(list1), len(list2))
        for a, b in zip(list1, list2):
            if isinstance(a, list) and isinstance(b, list):
                self.assertListAlmostEqual(a, b, places)
            else:
                self.assertAlmostEqual(a, b, places)
