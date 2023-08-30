from unittest import TestCase

import rcvresults.election as election
from rcvresults.testing import TRANSLATIONS_PATH


class ModuleTestCase(TestCase):

    """
    Tests of functions in the module.
    """

    def test_make_html_base_name(self):
        cases = [
            ('rcv-complete.html', 'da_short-rounds'),
            ('rcv-summary.html', 'da_short-summary'),
        ]
        for template_name, expected in cases:
            with self.subTest(template_name=template_name):
                actual = election.make_html_base_name(
                    template_name, contest_base='da_short',
                )
                self.assertEqual(actual, expected)

    def get_label_translations(self):
        return election.read_label_translations(TRANSLATIONS_PATH)

    def test_translate_blanks(self):
        label_translations = self.get_label_translations()
        actual = election._translate_blanks(label_translations, lang_code='en')
        self.assertEqual(actual, 'Blanks (Undervotes)')

    def test_make_blanks_translations(self):
        label_translations = self.get_label_translations()
        actual = election._make_blanks_translations(label_translations)
        self.assertEqual(sorted(actual), ['en', 'es', 'tl', 'zh'])
        # Spot-check a single key-value.
        self.assertEqual(
            actual['es'],
            'Papeleta de votación en blanco (Votos por debajo del límite)',
        )

    def test_make_subtotal_translations(self):
        label_translations = self.get_label_translations()
        actual = election.make_subtotal_translations(label_translations)
        self.assertEqual(sorted(actual), [
            'blanks', 'continuing', 'exhausted', 'non_transferable', 'overvotes',
        ])
