from unittest import TestCase

from processors.gtfs import (
    dict_to_row,
    GTFS_COLUMNS,
)


class TestGTFS(TestCase):
    """Test processors/gtfs.py"""

    def test__dict_to_row__Nones_and_absent_keys(self) -> None:
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
                self.assertListEqual(
                    dict_to_row(test_trip["trip_data"], "trips"), answer
                )

    def test__dict_to_row__numeric_values(self) -> None:
        """Test that zero numeric values remain zeros in dict_to_row()
        function, and not empty strings or None.
        """

        shapes = [
            {
                "description": "Numeric non-zeroes",
                "shape_data": {
                    "shape_id": 1,
                    "shape_pt_lat": 55.3242425,
                    "shape_pt_lon": -179.23242,
                    "shape_pt_sequence": 133,
                    "shape_dist_traveled": 1.2345,
                },
                "answer": [1, 55.3242425, -179.23242, 133, 1.2345],
            },
            {
                "description": "Numeric zeroes and None keys",
                "shape_data": {
                    "shape_id": 0,
                    "shape_pt_lat": 0.0,
                    "shape_pt_lon": 0,
                    "shape_pt_sequence": 0,
                    "shape_dist_traveled": None,
                },
                "answer": [0, 0.0, 0, 0, ""],
            },
        ]

        for shape in shapes:
            with self.subTest(shape["description"]):
                self.assertListEqual(
                    dict_to_row(shape["shape_data"], "shapes"), shape["answer"]
                )
