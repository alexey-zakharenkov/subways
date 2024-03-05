from subways.structure.route_master import RouteMaster
from subways.tests.sample_data_for_twin_routes import metro_samples
from subways.tests.util import TestCase


class TestRouteMaster(TestCase):
    def test__find_common_circular_subsequence(self) -> None:
        cases = [
            {  # the 1st sequence is empty
                "sequence1": [],
                "sequence2": [1, 2, 3, 4],
                "answer": [],
            },
            {  # the 2nd sequence is empty
                "sequence1": [1, 2, 3, 4],
                "sequence2": [],
                "answer": [],
            },
            {  # equal sequences
                "sequence1": [1, 2, 3, 4],
                "sequence2": [1, 2, 3, 4],
                "answer": [1, 2, 3, 4],
            },
            {  # one sequence is a cyclic shift of the other
                "sequence1": [1, 2, 3, 4],
                "sequence2": [4, 1, 2, 3],
                "answer": [1, 2, 3, 4],
            },
            {  # the 2nd sequence is a subsequence of the 1st; equal ends
                "sequence1": [1, 2, 3, 4],
                "sequence2": [1, 2, 4],
                "answer": [1, 2, 4],
            },
            {  # the 1st sequence is a subsequence of the 2nd; equal ends
                "sequence1": [1, 2, 4],
                "sequence2": [1, 2, 3, 4],
                "answer": [1, 2, 4],
            },
            {  # the 2nd sequence is an innter subsequence of the 1st
                "sequence1": [1, 2, 3, 4],
                "sequence2": [2, 3],
                "answer": [2, 3],
            },
            {  # the 1st sequence is an inner subsequence of the 2nd
                "sequence1": [2, 3],
                "sequence2": [1, 2, 3, 4],
                "answer": [2, 3],
            },
            {  # the 2nd sequence is a continuation of the 1st
                "sequence1": [1, 2, 3, 4],
                "sequence2": [4, 5, 6],
                "answer": [4],
            },
            {  # the 1st sequence is a continuation of the 2nd
                "sequence1": [4, 5, 6],
                "sequence2": [1, 2, 3, 4],
                "answer": [4],
            },
            {  # no common elements
                "sequence1": [1, 2, 3, 4],
                "sequence2": [5, 6, 7],
                "answer": [],
            },
            {  # one sequence is the reversed other
                "sequence1": [1, 2, 3, 4],
                "sequence2": [4, 3, 2, 1],
                "answer": [1, 2],
            },
            {  # the 2nd is a subsequence of shifted 1st
                "sequence1": [1, 2, 3, 4],
                "sequence2": [2, 4, 1],
                "answer": [1, 2, 4],
            },
            {  # the 1st is a subsequence of shifted 2nd
                "sequence1": [2, 4, 1],
                "sequence2": [1, 2, 3, 4],
                "answer": [2, 4, 1],
            },
            {  # mixed case: few common elements
                "sequence1": [1, 2, 4],
                "sequence2": [2, 3, 4],
                "answer": [2, 4],
            },
        ]

        for i, case in enumerate(cases):
            with self.subTest(f"case#{i}"):
                self.assertListEqual(
                    case["answer"],
                    RouteMaster.find_common_circular_subsequence(
                        case["sequence1"], case["sequence2"]
                    ),
                )

    def _test_find_twin_routes_for_network(self, metro_sample: dict) -> None:
        cities, transfers = self.prepare_cities(metro_sample)
        city = cities[0]

        self.assertTrue(city.is_good)

        for route_master_id, expected_twin_ids in metro_sample[
            "twin_routes"
        ].items():
            route_master = city.routes[route_master_id]
            calculated_twins = route_master.find_twin_routes()
            calculated_twin_ids = {
                r1.id: r2.id for r1, r2 in calculated_twins.items()
            }
            self.assertDictEqual(expected_twin_ids, calculated_twin_ids)

    def test_find_twin_routes(self) -> None:
        for sample in metro_samples:
            with self.subTest(msg=sample["name"]):
                self._test_find_twin_routes_for_network(sample)
