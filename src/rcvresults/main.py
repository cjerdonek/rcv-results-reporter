"""
Usage:

$ python src/rcvresults/main.py

"""

import glob
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

import rcvresults.parsers.xslx as excel_parsing
import rcvresults.rendering as rendering


_log = logging.getLogger(__name__)


def make_environment():
    env = Environment(
        loader=FileSystemLoader('templates'),
        # TODO: pass the autoescape argument?
    )
    return env


def make_rcv_snippets(data_dir, output_dir):
    env = make_environment()
    template = env.get_template('rcv-summary.html')

    glob_path = data_dir / '*.xlsx'
    paths = glob.glob(str(glob_path))
    for path in sorted(paths):
        path = Path(path)
        file_name = path.name
        if file_name.startswith('~'):
            _log.warning(f'skipping temp file: {path}')
            continue

        _log.info(f'parsing: {path}')
        results = excel_parsing.parse_excel_file(path)
        contest_name = results['contest_name']
        candidates = results['candidates']
        _log.info(f'parsed contest: {contest_name!r} ({len(candidates)} candidates)')

        output_path = output_dir / f'{path.stem}.html'
        _log.info(f'writing: {output_path}')
        rendering.render_contest(template, results, path=output_path)


def make_index_html(output_path, rcv_html_dir):
    def insert_html(file_name):
        path = rcv_html_dir / file_name
        html = path.read_text()
        return Markup(html)

    env = make_environment()
    env.globals['insert_html'] = insert_html
    template = env.get_template('index-test.html')

    html = template.render()
    output_path.write_text(html)


def main():
    log_format = '[{levelname}] {name}: {message}'
    logging.basicConfig(format=log_format, style='{', level=logging.INFO)

    # First generate the RCV summary snippets.
    output_dir = Path('output')
    rcv_html_dir = output_dir / 'rcv-html'
    if not rcv_html_dir.exists():
        rcv_html_dir.mkdir(parents=True)

    data_dir = Path('data/2022-11-08')
    make_rcv_snippets(data_dir=data_dir, output_dir=rcv_html_dir)

    # Then generate the overall page.
    output_dir = Path('html/2022-11-08')
    output_path = output_dir / 'index-generated.html'
    make_index_html(output_path, rcv_html_dir=rcv_html_dir)


if __name__ == '__main__':
    main()
