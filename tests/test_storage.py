import json
from operator import itemgetter

from processors._common import transit_to_dict
from tests.sample_data_for_outputs import metro_samples
from tests.util import JsonLikeComparisonMixin, TestCase


class TestStorage(JsonLikeComparisonMixin, TestCase):
    def test_storage(self) -> None:
        for sample in metro_samples:
            with self.subTest(msg=sample["name"]):
                self._test_storage_for_sample(sample)

    def _test_storage_for_sample(self, metro_sample: dict) -> None:
        cities, transfers = self.prepare_cities(metro_sample)

        calculated_transit_data = transit_to_dict(cities, transfers)

        control_transit_data = json.loads(metro_sample["json_dump"])
        control_transit_data["transfers"] = set(
            map(tuple, control_transit_data["transfers"])
        )

        self._compare_transit_data(
            calculated_transit_data, control_transit_data
        )

    def _compare_transit_data(
        self, transit_data1: dict, transit_data2: dict
    ) -> None:
        id_cmp = itemgetter("id")

        self.assertMappingAlmostEqual(
            transit_data1,
            transit_data2,
            unordered_lists={
                "routes": id_cmp,
                "itineraries": id_cmp,
                "entrances": id_cmp,
            },
        )
