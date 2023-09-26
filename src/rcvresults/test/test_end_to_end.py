"""
End-to-end tests using the real Excel and XML result reports.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import rcvresults.election as election
import rcvresults.main as main
import rcvresults.scripts.build_demo as demo
from rcvresults.scripts.build_demo import (
    DATA_DIR_JSON, DATA_DIR_REPORTS, DIR_NAME_2020_NOV, DIR_NAME_2022_NOV,
)


class EndToEndTestCase(TestCase):

    """
    End-to-end test case using the real Excel and XML result reports.
    """

    def _test_json_outputs(self, dir_name, expected_count):
        reference_dir = DATA_DIR_JSON / dir_name
        paths = demo.get_report_paths(DATA_DIR_REPORTS, dir_name=dir_name)
        # Make sure we got all the paths
        self.assertEqual(len(paths), expected_count)

        for path in paths:
            with self.subTest(path=path):
                with TemporaryDirectory() as temp_dir:
                    temp_dir = Path(temp_dir)
                    output_path = election.make_rcv_json(
                        path, output_dir=temp_dir,
                    )
                    reference_path = reference_dir / f'{path.stem}.json'
                    actual_text, expected_text = (
                        path.read_text() for path in (output_path, reference_path)
                    )
                    self.assertEqual(actual_text, expected_text)

    def test_json_outputs_2020_november(self):
        # This directory has: 20201201_d1_short.xml on up to
        # 20201201_d11_short.xml.
        self._test_json_outputs(dir_name=DIR_NAME_2020_NOV, expected_count=6)

    def test_json_outputs_2022_november(self):
        # This directory has: d4_short.xlsx on up to d10_short.xlsx,
        # as well as da_short.xlsx and defender_short.xlsx.
        self._test_json_outputs(dir_name=DIR_NAME_2022_NOV, expected_count=6)
