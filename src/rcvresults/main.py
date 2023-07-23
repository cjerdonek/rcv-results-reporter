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

import rcvresults.parsers.xml as xml_parsing
import rcvresults.parsers.xslx as excel_parsing
import rcvresults.rendering as rendering
import rcvresults.summary as summary
import rcvresults.utils as utils


_log = logging.getLogger(__name__)

DATA_DIR_REPORTS = Path('data-reports')
DATA_DIR_PARSED = Path('data-parsed')
# Directory containing copies of real past html results summary pages.
HTML_DIR = Path('html')

DIR_NAME_2020_NOV = '2020-11-03'
DIR_NAME_2022_NOV = '2022-11-08'

# Mapping saying what kinds of results reports (file extension) are stored
# in each election directory.
REPORT_DIR_EXTENSIONS = {
    DIR_NAME_2020_NOV: 'xml',
    DIR_NAME_2022_NOV: 'xlsx',
}


def get_xml_paths(dir_path):
    glob_path = dir_path / '*.xml'
    raw_paths = glob.glob(str(glob_path))
    paths = [Path(raw_path) for raw_path in sorted(raw_paths)]

    return paths


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


def get_report_paths(parent_reports_dir, dir_name):
    data_dir = parent_reports_dir / dir_name

    extension = REPORT_DIR_EXTENSIONS[dir_name]
    if extension == 'xlsx':
        paths = get_excel_paths(data_dir)
    else:
        assert extension == 'xml'
        paths = get_xml_paths(data_dir)

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
    suffix = path.suffix
    if suffix == '.xlsx':
        parse_report_file = excel_parsing.parse_excel_file
        results = excel_parsing.parse_excel_file(path)
    else:
        assert suffix == '.xml'
        parse_report_file = xml_parsing.parse_xml_file

    try:
        results = parse_report_file(path)
    except Exception:
        raise RuntimeError(f'error parsing report file: {path}')

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


def make_rcv_snippets(
    parent_reports_dir, parent_parsed_dir, parent_snippets_dir, dir_name,
):
    parsed_dir, html_dir = (
        parent_dir / dir_name for parent_dir in
        (parent_parsed_dir, parent_snippets_dir)
    )

    # Make sure the intermediate output directories exist.
    if not parsed_dir.exists():
        parsed_dir.mkdir(parents=True)
    if not html_dir.exists():
        html_dir.mkdir(parents=True)

    env = make_environment()
    template = env.get_template('rcv-summary.html')

    paths = get_report_paths(parent_reports_dir, dir_name=dir_name)

    for path in paths:
        process_rcv_contest(
            path, template=template, parsed_dir=parsed_dir, html_dir=html_dir,
        )


def make_index_html(output_path, snippets_dir, js_dir):
    """
    Args:
      js_dir: the path to the directory containing the js files, relative
        to the location of the output path.
    """
    def insert_html(rel_path):
        path = snippets_dir / rel_path
        html = path.read_text()
        return Markup(html)

    env = make_environment()
    env.globals['insert_html'] = insert_html
    template = env.get_template('index-test.html')

    context = {
        'js_dir': str(js_dir),
    }
    html = template.render(context)
    output_path.write_text(html)


def main():
    log_format = '[{levelname}] {name}: {message}'
    logging.basicConfig(format=log_format, style='{', level=logging.INFO)

    output_dir = Path('output')
    # Start with the parent ("..") to get from output_dir back to the
    # repo root.
    js_dir = Path('..') / HTML_DIR / DIR_NAME_2022_NOV / 'js'

    # First generate the RCV summary snippets.
    # This is the parent directory to which to write the intermediate
    # HTML snippets.
    snippets_dir = output_dir / 'rcv-snippets'

    # TODO: uncomment this.
    dir_names = [DIR_NAME_2020_NOV, DIR_NAME_2022_NOV]
    # dir_names = [DIR_NAME_2022_NOV]
    for dir_name in dir_names:
        make_rcv_snippets(
            parent_reports_dir=DATA_DIR_REPORTS, parent_parsed_dir=DATA_DIR_PARSED,
            parent_snippets_dir=snippets_dir, dir_name=dir_name,
        )

    # Then generate the overall page.
    output_path = output_dir / 'index.html'
    _log.info(f'writing: {output_path}')
    make_index_html(output_path, snippets_dir=snippets_dir, js_dir=js_dir)


if __name__ == '__main__':
    main()
