"""
Usage:

$ python src/rcvresults/main.py

"""

import logging

import rcvresults.parsing as parsing


_log = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO)
    results = parsing.parse_workbook('data/2022-11-08/da_short.xlsx')
    raise RuntimeError(results)


if __name__ == '__main__':
    main()
