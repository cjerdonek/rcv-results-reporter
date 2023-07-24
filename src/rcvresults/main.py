"""
Usage:

$ python src/rcvresults/main.py

"""

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

CONFIG_PATH = Path('config.yml')

DATA_DIR_REPORTS = Path('data-reports')
DATA_DIR_PARSED = Path('data-parsed')
# Directory containing copies of real past html results summary pages.
HTML_DIR = Path('html')

DIR_NAME_2020_NOV = '2020-11-03'
DIR_NAME_2022_FEB = '2022-02-15'
DIR_NAME_2022_NOV = '2022-11-08'

# Mapping saying what kinds of results reports (file extension) are stored
# in each election directory.
REPORT_DIR_EXTENSIONS = {
    DIR_NAME_2020_NOV: 'xml',
    DIR_NAME_2022_FEB: 'xml',
    DIR_NAME_2022_NOV: 'xlsx',
}


def get_xml_paths(dir_path):
    return utils.get_paths(dir_path, suffix='xml')


def get_excel_paths(dir_path):
    original_paths = utils.get_paths(dir_path, suffix='xlsx')
    paths = []  # the return value
    for path in original_paths:
        file_name = path.name
        if file_name.startswith('~'):
            _log.warning(f'skipping temp file: {path}')
            continue
        paths.append(path)

    return paths


def get_report_paths(parent_reports_dir, dir_name):
    data_dir = parent_reports_dir / dir_name
    extension = REPORT_DIR_EXTENSIONS[dir_name]
    _log.info(f'gathering {extension} paths from: {data_dir}')

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


def _make_index_jinja_env(snippets_dir):
    """
    Create and return a Jinja2 Environment object to use when rendering
    one of the index.html templates.
    """
    env = make_environment()
    config = utils.read_yaml(CONFIG_PATH)
    elections = config['elections']

    # TODO: don't use a nested function definition here?
    def iter_contests(election):
        dir_name = election['dir_name']
        json_dir = DATA_DIR_PARSED / dir_name
        contests = election['contests']
        for contest in contests:
            file_stem = contest['file']
            contest_url = contest['url']
            json_path = json_dir / f'{file_stem}.json'
            html_path = f'{dir_name}/{file_stem}.html'
            contest_data = utils.read_json(json_path)
            yield (html_path, contest_data, contest_url)

    def insert_html(rel_path):
        path = snippets_dir / rel_path
        html = path.read_text()
        return Markup(html)

    env.globals.update({
        'elections': elections,
        'iter_contests': iter_contests,
        'insert_html': insert_html,
    })

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
    results = utils.read_json(parsed_path)

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


def make_index_html(output_dir, template_name, snippets_dir, js_dir, env):
    """
    Args:
      js_dir: the path to the directory containing the js files, relative
        to the location of the output path.
    """
    output_path = output_dir / template_name
    _log.info(f'writing: {output_path}')

    template = env.get_template(template_name)

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

    dir_names = [DIR_NAME_2020_NOV, DIR_NAME_2022_FEB, DIR_NAME_2022_NOV]
    for dir_name in dir_names:
        make_rcv_snippets(
            parent_reports_dir=DATA_DIR_REPORTS, parent_parsed_dir=DATA_DIR_PARSED,
            parent_snippets_dir=snippets_dir, dir_name=dir_name,
        )

    # Then generate the overall pages.
    env = _make_index_jinja_env(snippets_dir=snippets_dir)
    template_names = ['index-test.html', 'index-all-rcv.html']
    for template_name in template_names:
        make_index_html(
            output_dir, template_name=template_name,
            snippets_dir=snippets_dir, js_dir=js_dir, env=env,
        )


if __name__ == '__main__':
    main()
