import codecs
import csv
from functools import partial
from pathlib import Path
from zipfile import ZipFile

from processors._common import transit_to_dict
from processors.gtfs import dict_to_row, GTFS_COLUMNS, transit_data_to_gtfs
from tests.util import TestCase
from tests.sample_data_for_outputs import metro_samples


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

    def test__transit_data_to_gtfs(self) -> None:
        for metro_sample in metro_samples:
            cities, transfers = self.prepare_cities(metro_sample)
            calculated_transit_data = transit_to_dict(cities, transfers)
            calculated_gtfs_data = transit_data_to_gtfs(
                calculated_transit_data
            )

            control_gtfs_data = self._readGtfs(
                Path(__file__).resolve().parent / metro_sample["gtfs_file"]
            )
            self._compareGtfs(calculated_gtfs_data, control_gtfs_data)

    @staticmethod
    def _readGtfs(filepath: str) -> dict:
        gtfs_data = dict()
        with ZipFile(filepath) as zf:
            for gtfs_feature in GTFS_COLUMNS:
                with zf.open(f"{gtfs_feature}.txt") as f:
                    reader = csv.reader(codecs.iterdecode(f, "utf-8"))
                    next(reader)  # read header
                    rows = list(reader)
                    gtfs_data[gtfs_feature] = rows
        return gtfs_data

    def _compareGtfs(
        self, calculated_gtfs_data: dict, control_gtfs_data: dict
    ) -> None:
        for gtfs_feature in GTFS_COLUMNS:
            calculated_rows = sorted(
                map(
                    partial(dict_to_row, record_type=gtfs_feature),
                    calculated_gtfs_data[gtfs_feature],
                )
            )
            control_rows = sorted(control_gtfs_data[gtfs_feature])

            self.assertEqual(len(calculated_rows), len(control_rows))

            for i, (calculated_row, control_row) in enumerate(
                zip(calculated_rows, control_rows)
            ):
                self.assertEqual(
                    len(calculated_row),
                    len(control_row),
                    f"Different length of {i}-th row of {gtfs_feature}",
                )
                for calculated_value, control_value in zip(
                    calculated_row, control_row
                ):
                    if calculated_value is None:
                        self.assertEqual(control_value, "", f"in {i}-th row")
                    else:  # convert str to float/int/str
                        self.assertAlmostEqual(
                            calculated_value,
                            type(calculated_value)(control_value),
                            places=10,
                        )
