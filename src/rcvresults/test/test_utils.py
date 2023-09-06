"""
Unit tests of rcvresults/utils.py.
"""

from unittest import TestCase

import rcvresults.utils as utils


class FunctionTestCase(TestCase):

    def test_make_html_page_name(self):
        actual = utils.make_html_page_name('rcv-contest', lang_code='en')
        self.assertEqual(actual, 'rcv-contest-en.html')

    def test_make_page_names(self):
        actual = utils.make_page_names('rcv-contest')
        expected = {
            'en': 'rcv-contest-en.html',
            'es': 'rcv-contest-es.html',
            'tl': 'rcv-contest-tl.html',
            'zh': 'rcv-contest-zh.html',
        }
        self.assertEqual(actual, expected)
