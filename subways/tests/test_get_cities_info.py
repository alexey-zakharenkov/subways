import os
import tempfile
from unittest import TestCase

from subways.validation import get_cities_info

HEADER = (
    "id,name,country,continent,num_stations,num_lines,"
    "num_light_lines,num_interchanges,bbox,networks"
)


class TestGetCitiesInfo(TestCase):
    def setUp(self) -> None:
        self._temp_files: list[str] = []

    def tearDown(self) -> None:
        for path in self._temp_files:
            os.unlink(path)

    def _csv_url(self, rows: list[str]) -> str:
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        )
        f.write(HEADER + "\n")
        for row in rows:
            f.write(row + "\n")
        f.close()
        self._temp_files.append(f.name)
        return f"file://{f.name}"

    def test_single_source(self) -> None:
        url = self._csv_url(
            [
                '1,Moscow,Russia,Europe,300,14,3,66,"37,55,38,56",net1',
                '2,SPb,Russia,Europe,72,5,0,7,"30,59,30,60",net2',
            ]
        )
        result = get_cities_info([url])
        self.assertListEqual(
            [(c["id"], c["name"]) for c in result],
            [("1", "Moscow"), ("2", "SPb")],
        )

    def test_skips_rows_without_id_or_bbox(self) -> None:
        url = self._csv_url(
            [
                '1,WithBoth,Russia,Europe,1,1,0,0,"1,2,3,4",net',
                ',NoId,Russia,Europe,1,1,0,0,"1,2,3,4",net',
                "2,NoBbox,Russia,Europe,1,1,0,0,,net",
            ]
        )
        result = get_cities_info([url])
        self.assertListEqual([c["name"] for c in result], ["WithBoth"])

    def test_same_id_same_name_last_wins(self) -> None:
        a = self._csv_url(
            ['1,Moscow,Russia,Europe,200,12,1,40,"37,55,38,56",net1']
        )
        b = self._csv_url(
            ['1,Moscow,Russia,Europe,300,14,3,66,"37,55,38,56",net2']
        )
        result = get_cities_info([a, b])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["num_stations"], "300")
        self.assertEqual(result[0]["networks"], "net2")

    def test_same_id_different_name_releases_old_name(self) -> None:
        # After source b renames id=1 from OldName to NewName, the OldName slot
        # is freed: source c with a different id can reuse it without conflict.
        a = self._csv_url(['1,OldName,Russia,Europe,1,1,0,0,"1,2,3,4",net1'])
        b = self._csv_url(['1,NewName,Russia,Europe,1,1,0,0,"1,2,3,4",net2'])
        c = self._csv_url(['2,OldName,US,NA,1,1,0,0,"1,2,3,4",net3'])
        result = get_cities_info([a, b, c])
        by_id = {x["id"]: x["name"] for x in result}
        self.assertDictEqual(by_id, {"1": "NewName", "2": "OldName"})

    def test_different_id_same_name_evicts_old(self) -> None:
        a = self._csv_url(
            ['1,Moscow,Russia,Europe,200,12,1,40,"37,55,38,56",net1']
        )
        b = self._csv_url(
            ['2,Moscow,Russia,Europe,300,14,3,66,"37,55,38,56",net2']
        )
        result = get_cities_info([a, b])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "2")
        self.assertEqual(result[0]["num_stations"], "300")

    def test_independent_records_concatenated(self) -> None:
        a = self._csv_url(
            ['1,Moscow,Russia,Europe,200,12,1,40,"37,55,38,56",net1']
        )
        b = self._csv_url(['2,SPb,Russia,Europe,72,5,0,7,"30,59,30,60",net2'])
        result = get_cities_info([a, b])
        self.assertListEqual(
            [(c["id"], c["name"]) for c in result],
            [("1", "Moscow"), ("2", "SPb")],
        )

    def test_duplicate_id_within_single_source(self) -> None:
        # last-wins applies inside a single CSV too
        url = self._csv_url(
            [
                '1,Moscow,Russia,Europe,200,12,1,40,"37,55,38,56",net1',
                '1,Moscow,Russia,Europe,300,14,3,66,"37,55,38,56",net2',
            ]
        )
        result = get_cities_info([url])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["num_stations"], "300")
