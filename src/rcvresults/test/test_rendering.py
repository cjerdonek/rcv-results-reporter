"""
Unit tests of rcvresults/rendering.py.
"""

from unittest import TestCase

import rcvresults.election as election
import rcvresults.rendering as rendering
from rcvresults.testing import TRANSLATIONS_PATH


class FunctionTestCase(TestCase):

    def test_translate_label_tooltip(self):
        label_translations = election.read_label_translations(TRANSLATIONS_PATH)
        actual = rendering.translate_label_tooltip(
            None, label='total_continuing', lang='en', label_translations=label_translations,
        )
        self.assertEqual(actual, 'The number of ballots in the round counting towards some candidate.')
