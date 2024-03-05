import collections
import itertools
import unittest

from subways.geom_utils import project_on_segment
from subways.types import LonLat


class TestProjection(unittest.TestCase):
    """Test subways.geom_utils.project_on_segment function"""

    PRECISION = 10  # decimal places in assertAlmostEqual

    SHIFT = 1e-6  # Small distance between projected point and segment endpoint

    def _test_projection_in_bulk(
        self,
        points: list[LonLat],
        segments: list[tuple[LonLat, LonLat]],
        answers: list[float | None],
    ) -> None:
        """Test 'project_on_segment' function for array of points and array
        of parallel segments projections on which are equal.
        """
        for point, ans in zip(points, answers):
            for seg in segments:
                for segment, answer in zip(
                    (seg, seg[::-1]),  # What if invert the segment?
                    (ans, None if ans is None else 1 - ans),
                ):
                    u = project_on_segment(point, segment[0], segment[1])

                    if answer is None:
                        self.assertIsNone(
                            u,
                            f"Project of point {point} onto segment {segment} "
                            f"should be None, but {u} returned",
                        )
                    else:
                        self.assertAlmostEqual(
                            u,
                            answer,
                            self.PRECISION,
                            f"Wrong projection of point {point} onto segment "
                            f"{segment}: {u} returned, {answer} expected",
                        )

    def test_projection_on_horizontal_segments(self) -> None:
        points = [
            (-2, 0),
            (-1 - self.SHIFT, 0),
            (-1, 0),
            (-1 + self.SHIFT, 0),
            (-0.5, 0),
            (0, 0),
            (0.5, 0),
            (1 - self.SHIFT, 0),
            (1, 0),
            (1 + self.SHIFT, 0),
            (2, 0),
        ]
        horizontal_segments = [
            ((-1, -1), (1, -1)),
            ((-1, 0), (1, 0)),
            ((-1, 1), (1, 1)),
        ]
        answers = [
            None,
            None,
            0,
            self.SHIFT / 2,
            0.25,
            0.5,
            0.75,
            1 - self.SHIFT / 2,
            1,
            None,
            None,
        ]

        self._test_projection_in_bulk(points, horizontal_segments, answers)

    def test_projection_on_vertical_segments(self) -> None:
        points = [
            (0, -2),
            (0, -1 - self.SHIFT),
            (0, -1),
            (0, -1 + self.SHIFT),
            (0, -0.5),
            (0, 0),
            (0, 0.5),
            (0, 1 - self.SHIFT),
            (0, 1),
            (0, 1 + self.SHIFT),
            (0, 2),
        ]
        vertical_segments = [
            ((-1, -1), (-1, 1)),
            ((0, -1), (0, 1)),
            ((1, -1), (1, 1)),
        ]
        answers = [
            None,
            None,
            0,
            self.SHIFT / 2,
            0.25,
            0.5,
            0.75,
            1 - self.SHIFT / 2,
            1,
            None,
            None,
        ]

        self._test_projection_in_bulk(points, vertical_segments, answers)

    def test_projection_on_inclined_segment(self) -> None:
        points = [
            (-2, -2),
            (-1, -1),
            (-0.5, -0.5),
            (0, 0),
            (0.5, 0.5),
            (1, 1),
            (2, 2),
        ]
        segments = [
            ((-2, 0), (0, 2)),
            ((-1, -1), (1, 1)),
            ((0, -2), (2, 0)),
        ]
        answers = [None, 0, 0.25, 0.5, 0.75, 1, None]

        self._test_projection_in_bulk(points, segments, answers)

    def test_projection_with_different_collections(self) -> None:
        """The tested function should accept points as any consecutive
        container with index operator.
        """
        types = (
            tuple,
            list,
            collections.deque,
        )

        point = (0, 0.5)
        segment_end1 = (0, 0)
        segment_end2 = (1, 0)

        for p_type, s1_type, s2_type in itertools.product(types, types, types):
            p = p_type(point)
            s1 = s1_type(segment_end1)
            s2 = s2_type(segment_end2)
            project_on_segment(p, s1, s2)

    def test_projection_on_degenerate_segment(self) -> None:
        coords = [-1, 0, 1]
        points = [(x, y) for x, y in itertools.product(coords, coords)]
        segments = [
            ((0, 0), (0, 0)),
            ((0, 0), (0, 1e-8)),
        ]
        answers = [None] * len(points)

        self._test_projection_in_bulk(points, segments, answers)
