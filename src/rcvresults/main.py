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


_log = logging.getLogger(__name__)


def write_json(data, path):
    with path.open('w') as f:
        json.dump(data, f, indent='    ', sort_keys=True)


def make_environment():
    env = Environment(
        loader=FileSystemLoader('templates'),
        # TODO: pass the autoescape argument?
    )
    env.filters['format_int'] = rendering.format_int
    env.filters['format_percent'] = rendering.format_percent

    return env


def process_rcv_contest(path, template, parsed_dir, html_dir):
    """
    Args:
      parsed_dir: the directory to which to write the data parsed from the
        results reports.
      html_dir: the directory to which to write the rendered html files.
    """
    _log.info(f'parsing: {path}')
    results = excel_parsing.parse_excel_file(path)
    metadata = results['_metadata']
    contest_name = metadata['contest_name']
    candidates = results['candidates']
    _log.info(f'parsed contest: {contest_name!r} ({len(candidates)} candidates)')

    parsed_path = parsed_dir / f'{path.stem}.json'
    write_json(results, path=parsed_path)

    output_path = html_dir / f'{path.stem}.html'
    _log.info(f'writing: {output_path}')
    rendering.render_contest(template, results, path=output_path)


def make_rcv_snippets(data_dir, parsed_dir, html_dir):
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

    dir_name = '2022-11-08'
    data_dir = Path('data-reports') / dir_name

    # First generate the RCV summary snippets.
    parsed_dir = Path('data-parsed') / dir_name
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
    output_dir = Path('html/2022-11-08')
    output_path = output_dir / 'index-generated.html'
    make_index_html(output_path, rcv_html_dir=rcv_html_dir)


if __name__ == '__main__':
    main()
