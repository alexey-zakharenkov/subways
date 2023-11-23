from tests.util import TestCase

from tests.sample_data_for_twin_routes import metro_samples


class TestRouteMaster(TestCase):
    def _test_find_twin_routes_for_network(self, metro_sample: dict) -> None:
        cities, transfers = self.prepare_cities(metro_sample)
        city = cities[0]

        self.assertTrue(city.is_good)

        for route_master_id, expected_twin_ids in metro_sample[
            "twin_routes"
        ].items():
            route_master = city.routes[route_master_id]
            calculated_twins = route_master.find_twin_routes()
            calculated_twin_ids = {
                r1.id: r2.id for r1, r2 in calculated_twins.items()
            }
            self.assertDictEqual(expected_twin_ids, calculated_twin_ids)

    def test_find_twin_routes(self) -> None:
        for sample in metro_samples:
            with self.subTest(msg=sample["name"]):
                self._test_find_twin_routes_for_network(sample)
