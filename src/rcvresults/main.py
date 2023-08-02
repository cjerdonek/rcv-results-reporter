"""
Usage:

$ python src/rcvresults/main.py

"""

import functools
import logging
from pathlib import Path

import jinja2
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

import rcvresults.parsers.xml as xml_parsing
import rcvresults.parsers.xslx as excel_parsing
import rcvresults.rendering as rendering
import rcvresults.summary as summary
import rcvresults.utils as utils
from rcvresults.utils import CURRENT_LANG_KEY, LANG_CODE_ENGLISH, LANGUAGES


_log = logging.getLogger(__name__)

TEMPLATE_NAME_RCV_DEMO = 'index-all-rcv.html'

CONFIG_PATH = Path('config.yml')
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

# Mapping saying what kinds of results reports (file extension) are stored
# in each election directory.
REPORT_DIR_EXTENSIONS = {
    DIR_NAME_2019_NOV: 'xml',
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
    _log.info(f'gathering {extension} reports in: {data_dir}')

    if extension == 'xlsx':
        paths = get_excel_paths(data_dir)
    else:
        assert extension == 'xml'
        paths = get_xml_paths(data_dir)

    return paths


def load_label_translations():
    data = utils.read_yaml(TRANSLATIONS_PATH)
    labels = data['labels']
    return labels


def load_phrases():
    data = utils.read_yaml(TRANSLATIONS_PATH)
    labels = data['labels']
    phrases = {}
    for label, translations in labels.items():
        phrase = translations[LANG_CODE_ENGLISH]
        phrases[phrase] = label

    return phrases


def make_environment():
    env = Environment(
        loader=FileSystemLoader('templates'),
        # TODO: pass the autoescape argument?
    )

    translated_labels = load_label_translations()
    translate_label = functools.partial(
        rendering.translate_label, translated_labels=translated_labels,
    )
    phrases = load_phrases()
    translate_phrase = functools.partial(
        rendering.translate_phrase, translated_labels=translated_labels,
        phrases=phrases,
    )

    env.filters.update({
        'format_int': rendering.format_int,
        'format_percent': rendering.format_percent,
        'TL': jinja2.pass_context(translate_label),
        'TP': jinja2.pass_context(translate_phrase),
    })
    return env


def make_rcv_json(path, json_dir):
    _log.info(f'parsing: {path}')
    suffix = path.suffix
    if suffix == '.xlsx':
        parse_report_file = excel_parsing.parse_excel_file
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

    json_path = json_dir / f'{path.stem}.json'
    _log.info(f'writing: {json_path}')
    utils.write_json(results, path=json_path)

    return json_path


def make_rcv_json_files(dir_names, parent_reports_dir, parent_json_dir):
    _log.info('starting RCV json file creation')
    for dir_name in dir_names:
        json_dir = parent_json_dir / dir_name
        if not json_dir.exists():
            json_dir.mkdir(parents=True)

        report_paths = get_report_paths(parent_reports_dir, dir_name=dir_name)
        for report_path in report_paths:
            make_rcv_json(report_path, json_dir=json_dir)


def render_template(template, output_path, context=None, lang_code=None):
    """
    Note: This function modifies the given context by adding a "lang" key!
    """
    if context is None:
        context = {}
    if lang_code is not None:
        context[CURRENT_LANG_KEY] = lang_code

    _log.info(f'rendering template to (lang={lang_code!r}): {output_path}')
    html = template.render(context)
    output_path.write_text(html)


def make_rcv_contest_html(json_path, template, html_dir):
    """
    Create the html snippets for an RCV contest, one for each language.

    Args:
      json_path: the path to the json file containing the data parsed
        from the result report for the contest.
      html_dir: the directory to which to write the rendered html files.
    """
    _log.info(f'making RCV html from: {json_path}')
    results = utils.read_json(json_path)
    base_name = json_path.stem

    for lang_code in LANGUAGES:
        file_name = f'{base_name}-{lang_code}.html'
        output_path = html_dir / file_name
        # Make a copy since render_template() adds to the context.
        context = results.copy()
        render_template(
            template, output_path=output_path, context=context,
            lang_code=lang_code,
        )


def make_rcv_snippets(parent_json_dir, parent_snippets_dir, dir_name):
    json_dir, html_dir = (
        parent_dir / dir_name for parent_dir in
        (parent_json_dir, parent_snippets_dir)
    )
    # Make sure the html output directory exists.
    if not html_dir.exists():
        html_dir.mkdir(parents=True)

    env = make_environment()
    template = env.get_template('rcv-summary.html')

    json_paths = utils.get_paths(json_dir, suffix='json')
    for json_path in json_paths:
        make_rcv_contest_html(json_path, template=template, html_dir=html_dir)


def make_all_rcv_snippets(output_dir, dir_names, parent_json_dir):
    _log.info('starting RCV html snippet creation')
    # This is the parent directory to which to write the intermediate
    # HTML snippets.
    snippets_dir = output_dir / 'rcv-snippets'

    for dir_name in dir_names:
        make_rcv_snippets(
            parent_json_dir=parent_json_dir,
            parent_snippets_dir=snippets_dir, dir_name=dir_name,
        )

    return snippets_dir


def _make_index_jinja_env(snippets_dir):
    """
    Create and return a Jinja2 Environment object to use when rendering
    one of the index.html templates.
    """
    env = make_environment()

    def insert_html(rel_path):
        path = snippets_dir / rel_path
        html = path.read_text()
        return Markup(html)

    env.globals['insert_html'] = insert_html

    return env


def make_index_html(
    output_dir, template, snippets_dir, js_dir, env, output_name=None,
    lang_code=None,
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
    render_template(
        template, output_path=output_path, context=context,
        lang_code=lang_code,
    )


def make_test_index_html(output_dir, snippets_dir, js_dir):
    _log.info(f'creating: test index html')
    env = _make_index_jinja_env(snippets_dir=snippets_dir)
    template = env.get_template('index-test.html')

    make_index_html(
        output_dir, template=template, snippets_dir=snippets_dir,
        js_dir=js_dir, env=env,
    )


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


def make_rcv_demo(output_dir, snippets_dir, js_dir, parent_json_dir):
    _log.info(f'creating: RCV demo index html')

    env = _make_index_jinja_env(snippets_dir=snippets_dir)

    config = utils.read_yaml(CONFIG_PATH)
    elections = config['elections']
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
            output_dir, template=template, snippets_dir=snippets_dir,
            js_dir=js_dir, env=env, output_name=output_name,
            lang_code=lang_code,
        )


def main():
    log_format = '[{levelname}] {name}: {message}'
    logging.basicConfig(format=log_format, style='{', level=logging.INFO)

    output_dir = DEFAULT_HTML_OUTPUT_DIR
    # Start with the parent ("..") to get from output_dir back to the
    # repo root.
    js_dir = Path('..') / HTML_DIR / DIR_NAME_2022_NOV / 'js'
    parent_json_dir = DATA_DIR_JSON

    dir_names = [
        DIR_NAME_2019_NOV,
        DIR_NAME_2020_NOV,
        DIR_NAME_2022_FEB,
        DIR_NAME_2022_NOV,
    ]
    # First generate the RCV json files.
    make_rcv_json_files(
        dir_names=dir_names, parent_reports_dir=DATA_DIR_REPORTS,
        parent_json_dir=parent_json_dir,
    )
    # Next, generate the RCV summary html snippets.
    snippets_dir = make_all_rcv_snippets(
        output_dir, dir_names=dir_names, parent_json_dir=parent_json_dir,
    )

    # Finally, generate the index pages.
    make_test_index_html(output_dir, snippets_dir=snippets_dir, js_dir=js_dir)
    make_rcv_demo(
        output_dir, snippets_dir=snippets_dir, js_dir=js_dir,
        parent_json_dir=parent_json_dir,
    )


if __name__ == '__main__':
    main()
