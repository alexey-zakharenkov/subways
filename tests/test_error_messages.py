from tests.sample_data_for_error_messages import metro_samples
from tests.util import TestCase


class TestValidationMessages(TestCase):
    """Test that the validator provides expected validation messages
    on different types of errors in input OSM data.
    """

    def _test_validation_messages_for_network(
        self, metro_sample: dict
    ) -> None:
        cities, transfers = self.prepare_cities(metro_sample)
        city = cities[0]

        for err_level in ("errors", "warnings", "notices"):
            self.assertListEqual(
                sorted(getattr(city, err_level)),
                sorted(metro_sample[err_level]),
            )

    def test_validation_messages(self) -> None:
        for sample in metro_samples:
            with self.subTest(msg=sample["name"]):
                self._test_validation_messages_for_network(sample)
