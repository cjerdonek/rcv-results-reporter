"""
Usage:

$ python src/rcvresults/main.py

"""

import glob
import logging
from pathlib import Path

import rcvresults.parsing as parsing


_log = logging.getLogger(__name__)


def main():
    log_format = '[{levelname}] {name}: {message}'
    logging.basicConfig(format=log_format, style='{', level=logging.INFO)

    paths = sorted(glob.glob('data/2022-11-08/*.xlsx'))
    for path in paths:
        path = Path(path)
        if path.name.startswith('~'):
            _log.warning(f'skipping temp file: {path}')
            continue

        _log.info(f'parsing: {path}')
        results = parsing.parse_workbook(path)
        candidates = results['candidates']
        _log.info(f'found: {len(candidates)} candidates')


if __name__ == '__main__':
    main()
