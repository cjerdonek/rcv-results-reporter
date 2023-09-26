"""
Recreate the demo page.

Usage:

  $ python src/rcvresults/scripts/build_demo.py

"""

import argparse
import functools
import logging
from pathlib import Path

import jinja2
from markupsafe import Markup

import rcvresults.election as election_mod
from rcvresults.election import HTML_OUTPUT_DIR_NAMES
import rcvresults.rendering as rendering
from rcvresults.rendering import (
    CONTEXT_KEY_CURRENT_LANG, CONTEXT_KEY_PAGE_NAMES,
)
from rcvresults.testing import TRANSLATIONS_PATH
import rcvresults.utils as utils
from rcvresults.utils import LANG_CODE_ENGLISH, LANGUAGES


_log = logging.getLogger(__name__)

DESCRIPTION = """\
Build the demo.
"""

TEMPLATE_NAME_RCV_DEMO = 'index-all-rcv.html'
RCV_SNIPPETS_DIR_NAME = 'rcv-snippets'

CONFIG_DIR = Path('config')

DATA_DIR = Path('data')
DATA_DIR_REPORTS = DATA_DIR / 'input-reports'
DATA_DIR_JSON = DATA_DIR / 'output-json'
DEFAULT_HTML_OUTPUT_DIR = DATA_DIR / 'output-html'

# Directory containing copies of real past html results summary pages.
HTML_DIR = Path('sample-html')

DIR_NAME_2019_NOV = '2019-11-05'
DIR_NAME_2020_NOV = '2020-11-03'
DIR_NAME_2022_FEB = '2022-02-15'
DIR_NAME_2022_NOV = '2022-11-08'

# Mapping saying what kind of results reports (file extension) should
# be read and parsed from each election directory.
REPORT_DIR_EXTENSIONS = {
    DIR_NAME_2019_NOV: 'xml',
    DIR_NAME_2020_NOV: 'xml',
    DIR_NAME_2022_FEB: 'xml',
    # The November 2022 election doesn't have XML files posted -- only Excel.
    DIR_NAME_2022_NOV: 'xlsx',
}


def get_config_path(dir_name):
    return CONFIG_DIR / f'election-{dir_name}.yml'


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


# TODO: remove this?
def get_report_paths(parent_reports_dir, dir_name):
    data_dir = parent_reports_dir / dir_name
    extension = REPORT_DIR_EXTENSIONS[dir_name]
    _log.info(f'gathering {extension} reports in: {data_dir}')

    if extension == 'xlsx':
        paths = get_excel_paths(data_dir)
    else:
        assert extension == 'xml'
        paths = get_xml_paths(data_dir)

    return paths


def make_all_rcv_snippets(
    config_paths, parent_snippets_dir, parent_json_dir, translations_path,
):
    """
    Args:
      config_paths: a dict mapping dir_name to config_path.
      parent_snippets_dir: the parent directory to which to write the
        intermediate RCV HTML snippets.
    """
    css_dir = '../../..'
    for dir_name, config_path in config_paths.items():
        _log.info(f'starting election: {dir_name}')
        report_suffix = REPORT_DIR_EXTENSIONS[dir_name]
        reports_dir, json_dir, html_snippets_dir = (
            parent_dir / dir_name for parent_dir in
            (DATA_DIR_REPORTS, parent_json_dir, parent_snippets_dir)
        )
        election_mod.process_election(
            config_path=config_path, reports_dir=reports_dir,
            report_suffix=report_suffix, translations_path=translations_path,
            output_dir=html_snippets_dir, json_dir=json_dir, css_dir=css_dir,
        )


def _make_index_jinja_env(snippets_dir):
    """
    Create and return a Jinja2 Environment object to use when rendering
    one of the index.html templates.
    """
    env = election_mod.make_environment(TRANSLATIONS_PATH)

    def insert_html(rel_path):
        path = snippets_dir / rel_path
        html = path.read_text()
        return Markup(html)

    env.globals['insert_html'] = insert_html

    return env


def get_index_name(lang_code):
    """
    Return the name of the index.html page, for the given language.
    """
    if lang_code == LANG_CODE_ENGLISH:
        return 'index.html'

    return f'index-{lang_code}.html'


def make_index_page_names():
    return {
        lang_code: get_index_name(lang_code) for lang_code in LANGUAGES
    }


def make_index_html(
    output_dir, template, js_dir, env, output_name=None, lang_code=None,
):
    """
    Args:
      js_dir: the path to the directory containing the js files, relative
        to the location of the output path.
    """
    if output_name is None:
        output_name = template.name

    context = {'js_dir': str(js_dir)}
    output_path = output_dir / output_name
    rendering.render_template(
        template, output_path=output_path, context=context,
        lang_code=lang_code,
    )


def make_test_index_html(output_dir, snippets_dir, js_dir):
    _log.info(f'creating: test index html')
    env = _make_index_jinja_env(snippets_dir=snippets_dir)
    template = env.get_template('index-test.html')
    make_index_html(output_dir, template=template, js_dir=js_dir, env=env)


def _get_rounds_report_url(context, election, contest_base):
    """
    Return the URL to an html round-by-round report for a contest, as a
    relative URL. For example, "rcv-snippets/2022-11-08/da_short-rounds-en.html".

    Args:
      election_dir_name: for example, "2022-11-08".
      contest_base: the contest base name (e.g. "da_short").
    """
    # TODO: stop hard-coding this template name.
    template_name = 'rcv-complete.html'
    lang_code = context[CONTEXT_KEY_CURRENT_LANG]
    dir_name = election['dir_name']
    subdir_name = HTML_OUTPUT_DIR_NAMES[template_name]
    # This is the output file stem without the language code suffix.
    html_base_name = election_mod.make_html_base_name(
        template_name, contest_base=contest_base,
    )
    file_name = utils.make_html_page_name(html_base_name, lang_code=lang_code)
    rel_path = Path(RCV_SNIPPETS_DIR_NAME) / dir_name / subdir_name / file_name

    return str(rel_path)


def _get_contest_summary_path(context, election, contest_base):
    """
    Return the path to an html summary file for a contest, as a relative
    string path. For example, "2022-11-08/da_short-summary-en.html".

    Args:
      election_dir_name: for example, "2022-11-08".
      contest_base: the contest base name (e.g. "da_short").
    """
    # TODO: stop hard-coding this template name.
    template_name = 'rcv-summary.html'
    lang_code = context[CONTEXT_KEY_CURRENT_LANG]
    dir_name = election['dir_name']
    subdir_name = HTML_OUTPUT_DIR_NAMES[template_name]
    # This is the output file stem without the language code suffix.
    html_base_name = election_mod.make_html_base_name(
        template_name, contest_base=contest_base,
    )
    file_name = utils.make_html_page_name(html_base_name, lang_code=lang_code)
    rel_path = Path(dir_name) / subdir_name / file_name

    return str(rel_path)


def _iter_contests(election, parent_json_dir):
    """
    Yield information about each contest in an election.
    """
    dir_name = election['dir_name']
    json_dir = parent_json_dir / dir_name
    contests = election['contests']
    for contest in contests:
        base_name = contest['file_stem']
        pdf_url = contest['pdf_url']
        json_path = json_dir / f'{base_name}.json'
        contest_data = utils.read_json(json_path)

        yield (base_name, contest_data, pdf_url)


def _build_elections_list(config_paths):
    """
    Return the elections to include in the demo page, as a list of election
    configs.

    Args:
      config_paths: a dict mapping dir_name to config_path.
    """
    elections = []
    for dir_name, config_path in config_paths.items():
        _log.info(f'starting election: {dir_name}')
        election_config = election_mod.read_election_config(config_path)

        # TODO: should dir_name be stored here?
        election_config['dir_name'] = dir_name
        elections.append(election_config)

    return elections


def make_rcv_demo(
    config_paths, snippets_dir, js_dir, parent_json_dir, output_dir,
):
    """
    Args:
      config_paths: a dict mapping dir_name to config_path.
    """
    _log.info(f'creating: RCV demo index html')
    env = _make_index_jinja_env(snippets_dir=snippets_dir)

    page_names = make_index_page_names()
    # Create a single "elections" list for use from the template.
    elections = _build_elections_list(config_paths)

    iter_contests = functools.partial(
        _iter_contests, parent_json_dir=parent_json_dir,
    )

    global_vars = {
        'elections': elections,
        CONTEXT_KEY_PAGE_NAMES: page_names,
        'get_rounds_url': jinja2.pass_context(_get_rounds_report_url),
        'get_summary_path': jinja2.pass_context(_get_contest_summary_path),
        'iter_contests': iter_contests,
        'iter_languages': jinja2.pass_context(rendering.iter_languages),
    }

    template = env.get_template(TEMPLATE_NAME_RCV_DEMO, globals=global_vars)

    for lang_code in LANGUAGES:
        output_name = get_index_name(lang_code)
        make_index_html(
            output_dir, template=template, js_dir=js_dir, env=env,
            output_name=output_name, lang_code=lang_code,
        )


def make_arg_parser():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        '--html-output-dir', metavar='OUTPUT_DIR', help=(
            'path to the html output directory. '
            f'Defaults to: {DEFAULT_HTML_OUTPUT_DIR}.'
        ), default=DEFAULT_HTML_OUTPUT_DIR,
    )
    return parser


# TODO: allow specifying the json directory, or make it a subdirectory
#  of the given output directory if one is provided.
def main():
    parser = make_arg_parser()
    args = parser.parse_args()

    log_format = '[{levelname}] {name}: {message}'
    logging.basicConfig(format=log_format, style='{', level=logging.INFO)

    parent_json_dir = DATA_DIR_JSON
    html_output_dir = Path(args.html_output_dir)
    # This is the parent directory to which to write the intermediate
    # RCV HTML snippets.
    snippets_dir = html_output_dir / RCV_SNIPPETS_DIR_NAME

    # We have a symlink at "data/output-html/js" that points to
    # "sample-html/2022-11-08/js" (as a relative path).
    js_dir = Path('js')

    # The order of this list controls the order the elections should be
    # listed on the demo page.
    dir_names = [
        DIR_NAME_2022_NOV,
        DIR_NAME_2022_FEB,
        DIR_NAME_2020_NOV,
        DIR_NAME_2019_NOV,
    ]
    config_paths = {
        dir_name: get_config_path(dir_name) for dir_name in dir_names
    }

    # First generate the RCV summary html snippets for all the elections.
    make_all_rcv_snippets(
        config_paths, parent_snippets_dir=snippets_dir,
        parent_json_dir=parent_json_dir, translations_path=TRANSLATIONS_PATH,
    )

    # Next, generate the index html pages.
    # TODO: check that this still works.
    make_test_index_html(
        html_output_dir, snippets_dir=snippets_dir, js_dir=js_dir,
    )

    make_rcv_demo(
        config_paths, snippets_dir=snippets_dir, js_dir=js_dir,
        parent_json_dir=parent_json_dir, output_dir=html_output_dir,
    )


if __name__ == '__main__':
    main()
