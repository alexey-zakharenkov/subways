import contextlib
import io
from pathlib import Path
from unittest import TestCase

from make_all_metro_poly import make_disjoint_metro_polygons


cases = [
    {
        "csv_file": "cities_info_1city.csv",
        "expected_stdout": """all metro
1
  37.1667 55.3869
  37.1667 56.0136
  38.2626 56.0136
  38.2626 55.3869
  37.1667 55.3869
END
END
""",
        "shape_line_ranges": [
            {
                "start": 2,
                "end": 6,
            },
        ],
    },
    {
        "csv_file": "cities_info_2cities.csv",
        "expected_stdout": """all metro
1
  -0.9747 51.8459
  0.3315 51.8459
  0.3315 51.1186
  -0.9747 51.1186
  -0.9747 51.8459
END
2
  37.1667 56.0136
  38.2626 56.0136
  38.2626 55.3869
  37.1667 55.3869
  37.1667 56.0136
END
END
""",
        "shape_line_ranges": [
            {
                "start": 2,
                "end": 6,
            },
            {
                "start": 9,
                "end": 13,
            },
        ],
    },
]


class TestMakeAllMetroPoly(TestCase):
    def test_make_disjoint_metro_polygons(self) -> None:
        for case in cases:
            with self.subTest(msg=case["csv_file"]):
                assets_dir = Path(__file__).resolve().parent / "assets"
                file_url = f"file://{assets_dir}/{case['csv_file']}"
                stream = io.StringIO()
                with contextlib.redirect_stdout(stream):
                    make_disjoint_metro_polygons(file_url)
                generated_poly = stream.getvalue()
                expected_poly = case["expected_stdout"]

                # Since shapely may produce multipolygon with different order
                # of polygons in it and different vertex order in a polygon,
                # we should compare polygons/vertexes as sets.

                generated_poly_lines = generated_poly.split("\n")
                expected_poly_lines = expected_poly.split("\n")
                self.assertSetEqual(
                    set(expected_poly_lines), set(generated_poly_lines)
                )

                line_ranges = case["shape_line_ranges"]

                # Check that polygons are closed
                for line_range in line_ranges:
                    self.assertEqual(
                        generated_poly_lines[line_range["start"]],
                        generated_poly_lines[line_range["end"]],
                    )

                generated_points = [
                    sorted(
                        generated_poly_lines[r["start"] : r["end"]]  # noqa 203
                    )
                    for r in line_ranges
                ]
                expected_points = [
                    sorted(
                        expected_poly_lines[r["start"] : r["end"]]  # noqa 203
                    )
                    for r in line_ranges
                ]
                expected_points.sort()
                generated_points.sort()
                self.assertListEqual(expected_points, generated_points)
