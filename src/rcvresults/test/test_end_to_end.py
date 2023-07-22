"""
End-to-end tests using the real Excel and XML result reports.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import rcvresults.main as main
from rcvresults.main import (
    DATA_DIR_PARSED, DATA_DIR_REPORTS, DIR_NAME_2022_NOV,
)


class EndToEndTestCase(TestCase):

    """
    End-to-end test case using the real Excel and XML result reports.
    """

    def test_json_outputs(self):
        data_dir, reference_dir = (
            dir_path / DIR_NAME_2022_NOV for dir_path in (DATA_DIR_REPORTS, DATA_DIR_PARSED)
        )
        paths = main.get_excel_paths(data_dir)
        # Make sure we got all the paths
        self.assertEqual(len(paths), 6)

        for path in paths:
            with self.subTest(path=path):
                with TemporaryDirectory() as temp_dir:
                    temp_dir = Path(temp_dir)
                    output_path = main.make_rcv_json(path, parsed_dir=temp_dir)
                    reference_path = reference_dir / f'{path.stem}.json'
                    actual_text, expected_text = (
                        path.read_text() for path in (output_path, reference_path)
                    )
                    self.assertEqual(actual_text, expected_text)
