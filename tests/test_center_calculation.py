import json
from pathlib import Path
from unittest import TestCase

from process_subways import calculate_centers
from subway_io import load_xml


class TestCenterCalculation(TestCase):
    """Test center calculation. Test data [should] contain among others
    the following edge cases:
      - an empty relation. It's element should not obtain "center" key.
      - relation as member of relation, the child relation following the parent
        in the OSM XML file.
      - relation with incomplete members (broken references).
      - relations with cyclic references.
    """

    ASSETS_PATH = Path(__file__).resolve().parent / "assets"
    OSM_DATA = str(ASSETS_PATH / "kuntsevskaya_transfer.osm")
    CORRECT_CENTERS = str(ASSETS_PATH / "kuntsevskaya_centers.json")

    def test__calculate_centers(self) -> None:
        elements = load_xml(self.OSM_DATA)

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

        with open(self.CORRECT_CENTERS) as f:
            correct_centers = json.load(f)

        self.assertTrue(set(calculated_centers).issubset(correct_centers))

        for k, correct_center in correct_centers.items():
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
