from unittest import TestCase, mock

from subways.overpass import compose_overpass_request, overpass_request


class TestOverpassQuery(TestCase):
    def test__compose_overpass_request__no_bboxes(self) -> None:
        bboxes = []
        for overground in (True, False):
            with self.subTest(msg=f"{overground=}"):
                with self.assertRaises(RuntimeError):
                    compose_overpass_request(overground, bboxes)

    def test__compose_overpass_request__one_bbox(self) -> None:
        bboxes = [[1, 2, 3, 4]]

        expected = {
            False: (
                "[out:json][timeout:1000];"
                "("
                "("
                'rel[route="light_rail"](1,2,3,4);'
                'rel[route="monorail"](1,2,3,4);'
                'rel[route="subway"](1,2,3,4);'
                'rel[route="train"](1,2,3,4);'
                ");"
                "rel(br)[type=route_master];"
                "node[railway=subway_entrance](1,2,3,4);"
                "node[railway=train_station_entrance](1,2,3,4);"
                "rel[public_transport=stop_area](1,2,3,4);"
                "rel(br)[type=public_transport]"
                "[public_transport=stop_area_group];"
                ");"
                "(._;>>;);"
                "out body center qt;"
            ),
            True: (
                "[out:json][timeout:1000];"
                "("
                "("
                'rel[route="aerialway"](1,2,3,4);'
                'rel[route="bus"](1,2,3,4);'
                'rel[route="ferry"](1,2,3,4);'
                'rel[route="tram"](1,2,3,4);'
                'rel[route="trolleybus"](1,2,3,4);'
                ");"
                "rel(br)[type=route_master];"
                "rel[public_transport=stop_area](1,2,3,4);"
                "rel(br)[type=public_transport]"
                "[public_transport=stop_area_group];"
                ");"
                "(._;>>;);"
                "out body center qt;"
            ),
        }

        for overground, expected_answer in expected.items():
            with self.subTest(msg=f"{overground=}"):
                self.assertEqual(
                    expected_answer,
                    compose_overpass_request(overground, bboxes),
                )

    def test__compose_overpass_request__several_bboxes(self) -> None:
        bboxes = [[1, 2, 3, 4], [5, 6, 7, 8]]

        expected = {
            False: (
                "[out:json][timeout:1000];"
                "("
                "("
                'rel[route="light_rail"](1,2,3,4);'
                'rel[route="monorail"](1,2,3,4);'
                'rel[route="subway"](1,2,3,4);'
                'rel[route="train"](1,2,3,4);'
                ");"
                "rel(br)[type=route_master];"
                "node[railway=subway_entrance](1,2,3,4);"
                "node[railway=train_station_entrance](1,2,3,4);"
                "rel[public_transport=stop_area](1,2,3,4);"
                "rel(br)[type=public_transport][public_transport=stop_area_group];"  # noqa E501
                "("
                'rel[route="light_rail"](5,6,7,8);'
                'rel[route="monorail"](5,6,7,8);'
                'rel[route="subway"](5,6,7,8);'
                'rel[route="train"](5,6,7,8);'
                ");"
                "rel(br)[type=route_master];"
                "node[railway=subway_entrance](5,6,7,8);"
                "node[railway=train_station_entrance](5,6,7,8);"
                "rel[public_transport=stop_area](5,6,7,8);"
                "rel(br)[type=public_transport][public_transport=stop_area_group];"  # noqa E501
                ");"
                "(._;>>;);"
                "out body center qt;"
            ),
            True: (
                "[out:json][timeout:1000];"
                "("
                "("
                'rel[route="aerialway"](1,2,3,4);'
                'rel[route="bus"](1,2,3,4);'
                'rel[route="ferry"](1,2,3,4);'
                'rel[route="tram"](1,2,3,4);'
                'rel[route="trolleybus"](1,2,3,4);'
                ");"
                "rel(br)[type=route_master];"
                "rel[public_transport=stop_area](1,2,3,4);"
                "rel(br)[type=public_transport][public_transport=stop_area_group];"  # noqa E501
                "("
                'rel[route="aerialway"](5,6,7,8);'
                'rel[route="bus"](5,6,7,8);'
                'rel[route="ferry"](5,6,7,8);'
                'rel[route="tram"](5,6,7,8);'
                'rel[route="trolleybus"](5,6,7,8);'
                ");"
                "rel(br)[type=route_master];"
                "rel[public_transport=stop_area](5,6,7,8);"
                "rel(br)[type=public_transport][public_transport=stop_area_group];"  # noqa E501
                ");"
                "(._;>>;);"
                "out body center qt;"
            ),
        }

        for overground, expected_answer in expected.items():
            with self.subTest(msg=f"{overground=}"):
                self.assertEqual(
                    expected_answer,
                    compose_overpass_request(overground, bboxes),
                )

    def test__overpass_request(self) -> None:
        overpass_api = "http://overpass.example/"
        overground = False
        bboxes = [[1, 2, 3, 4]]
        expected_url = (
            "http://overpass.example/?data="
            "%5Bout%3Ajson%5D%5Btimeout%3A1000%5D%3B%28%28"
            "rel%5Broute%3D%22light_rail%22%5D%281%2C2%2C3%2C4"
            "%29%3Brel%5Broute%3D%22monorail%22%5D%281%2C2%2C3%2C4%29%3B"
            "rel%5Broute%3D%22subway%22%5D%281%2C2%2C3%2C4%29%3B"
            "rel%5Broute%3D%22train%22%5D%281%2C2%2C3%2C4%29%3B%29%3B"
            "rel%28br%29%5Btype%3Droute_master%5D%3B"
            "node%5Brailway%3Dsubway_entrance%5D%281%2C2%2C3%2C4%29%3B"
            "node%5Brailway%3Dtrain_station_entrance%5D%281%2C2%2C3%2C4%29%3B"
            "rel%5Bpublic_transport%3Dstop_area%5D%281%2C2%2C3%2C4%29%3B"
            "rel%28br%29%5Btype%3Dpublic_transport%5D%5Bpublic_transport%3D"
            "stop_area_group%5D%3B%29%3B"
            "%28._%3B%3E%3E%3B%29%3Bout%20body%20center%20qt%3B"
        )

        with mock.patch("subways.overpass.json.load") as load_mock:
            load_mock.return_value = {"elements": []}

            with mock.patch(
                "subways.overpass.urllib.request.urlopen"
            ) as urlopen_mock:
                urlopen_mock.return_value.getcode.return_value = 200

                overpass_request(overground, overpass_api, bboxes)

        urlopen_mock.assert_called_once_with(expected_url, timeout=1000)
