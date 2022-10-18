import unittest

from processors.gtfs import (
    dict_to_row,
    GTFS_COLUMNS,
)


class TestGTFS(unittest.TestCase):
    """Test processors/gtfs.py"""

    def test_dict_to_row(self):
        """Test that absent or None values in a GTFS feature item
        are converted by dict_to_row() function to empty strings
        in right amount.
        """

        if GTFS_COLUMNS["trips"][:3] != ["route_id", "service_id", "trip_id"]:
            raise RuntimeError("GTFS column names/order inconsistency")

        test_trips = [
            {
                "description": "Absent keys",
                "trip_data": {
                    "route_id": 1,
                    "service_id": "a",
                    "trip_id": "tr_123",
                },
            },
            {
                "description": "None or absent keys",
                "trip_data": {
                    "route_id": 1,
                    "service_id": "a",
                    "trip_id": "tr_123",
                    "trip_headsign": None,
                    "trip_short_name": None,
                    "route_pattern_id": None,
                },
            },
            {
                "description": "None, empty-string or absent keys",
                "trip_data": {
                    "route_id": 1,
                    "service_id": "a",
                    "trip_id": "tr_123",
                    "trip_headsign": "",
                    "trip_short_name": "",
                    "route_pattern_id": None,
                },
            },
        ]

        answer = [1, "a", "tr_123"] + [""] * (len(GTFS_COLUMNS["trips"]) - 3)

        for test_trip in test_trips:
            with self.subTest(msg=test_trip["description"]):
                self.assertEqual(
                    dict_to_row(test_trip["trip_data"], "trips"), answer
                )
