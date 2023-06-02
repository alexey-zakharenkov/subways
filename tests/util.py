import io
from collections.abc import Sequence, Mapping
from operator import itemgetter
from pathlib import Path
from typing import Any
from unittest import TestCase as unittestTestCase

from process_subways import (
    add_osm_elements_to_cities,
    validate_cities,
    calculate_centers,
)
from subway_io import load_xml
from subway_structure import City, find_transfers


class TestCase(unittestTestCase):
    """TestCase class for testing the Subway Validator"""

    CITY_TEMPLATE = {
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

    @classmethod
    def setUpClass(cls) -> None:
        cls.city_class = City

    def prepare_cities(self, metro_sample: dict) -> tuple:
        """Load cities from file/string, validate them and return cities
        and transfers.
        """

        def assign_unique_id(city_info: dict, cities_info: list[dict]) -> None:
            """city_info - newly added city, cities_info - already added
            cities. Check city id uniqueness / assign unique id to the city.
            """
            occupied_ids = set(c["id"] for c in cities_info)
            if "id" in city_info:
                if city_info["id"] in occupied_ids:
                    raise RuntimeError("Not unique city ids in test data")
            else:
                city_info["id"] = max(occupied_ids, default=1) + 1

        cities_given_info = metro_sample["cities_info"]
        cities_info = list()
        for city_given_info in cities_given_info:
            city_info = self.CITY_TEMPLATE.copy()
            for attr in city_given_info.keys():
                city_info[attr] = city_given_info[attr]
            assign_unique_id(city_info, cities_info)
            cities_info.append(city_info)

        if len(set(ci["name"] for ci in cities_info)) < len(cities_info):
            raise RuntimeError("Not unique city names in test data")

        cities = list(map(self.city_class, cities_info))
        if "xml" in metro_sample:
            xml_file = io.BytesIO(metro_sample["xml"].encode())
        else:
            xml_file = (
                Path(__file__).resolve().parent / metro_sample["xml_file"]
            )
        elements = load_xml(xml_file)
        calculate_centers(elements)
        add_osm_elements_to_cities(elements, cities)
        validate_cities(cities)
        transfers = find_transfers(elements, cities)
        return cities, transfers

    def _assertAnyAlmostEqual(
        self,
        first: Any,
        second: Any,
        places: int = 10,
        ignore_keys: set = None,
    ) -> None:
        """Dispatcher method to other "...AlmostEqual" methods
        depending on argument types.
        """
        if isinstance(first, Mapping):
            self.assertMappingAlmostEqual(first, second, places, ignore_keys)
        elif isinstance(first, Sequence) and not isinstance(
            first, (str, bytes)
        ):
            self.assertSequenceAlmostEqual(first, second, places, ignore_keys)
        else:
            self.assertAlmostEqual(first, second, places)

    def assertSequenceAlmostEqual(
        self,
        seq1: Sequence,
        seq2: Sequence,
        places: int = 10,
        ignore_keys: set = None,
    ) -> None:
        """Compare two sequences, items of numeric types being compared
        approximately, containers being approx-compared recursively.

        :param: seq1  a sequence of values of any types, including collections
        :param: seq2  a sequence of values of any types, including collections
        :param: places  number of fractional digits (passed to
                assertAlmostEqual() method of parent class)
        :param: ignore_keys  a set of strs with keys in dictionaries
                that should be ignored during recursive comparison
        :return: None
        """
        if not (isinstance(seq1, Sequence) and isinstance(seq2, Sequence)):
            raise RuntimeError(
                f"Not a sequence passed to the '{self.__class__.__name__}."
                "assertSequenceAlmostEqual' method"
            )
        self.assertEqual(len(seq1), len(seq2))
        for a, b in zip(seq1, seq2):
            self._assertAnyAlmostEqual(a, b, places, ignore_keys)

    def assertMappingAlmostEqual(
        self,
        d1: Mapping,
        d2: Mapping,
        places: int = 10,
        ignore_keys: set = None,
    ) -> None:
        """Compare dictionaries recursively, numeric values being compared
        approximately.

        :param: d1  a mapping of arbitrary key/value types,
                including collections
        :param: d1  a mapping of arbitrary key/value types,
                including collections
        :param: places  number of fractional digits (passed to
                assertAlmostEqual() method of parent class)
        :param: ignore_keys  a set of strs with keys in dictionaries
                that should be ignored during recursive comparison
        :return: None
        """
        if not (isinstance(d1, Mapping) and isinstance(d2, Mapping)):
            raise RuntimeError(
                f"Not a dictionary passed to the '{self.__class__.__name__}."
                "assertMappingAlmostEqual' method"
            )

        d1_keys = set(d1.keys())
        d2_keys = set(d2.keys())
        if ignore_keys:
            d1_keys -= ignore_keys
            d2_keys -= ignore_keys
        self.assertSetEqual(d1_keys, d2_keys)
        for k in d1_keys:
            v1 = d1[k]
            v2 = d2[k]
            self._assertAnyAlmostEqual(v1, v2, places, ignore_keys)


class TestTransitDataMixin:
    def compare_transit_data(self, td1: dict, td2: dict) -> None:
        """Compare transit data td1 and td2 remembering that:
        - arrays that represent sets ("routes", "itineraries", "entrances")
          should be compared without order;
        - all floating-point values (coordinates) should be compared
          approximately.
        """
        self.assertMappingAlmostEqual(
            td1,
            td2,
            ignore_keys={"stopareas", "routes", "itineraries"},
        )

        networks1 = td1["networks"]
        networks2 = td2["networks"]

        id_cmp = itemgetter("id")

        for network_name, network_data1 in networks1.items():
            network_data2 = networks2[network_name]
            routes1 = sorted(network_data1["routes"], key=id_cmp)
            routes2 = sorted(network_data2["routes"], key=id_cmp)
            self.assertEqual(len(routes1), len(routes2))
            for r1, r2 in zip(routes1, routes2):
                self.assertMappingAlmostEqual(
                    r1, r2, ignore_keys={"itineraries"}
                )
                its1 = sorted(r1["itineraries"], key=id_cmp)
                its2 = sorted(r2["itineraries"], key=id_cmp)
                self.assertEqual(len(its1), len(its2))
                for it1, it2 in zip(its1, its2):
                    self.assertMappingAlmostEqual(it1, it2)

        transfers1 = td1["transfers"]
        transfers2 = td2["transfers"]
        self.assertSetEqual(transfers1, transfers2)

        stopareas1 = td1["stopareas"]
        stopareas2 = td2["stopareas"]
        self.assertMappingAlmostEqual(
            stopareas1, stopareas2, ignore_keys={"entrances"}
        )

        for sa_id, sa1_data in stopareas1.items():
            sa2_data = stopareas2[sa_id]
            entrances1 = sorted(sa1_data["entrances"], key=id_cmp)
            entrances2 = sorted(sa2_data["entrances"], key=id_cmp)
            self.assertEqual(len(entrances1), len(entrances2))
            for e1, e2 in zip(entrances1, entrances2):
                self.assertMappingAlmostEqual(e1, e2)
