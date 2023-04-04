from tests.sample_data_for_error_messages import sample_networks
from tests.util import TestCase


class TestValidationMessages(TestCase):
    """Test that the validator provides expected validation messages
    on different types of errors in input OSM data.
    """

    def _test_validation_messages_for_network(self, network_data):
        city = self.validate_city(network_data)

        for err_level in ("errors", "warnings", "notices"):
            self.assertListEqual(
                sorted(getattr(city, err_level)),
                sorted(network_data[err_level]),
            )

    def test_validation_messages(self) -> None:
        for network_name, network_data in sample_networks.items():
            with self.subTest(msg=network_name):
                self._test_validation_messages_for_network(network_data)
