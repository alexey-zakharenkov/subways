"""
To perform tests manually, run this command from the top directory
of the repository:

> python -m unittest discover tests

or simply

> python -m unittest
"""

import io
import unittest

from subway_structure import City
from subway_io import load_xml
from tests.sample_data import sample_networks


class TestOneRouteTracks(unittest.TestCase):
    """Test tracks extending and truncating on one-route networks"""

    STATION_COUNT_INDEX = 4
    CITY_TEMPLATE = [
        1,  # city id
        "Null Island",  # name
        "World",  # Country
        "Africa",  # continent
        None,  # station count. Would be taken from the sample network data under testing
        1,  # subway line count
        0,  # light rail line count
        0,  # interchanges
        "-179, -89, 179, 89",  # bbox
    ]

    def prepare_city_routes(self, network):
        city_data = self.CITY_TEMPLATE.copy()
        city_data[self.STATION_COUNT_INDEX] = network["station_count"]
        city = City(city_data)
        elements = load_xml(io.BytesIO(network["xml"].encode("utf-8")))
        for el in elements:
            city.add(el)
        city.extract_routes()
        city.validate()

        self.assertTrue(city.is_good())

        route_master = list(city.routes.values())[0]
        variants = route_master.routes

        fwd_route = [v for v in variants if v.name == "Forward"][0]
        bwd_route = [v for v in variants if v.name == "Backward"][0]

        return fwd_route, bwd_route

    def _test_tracks_extending_for_network(self, network_data):
        fwd_route, bwd_route = self.prepare_city_routes(network_data)

        self.assertEqual(
            fwd_route.tracks,
            network_data["tracks"],
            "Wrong tracks",
        )
        extended_tracks = fwd_route.get_extended_tracks()
        self.assertEqual(
            extended_tracks,
            network_data["extended_tracks"],
            "Wrong tracks after extending",
        )

        self.assertEqual(
            bwd_route.tracks,
            network_data["tracks"][::-1],
            "Wrong backward tracks",
        )
        extended_tracks = bwd_route.get_extended_tracks()
        self.assertEqual(
            extended_tracks,
            network_data["extended_tracks"][::-1],
            "Wrong backward tracks after extending",
        )

    def _test_tracks_truncating_for_network(self, network_data):
        fwd_route, bwd_route = self.prepare_city_routes(network_data)

        truncated_tracks = fwd_route.get_truncated_tracks(fwd_route.tracks)
        self.assertEqual(
            truncated_tracks,
            network_data["truncated_tracks"],
            "Wrong tracks after truncating",
        )
        truncated_tracks = bwd_route.get_truncated_tracks(bwd_route.tracks)
        self.assertEqual(
            truncated_tracks,
            network_data["truncated_tracks"][::-1],
            "Wrong backward tracks after truncating",
        )

    def test_tracks_extending(self):
        for network_name, network_data in sample_networks.items():
            with self.subTest(msg=network_name):
                self._test_tracks_extending_for_network(network_data)

    def test_tracks_truncating(self):
        for network_name, network_data in sample_networks.items():
            with self.subTest(msg=network_name):
                self._test_tracks_truncating_for_network(network_data)
