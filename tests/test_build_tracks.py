from tests.sample_data_for_build_tracks import metro_samples
from tests.util import TestCase


class TestOneRouteTracks(TestCase):
    """Test tracks extending and truncating on one-route networks"""

    def prepare_city_routes(self, metro_sample: dict) -> tuple:
        cities, transfers = self.prepare_cities(metro_sample)
        city = cities[0]

        self.assertTrue(city.is_good)

        route_master = list(city.routes.values())[0]
        variants = route_master.routes

        fwd_route = [v for v in variants if v.name == "Forward"][0]
        bwd_route = [v for v in variants if v.name == "Backward"][0]

        return fwd_route, bwd_route

    def _test_tracks_extending_for_network(self, metro_sample: dict) -> None:
        fwd_route, bwd_route = self.prepare_city_routes(metro_sample)

        self.assertEqual(
            fwd_route.tracks,
            metro_sample["tracks"],
            "Wrong tracks",
        )
        extended_tracks = fwd_route.get_extended_tracks()
        self.assertEqual(
            extended_tracks,
            metro_sample["extended_tracks"],
            "Wrong tracks after extending",
        )

        self.assertEqual(
            bwd_route.tracks,
            metro_sample["tracks"][::-1],
            "Wrong backward tracks",
        )
        extended_tracks = bwd_route.get_extended_tracks()
        self.assertEqual(
            extended_tracks,
            metro_sample["extended_tracks"][::-1],
            "Wrong backward tracks after extending",
        )

    def _test_tracks_truncating_for_network(self, metro_sample: dict) -> None:
        fwd_route, bwd_route = self.prepare_city_routes(metro_sample)

        truncated_tracks = fwd_route.get_truncated_tracks(fwd_route.tracks)
        self.assertEqual(
            truncated_tracks,
            metro_sample["truncated_tracks"],
            "Wrong tracks after truncating",
        )
        truncated_tracks = bwd_route.get_truncated_tracks(bwd_route.tracks)
        self.assertEqual(
            truncated_tracks,
            metro_sample["truncated_tracks"][::-1],
            "Wrong backward tracks after truncating",
        )

    def _test_stop_positions_on_rails_for_network(self, sample: dict) -> None:
        fwd_route, bwd_route = self.prepare_city_routes(sample)

        for route, route_label in zip(
            (fwd_route, bwd_route), ("forward", "backward")
        ):
            route_data = sample[route_label]

            for attr in (
                "first_stop_on_rails_index",
                "last_stop_on_rails_index",
            ):
                self.assertEqual(
                    getattr(route, attr),
                    route_data[attr],
                    f"Wrong {attr} for {route_label} route",
                )

            first_ind = route_data["first_stop_on_rails_index"]
            last_ind = route_data["last_stop_on_rails_index"]
            positions_on_rails = [
                rs.positions_on_rails
                for rs in route.stops[first_ind : last_ind + 1]  # noqa E203
            ]
            self.assertSequenceAlmostEqual(
                positions_on_rails, route_data["positions_on_rails"]
            )

    def test_tracks_extending(self) -> None:
        for sample in metro_samples:
            sample_name = sample["name"]
            sample["cities_info"][0]["name"] = sample_name
            with self.subTest(msg=sample_name):
                self._test_tracks_extending_for_network(sample)

    def test_tracks_truncating(self) -> None:
        for sample in metro_samples:
            sample_name = sample["name"]
            sample["cities_info"][0]["name"] = sample_name
            with self.subTest(msg=sample_name):
                self._test_tracks_truncating_for_network(sample)

    def test_stop_position_on_rails(self) -> None:
        for sample in metro_samples:
            sample_name = sample["name"]
            sample["cities_info"][0]["name"] = sample_name
            with self.subTest(msg=sample_name):
                self._test_stop_positions_on_rails_for_network(sample)
