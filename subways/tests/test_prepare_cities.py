import inspect
from pathlib import Path
from unittest import TestCase

from subways.validation import prepare_cities


class TestPrepareCities(TestCase):
    def test_prepare_cities(self) -> None:
        csv_path = (
            Path(inspect.getfile(self.__class__)).parent
            / "assets"
            / "cities_info_with_bad_values.csv"
        )

        cities = prepare_cities(cities_info_urls=[f"file://{csv_path}"])

        city_errors = {city.name: sorted(city.errors) for city in cities}

        expected_errors = {
            "Kazan": [
                "Configuration error: wrong value for bbox: "
                "48.933,55.65,49.297"
            ],
            "Nizhny Novgorod": [],
            "Omsk": [
                "Configuration error: wrong value for bbox: "
                "73.2,54.9,73.6,55.1x"
            ],
            "Perm": [
                "Configuration error: wrong value for bbox: "
                "56.0,57.9,561.0,58.1"
            ],
            "Rostov": [
                "Configuration error: wrong value for bbox: "
                "39.5,nan,39.9,47.4"
            ],
            "Novosibirsk": ["Configuration error: wrong value for id: NBS"],
            "Saint Petersburg": [],
            "Samara": [
                "Configuration error: wrong value for num_stations: 10x"
            ],
            "Volgograd": [
                "Configuration error: wrong value for num_light_lines: 2zero",
                "Configuration error: wrong value for num_lines: zero",
            ],
            "Yekaterinburg": [
                "Configuration error: wrong value for num_stations: <empty>"
            ],
        }

        self.assertDictEqual(city_errors, expected_errors)

        bboxes = {city.name: city.bbox for city in cities}
        self.assertIsNone(bboxes["Kazan"])
        self.assertIsNone(bboxes["Omsk"])
        self.assertIsNone(bboxes["Perm"])
        self.assertIsNone(bboxes["Rostov"])
        self.assertListEqual(
            bboxes["Saint Petersburg"], [59.7509, 30.0648, 60.1292, 30.5976]
        )
