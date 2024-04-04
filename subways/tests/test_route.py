from unittest import TestCase

from subways.structure.route import (
    get_interval_in_seconds_from_tags,
    osm_interval_to_seconds,
    parse_time_range,
)


class TestTimeIntervalsParsing(TestCase):
    def test__osm_interval_to_seconds__invalid_value(self) -> None:
        intervals = (
            ["", "abc", "x30", "30x", "3x0"]
            + ["5:", ":5", "01:05:", ":01:05", "01:01:00:", ":01:01:00"]
            + ["01x:05", "01:x5", "x5:01:00", "01:0x:00", "01:01:x"]
            + ["-5", "01:-05", "-01:05", "-01:00:00", "01:-01:00", "01:01:-01"]
            + ["0", "00:00", "00:00:00"]
            + ["00:60", "01:00:60", "01:60:00"]
            + ["01:60:61", "01:61:60", "01:61:61"]
        )
        for interval in intervals:
            with self.subTest(msg=f"value='{interval}'"):
                self.assertIsNone(osm_interval_to_seconds(interval))

    def test__osm_interval_to_seconds__valid_value(self) -> None:
        intervals = {
            "5": 300,
            "65": 3900,
            "10:55": 39300,
            "02:02:02": 7322,
            "2:2:2": 7322,
            "00:59": 3540,
            "01:00": 3600,
            "00:00:50": 50,
            "00:10:00": 600,
            "01:00:00": 3600,
        }

        for interval_str, interval_sec in intervals.items():
            with self.subTest(msg=f"value='{interval_str}'"):
                self.assertEqual(
                    interval_sec, osm_interval_to_seconds(interval_str)
                )

    def test__parse_time_range__invalid_values(self) -> None:
        ranges = (
            ["", "a", "ab:cd-ab:cd", "1", "1-2", "01-02"]
            + ["24/8", "24/7/365"]
            + ["1:00-02:00", "01:0-02:00", "01:00-2:00", "01:00-02:0"]
            + ["1x:00-02:00", "01:0x-02:00", "01:00-1x:00", "01:00-02:ab"]
            + ["-1:00-02:00", "01:-1-02:00", "01:00--2:00", "01:00-02:-1"]
            + ["01;00-02:00", "01:00-02;00", "01:00=02:00"]
            + ["01:00-#02:00", "01:00 - 02:00"]
            + ["01:60-02:05", "01:00-01:61"]
        )
        for r in ranges:
            with self.subTest(msg=f"value='{r}'"):
                self.assertIsNone(parse_time_range(r))

    def test__parse_time_range__valid_values(self) -> None:
        ranges = (
            ["24/7"]
            + ["00:00-00:00", "00:01-00:02"]
            + ["01:00-02:00", "02:01-01:02"]
            + ["02:00-26:59", "12:01-13:59"]
            + ["Mo-Fr 06:00-21:30", "06:00-21:30 (weekdays)"]
            + ["Mo-Fr 06:00-21:00; Sa-Su 07:00-20:00"]
        )
        answers = [
            ((0, 0), (24, 0)),
            ((0, 0), (0, 0)),
            ((0, 1), (0, 2)),
            ((1, 0), (2, 0)),
            ((2, 1), (1, 2)),
            ((2, 0), (26, 59)),
            ((12, 1), (13, 59)),
            ((6, 0), (21, 30)),
            ((6, 0), (21, 30)),
            ((6, 0), (21, 0)),
        ]

        for r, answer in zip(ranges, answers):
            with self.subTest(msg=f"value='{r}'"):
                self.assertTupleEqual(answer, parse_time_range(r))


class TestRouteIntervals(TestCase):
    def test__get_interval_in_seconds_from_tags__one_key(self) -> None:
        cases = [
            {"tags": {}, "answer": None},
            {"tags": {"a": "1"}, "answer": None},
            {"tags": {"duration": "1"}, "answer": 60},
            {"tags": {"durationxxx"}, "answer": None},
            {"tags": {"xxxduration"}, "answer": None},
            # prefixes not considered
            {"tags": {"ru:duration"}, "answer": None},
            # suffixes considered
            {"tags": {"duration:peak": "1"}, "answer": 60},
            # bare tag has precedence over suffixed version
            {"tags": {"duration:peak": "1", "duration": "2"}, "answer": 120},
            # first suffixed version apply
            {"tags": {"duration:y": "1", "duration:x": "2"}, "answer": 60},
            # other tags present
            {"tags": {"a": "x", "duration": "1", "b": "y"}, "answer": 60},
        ]

        for case in cases:
            with self.subTest(msg=f"{case['tags']}"):
                self.assertEqual(
                    case["answer"],
                    get_interval_in_seconds_from_tags(
                        case["tags"], "duration"
                    ),
                )

    def test__get_interval_in_seconds_from_tags__several_keys(self) -> None:
        keys = ("interval", "headway")
        cases = [
            {"tags": {}, "answer": None},
            # prefixes not considered
            {"tags": {"ru:interval"}, "answer": None},
            {"tags": {"interval": "1"}, "answer": 60},
            {"tags": {"headway": "1"}, "answer": 60},
            {"tags": {"interval": "1", "headway": "2"}, "answer": 60},
            #  interval has precedence due to its position in 'keys'
            {"tags": {"headway": "2", "interval": "1"}, "answer": 60},
            #  non-suffixed keys has precedence
            {"tags": {"interval:peak": "1", "headway": "2"}, "answer": 120},
            # among suffixed versions, first key in 'keys' is used first
            {
                "tags": {"headway:peak": "2", "interval:peak": "1"},
                "answer": 60,
            },
        ]

        for case in cases:
            with self.subTest(msg=f"{case['tags']}"):
                self.assertEqual(
                    case["answer"],
                    get_interval_in_seconds_from_tags(case["tags"], keys),
                )
