import io
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, TypeAlias, Self
from unittest import TestCase as unittestTestCase

from subways.structure.city import City, find_transfers
from subways.subway_io import load_xml
from subways.validation import (
    add_osm_elements_to_cities,
    validate_cities,
    calculate_centers,
)

TestCaseMixin: TypeAlias = Self | unittestTestCase


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


class JsonLikeComparisonMixin:
    """Contains auxiliary methods for the TestCase class that allow
    to compare json-like structures where some lists do not imply order
    and actually represent sets.
    Also, all collections compare floats with given precision to any nesting
    depth.
    """

    def _assertAnyAlmostEqual(
        self: TestCaseMixin,
        first: Any,
        second: Any,
        places: int = 10,
        *,
        unordered_lists: dict[str, Callable] | None = None,
        ignore_keys: set[str] | None = None,
    ) -> None:
        """Dispatcher method to other "...AlmostEqual" methods
        depending on argument types.

        Compare dictionaries/lists recursively, numeric values being compared
        approximately.

        :param: first  a value of arbitrary type, including collections
        :param: second  a value of arbitrary type, including collections
        :param: places  number of fractional digits. Is passed to
                the self.assertAlmostEqual() method.
        :param: unordered_lists  a dict whose keys are names of lists
                to be compared without order, values - comparators for
                the lists to sort them in an unambiguous order. If a comparator
                is None, then the lists are compared as sets.
        :param: ignore_keys  a set of strs with keys that should be ignored
                during recursive comparison of dictionaries. May be used to
                elaborate a custom comparison mechanism for some substructures.
        :return: None
        """
        if all(isinstance(x, Mapping) for x in (first, second)):
            self.assertMappingAlmostEqual(
                first,
                second,
                places,
                unordered_lists=unordered_lists,
                ignore_keys=ignore_keys,
            )
        elif all(
            isinstance(x, Sequence) and not isinstance(x, (str, bytes))
            for x in (first, second)
        ):
            self.assertSequenceAlmostEqual(
                first,
                second,
                places,
                unordered_lists=unordered_lists,
                ignore_keys=ignore_keys,
            )
        elif isinstance(first, float) and isinstance(second, float):
            self.assertAlmostEqual(first, second, places)
        else:
            self.assertEqual(first, second)

    def assertSequenceAlmostEqual(
        self: TestCaseMixin,
        seq1: Sequence,
        seq2: Sequence,
        places: int = 10,
        *,
        unordered_lists: dict[str, Callable] | None = None,
        ignore_keys: set[str] | None = None,
    ) -> None:
        """Compare two sequences, items of numeric types being compared
        approximately, containers being approx-compared recursively.

        :param: places  see _assertAnyAlmostEqual() method
        :param: unordered_lists  see _assertAnyAlmostEqual() method
        :param: ignore_keys  see _assertAnyAlmostEqual() method
        :return: None
        """
        if not (isinstance(seq1, Sequence) and isinstance(seq2, Sequence)):
            raise RuntimeError(
                f"Not a sequence passed to the '{self.__class__.__name__}."
                "assertSequenceAlmostEqual' method"
            )
        self.assertEqual(len(seq1), len(seq2))
        for a, b in zip(seq1, seq2):
            self._assertAnyAlmostEqual(
                a,
                b,
                places,
                unordered_lists=unordered_lists,
                ignore_keys=ignore_keys,
            )

    def assertSequenceAlmostEqualIgnoreOrder(
        self: TestCaseMixin,
        seq1: Sequence,
        seq2: Sequence,
        cmp: Callable | None = None,
        places: int = 10,
        *,
        unordered_lists: dict[str, Callable] | None = None,
        ignore_keys: set[str] | None = None,
    ) -> None:
        """Compares two sequences as sets, i.e. ignoring order. Nested
        lists determined with unordered_lists parameter are also compared
        without order.

        :param: cmp  if None then compare sequences as sets. If elements are
                     not hashable then this method is inapplicable and the
                     sorted (with the comparator) sequences are compared.
        :param: places  see _assertAnyAlmostEqual() method
        :param: unordered_lists  see _assertAnyAlmostEqual() method
        :param: ignore_keys  see _assertAnyAlmostEqual() method
        :return: None
        """
        if cmp is not None:
            v1 = sorted(seq1, key=cmp)
            v2 = sorted(seq2, key=cmp)
            self.assertSequenceAlmostEqual(
                v1,
                v2,
                places,
                unordered_lists=unordered_lists,
                ignore_keys=ignore_keys,
            )
        else:
            self.assertEqual(len(seq1), len(seq2))
            v1 = set(seq1)
            v2 = set(seq2)
            self.assertSetEqual(v1, v2)

    def assertMappingAlmostEqual(
        self: TestCaseMixin,
        d1: Mapping,
        d2: Mapping,
        places: int = 10,
        *,
        unordered_lists: dict[str, Callable] | None = None,
        ignore_keys: set[str] | None = None,
    ) -> None:
        """Compare dictionaries recursively, numeric values being compared
        approximately, some lists being compared without order.

        :param: places  see _assertAnyAlmostEqual() method
        :param: unordered_lists  see _assertAnyAlmostEqual() method
                Example 1:
                        d1 = {
                            "name_from_unordered_list": [a1, b1, c1],
                            "some_other_name": [e1, f1, g1],
                        }
                        d2 = {
                            "name_from_unordered_list": [a2, b2, c2],
                            "some_other_name": [e2, f2, g2],
                        }
                Lists [a1, b1, c1] and [a2, b2, c2] will be compared
                without order, lists [e1, f1, g1] and [e2, f2, g2] -
                considering the order.

                Example 2:
                        d1 = {
                            "name_from_unordered_list": {
                                "key1": [a1, b1, c1],
                                "key2": [e1, f1, g1],
                            },
                            "some_other_name": [h1, i1, k1],
                        }
                        d2 = {
                            "name_from_unordered_list": {
                                "key1": [a2, b2, c2],
                                "key2": [e2, f2, g2],
                            },
                            "some_other_name": [h2, i2, k2],
                        }
                Lists [a1, b1, c1] and [a2, b2, c2] will be compared
                without order, as well as [e1, f1, g1] and
                [e2, f2, g2]; lists [h1, i1, k1] and [h2, i2, k2] -
                considering the order.
        :param: ignore_keys  see _assertAnyAlmostEqual() method
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

        if unordered_lists is None:
            unordered_lists = {}

        for k in d1_keys:
            v1 = d1[k]
            v2 = d2[k]
            if (cmp := unordered_lists.get(k, "")) == "" or not isinstance(
                v1, (Sequence, Mapping)
            ):
                self._assertAnyAlmostEqual(
                    v1,
                    v2,
                    places,
                    unordered_lists=unordered_lists,
                    ignore_keys=ignore_keys,
                )
            elif isinstance(v1, Sequence):
                self.assertSequenceAlmostEqualIgnoreOrder(
                    v1,
                    v2,
                    cmp,
                    places,
                    unordered_lists=unordered_lists,
                    ignore_keys=ignore_keys,
                )
            else:
                self.assertSetEqual(set(v1.keys()), set(v2.keys()))
                for ik in v1.keys():
                    iv1 = v1[ik]
                    iv2 = v2[ik]
                    self.assertSequenceAlmostEqualIgnoreOrder(
                        iv1,
                        iv2,
                        cmp,
                        places,
                        unordered_lists=unordered_lists,
                        ignore_keys=ignore_keys,
                    )
