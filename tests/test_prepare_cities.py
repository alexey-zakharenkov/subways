import inspect
from pathlib import Path
from unittest import TestCase

from process_subways import prepare_cities


class TestPrepareCities(TestCase):
    def test_prepare_cities(self) -> None:
        csv_path = (
            Path(inspect.getfile(self.__class__)).parent
            / "assets"
            / "cities_info_with_bad_values.csv"
        )

        cities = prepare_cities(cities_info_url=f"file://{csv_path}")

        city_errors = {city.name: sorted(city.errors) for city in cities}

        expected_errors = {
            "Nizhny Novgorod": [],
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
