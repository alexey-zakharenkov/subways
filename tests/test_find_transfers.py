from copy import deepcopy

from tests.sample_data_for_outputs import metro_samples
from tests.util import TestCase, JsonLikeComparisonMixin


class TestTransfers(JsonLikeComparisonMixin, TestCase):
    """Test that the validator provides expected set of transfers."""

    def _test__find_transfers__for_sample(self, metro_sample: dict) -> None:
        cities, transfers = self.prepare_cities(metro_sample)
        expected_transfers = metro_sample["transfers"]

        self.assertSequenceAlmostEqualIgnoreOrder(
            expected_transfers,
            transfers,
            cmp=lambda transfer_as_set: sorted(transfer_as_set),
        )

    def test__find_transfers(self) -> None:
        sample1 = metro_samples[0]

        sample2 = deepcopy(metro_samples[0])
        # Make the second city invalid and thus exclude the inter-city transfer
        sample2["cities_info"][1]["num_stations"] += 1
        sample2["transfers"] = [{"r1", "r2"}]

        for sample in sample1, sample2:
            with self.subTest(msg=sample["name"]):
                self._test__find_transfers__for_sample(sample)
