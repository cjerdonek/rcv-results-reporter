from unittest import TestCase

import rcvresults.parsers.xslx as excel_parsing


class FunctionTestCase(TestCase):

    """
    Tests of functions in the module.
    """

    def test_iter_triples(self):
        cases = [
            (0, []),
            (1, [(0, None, None)]),
            (2, [(0, 1, None)]),
            (3, [(0, 1, 2)]),
            (4, [(0, 1, 2), (3, None, None)]),
            (5, [(0, 1, 2), (3, 4, None)]),
            (6, [(0, 1, 2), (3, 4, 5)]),
            (7, [(0, 1, 2), (3, 4, 5), (6, None, None)]),
        ]
        for n, expected in cases:
            with self.subTest(n=n):
                # We need to call iter() since range() is not an iterator.
                iterator = iter(range(n))
                actual = list(excel_parsing.iter_triples(iterator))
                self.assertEqual(actual, expected)
