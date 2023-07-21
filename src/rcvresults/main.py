"""
Usage:

$ python src/rcvresults/main.py

"""

import glob
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

import rcvresults.parsing as parsing
import rcvresults.rendering as rendering


_log = logging.getLogger(__name__)


def main():
    log_format = '[{levelname}] {name}: {message}'
    logging.basicConfig(format=log_format, style='{', level=logging.INFO)

    env = Environment(
        loader=FileSystemLoader('templates'),
        # TODO: pass the autoescape argument.
    )
    template = env.get_template('rcv-summary.html')

    output_dir = Path('output')
    if not output_dir.exists():
        output_dir.mkdir()

    paths = sorted(glob.glob('data/2022-11-08/*.xlsx'))
    for path in paths:
        path = Path(path)
        file_name = path.name
        if file_name.startswith('~'):
            _log.warning(f'skipping temp file: {path}')
            continue

        _log.info(f'parsing: {path}')
        results = parsing.parse_workbook(path)
        candidates = results['candidates']
        _log.info(f'found: {len(candidates)} candidates')

        output_path = output_dir / f'{path.stem}.html'
        _log.info(f'writing to: {output_path}')
        rendering.render_contest(template, results, path=output_path)


if __name__ == '__main__':
    main()
