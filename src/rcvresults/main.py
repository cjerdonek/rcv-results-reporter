"""
Usage:

$ python src/rcvresults/main.py

"""

import glob
import json
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

import rcvresults.parsers.xslx as excel_parsing
import rcvresults.rendering as rendering
import rcvresults.summary as summary
import rcvresults.utils as utils


_log = logging.getLogger(__name__)

DATA_DIR_REPORTS = Path('data-reports')
DATA_DIR_PARSED = Path('data-parsed')

DIR_NAME_2022_NOV = '2022-11-08'


def get_excel_paths(dir_path):
    glob_path = dir_path / '*.xlsx'
    raw_paths = glob.glob(str(glob_path))
    paths = []
    for raw_path in sorted(raw_paths):
        path = Path(raw_path)
        file_name = path.name
        if file_name.startswith('~'):
            _log.warning(f'skipping temp file: {path}')
            continue
        paths.append(path)

    return paths


def make_environment():
    env = Environment(
        loader=FileSystemLoader('templates'),
        # TODO: pass the autoescape argument?
    )
    env.filters['format_int'] = rendering.format_int
    env.filters['format_percent'] = rendering.format_percent

    return env


def make_rcv_json(path, parsed_dir):
    _log.info(f'parsing: {path}')
    results = excel_parsing.parse_excel_file(path)
    metadata = results['_metadata']
    contest_name = metadata['contest_name']
    candidates = results['candidates']
    _log.info(f'parsed contest: {contest_name!r} ({len(candidates)} candidates)')
    summary.add_summary(results)

    parsed_path = parsed_dir / f'{path.stem}.json'
    utils.write_json(results, path=parsed_path)

    return parsed_path


def process_rcv_contest(path, template, parsed_dir, html_dir):
    """
    Args:
      parsed_dir: the directory to which to write the data parsed from the
        results reports.
      html_dir: the directory to which to write the rendered html files.
    """
    parsed_path = make_rcv_json(path, parsed_dir=parsed_dir)
    with parsed_path.open() as f:
        results = json.load(f)

    output_path = html_dir / f'{path.stem}.html'
    _log.info(f'writing: {output_path}')
    rendering.render_contest(template, results, path=output_path)


def make_rcv_snippets(data_dir, parsed_dir, html_dir):
    env = make_environment()
    template = env.get_template('rcv-summary.html')

    paths = get_excel_paths(data_dir)
    for path in paths:
        process_rcv_contest(
            path, template=template, parsed_dir=parsed_dir, html_dir=html_dir,
        )


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

    dir_name = DIR_NAME_2022_NOV
    data_dir = DATA_DIR_REPORTS / dir_name

    # First generate the RCV summary snippets.
    parsed_dir = DATA_DIR_PARSED / dir_name
    # TODO: incorporate dir_name into the output directory?
    output_dir = Path('output')
    rcv_html_dir = output_dir / 'rcv-html'

    if not parsed_dir.exists():
        parsed_dir.mkdir(parents=True)
    if not rcv_html_dir.exists():
        rcv_html_dir.mkdir(parents=True)

    make_rcv_snippets(
        data_dir=data_dir, parsed_dir=parsed_dir, html_dir=rcv_html_dir,
    )

    # Then generate the overall page.
    output_dir = Path('html') / dir_name
    output_path = output_dir / 'index-generated.html'
    make_index_html(output_path, rcv_html_dir=rcv_html_dir)


if __name__ == '__main__':
    main()
