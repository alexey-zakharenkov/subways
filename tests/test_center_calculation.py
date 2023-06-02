import io
from unittest import TestCase

from process_subways import calculate_centers
from subway_io import load_xml
from tests.sample_data_for_center_calculation import metro_samples


class TestCenterCalculation(TestCase):
    """Test center calculation. Test data [should] contain among others
    the following edge cases:
      - an empty relation. Its element should not obtain "center" key.
      - relation as member of another relation, the child relation following
        the parent in the OSM XML.
      - relation with incomplete members (broken references).
      - relations with cyclic references.
    """

    def test_calculate_centers(self) -> None:
        for sample in metro_samples:
            with self.subTest(msg=sample["name"]):
                self._test_calculate_centers_for_sample(sample)

    def _test_calculate_centers_for_sample(self, metro_sample: dict) -> None:
        elements = load_xml(io.BytesIO(metro_sample["xml"].encode()))
        calculate_centers(elements)

        elements_dict = {
            f"{'w' if el['type'] == 'way' else 'r'}{el['id']}": el
            for el in elements
        }

        calculated_centers = {
            k: el["center"]
            for k, el in elements_dict.items()
            if "center" in el
        }

        expected_centers = metro_sample["expected_centers"]

        self.assertTrue(set(calculated_centers).issubset(expected_centers))

        for k, correct_center in expected_centers.items():
            if correct_center is None:
                self.assertNotIn("center", elements_dict[k])
            else:
                self.assertIn(k, calculated_centers)
                calculated_center = calculated_centers[k]
                self.assertAlmostEqual(
                    calculated_center["lat"], correct_center["lat"], places=10
                )
                self.assertAlmostEqual(
                    calculated_center["lon"], correct_center["lon"], places=10
                )
