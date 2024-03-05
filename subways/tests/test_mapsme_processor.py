from operator import itemgetter

from subways.processors.mapsme import transit_data_to_mapsme
from subways.tests.sample_data_for_outputs import metro_samples
from subways.tests.util import JsonLikeComparisonMixin, TestCase


class TestMapsme(JsonLikeComparisonMixin, TestCase):
    """Test processors/mapsme.py"""

    def test__transit_data_to_mapsme(self) -> None:
        for sample in metro_samples:
            with self.subTest(msg=sample["name"]):
                self._test__transit_data_to_mapsme__for_sample(sample)

    def _test__transit_data_to_mapsme__for_sample(
        self, metro_sample: dict
    ) -> None:
        cities, transfers = self.prepare_cities(metro_sample)
        calculated_mapsme_data = transit_data_to_mapsme(
            cities, transfers, cache_path=None
        )
        control_mapsme_data = metro_sample["mapsme_output"]

        self.assertSetEqual(
            set(control_mapsme_data.keys()),
            set(calculated_mapsme_data.keys()),
        )

        self.assertSequenceAlmostEqualIgnoreOrder(
            control_mapsme_data["stops"],
            calculated_mapsme_data["stops"],
            cmp=itemgetter("id"),
            unordered_lists={
                "entrances": lambda e: (e["osm_type"], e["osm_id"]),
                "exits": lambda e: (e["osm_type"], e["osm_id"]),
            },
        )

        self.assertSequenceAlmostEqualIgnoreOrder(
            control_mapsme_data["transfers"],
            calculated_mapsme_data["transfers"],
        )

        self.assertSequenceAlmostEqualIgnoreOrder(
            control_mapsme_data["networks"],
            calculated_mapsme_data["networks"],
            cmp=itemgetter("network"),
            unordered_lists={
                "routes": itemgetter("route_id"),
                "itineraries": lambda it: (it["stops"], it["interval"]),
            },
        )
