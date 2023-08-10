"""
Recreate the demo page.

Usage:

  $ python src/rcvresults/demo.py

"""

import functools
import logging
from pathlib import Path

import jinja2
from markupsafe import Markup

import rcvresults.main as main_mod
import rcvresults.rendering as rendering
import rcvresults.utils as utils
from rcvresults.utils import CURRENT_LANG_KEY, LANGUAGES


_log = logging.getLogger(__name__)

TEMPLATE_NAME_RCV_DEMO = 'index-all-rcv.html'

CONFIG_DIR = Path('config')
TRANSLATIONS_PATH = Path('translations.yml')

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
    for dir_name, config_path in config_paths.items():
        _log.info(f'starting election: {dir_name}')
        report_suffix = REPORT_DIR_EXTENSIONS[dir_name]
        reports_dir, json_dir, html_dir = (
            parent_dir / dir_name for parent_dir in
            (DATA_DIR_REPORTS, parent_json_dir, parent_snippets_dir)
        )
        main_mod.process_election(
            config_path=config_path, reports_dir=reports_dir,
            report_suffix=report_suffix, translations_path=translations_path,
            json_dir=json_dir, output_dir=html_dir,
        )


def _make_index_jinja_env(snippets_dir):
    """
    Create and return a Jinja2 Environment object to use when rendering
    one of the index.html templates.
    """
    env = main_mod.make_environment(TRANSLATIONS_PATH)

    def insert_html(rel_path):
        path = snippets_dir / rel_path
        html = path.read_text()
        return Markup(html)

    env.globals['insert_html'] = insert_html

    return env


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

    output_path = output_dir / output_name

    context = {'js_dir': str(js_dir)}
    rendering.render_template(
        template, output_path=output_path, context=context,
        lang_code=lang_code,
    )


def make_test_index_html(output_dir, snippets_dir, js_dir):
    _log.info(f'creating: test index html')
    env = _make_index_jinja_env(snippets_dir=snippets_dir)
    template = env.get_template('index-test.html')
    make_index_html(output_dir, template=template, js_dir=js_dir, env=env)


def _iter_contests(context, election, parent_json_dir):
    """
    Yield information about each contest in an election.
    """
    lang_code = context[CURRENT_LANG_KEY]
    dir_name = election['dir_name']
    json_dir = parent_json_dir / dir_name
    contests = election['contests']
    for contest in contests:
        file_stem = contest['file']
        contest_url = contest['url']
        json_path = json_dir / f'{file_stem}.json'
        html_path = f'{dir_name}/{file_stem}-{lang_code}.html'
        contest_data = utils.read_json(json_path)
        yield (html_path, contest_data, contest_url)


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
        election_config = main_mod.read_election_config(config_path)

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

    # Create a single "elections" list for use from the template.
    elections = _build_elections_list(config_paths)

    iter_contests = functools.partial(
        _iter_contests, parent_json_dir=parent_json_dir,
    )

    env.globals.update({
        'elections': elections,
        'iter_contests': jinja2.pass_context(iter_contests),
        'iter_languages': jinja2.pass_context(rendering.iter_languages),
    })

    template = env.get_template(TEMPLATE_NAME_RCV_DEMO)

    for lang_code in LANGUAGES:
        output_name = rendering.get_index_name(lang_code)
        make_index_html(
            output_dir, template=template, js_dir=js_dir, env=env,
            output_name=output_name, lang_code=lang_code,
        )


def main():
    log_format = '[{levelname}] {name}: {message}'
    logging.basicConfig(format=log_format, style='{', level=logging.INFO)

    parent_json_dir = DATA_DIR_JSON

    output_dir = DEFAULT_HTML_OUTPUT_DIR
    # This is the parent directory to which to write the intermediate
    # RCV HTML snippets.
    snippets_dir = output_dir / 'rcv-snippets'

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
    make_test_index_html(output_dir, snippets_dir=snippets_dir, js_dir=js_dir)

    make_rcv_demo(
        config_paths, snippets_dir=snippets_dir, js_dir=js_dir,
        parent_json_dir=parent_json_dir, output_dir=output_dir,
    )


if __name__ == '__main__':
    main()
