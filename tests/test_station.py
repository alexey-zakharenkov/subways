from unittest import TestCase

from structure.station import Station


class TestStation(TestCase):
    def test__get_modes(self) -> None:
        cases = [
            {"element": {"tags": {"railway": "station"}}, "modes": set()},
            {
                "element": {
                    "tags": {"railway": "station", "station": "train"}
                },
                "modes": {"train"},
            },
            {
                "element": {"tags": {"railway": "station", "train": "yes"}},
                "modes": {"train"},
            },
            {
                "element": {
                    "tags": {
                        "railway": "station",
                        "station": "subway",
                        "train": "yes",
                    }
                },
                "modes": {"subway", "train"},
            },
            {
                "element": {
                    "tags": {
                        "railway": "station",
                        "subway": "yes",
                        "train": "yes",
                        "light_rail": "yes",
                        "monorail": "yes",
                    }
                },
                "modes": {"subway", "train", "light_rail", "monorail"},
            },
        ]
        for case in cases:
            element = case["element"]
            expected_modes = case["modes"]
            self.assertSetEqual(expected_modes, Station.get_modes(element))
