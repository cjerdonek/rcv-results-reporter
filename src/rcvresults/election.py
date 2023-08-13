"""
Support for generating RCV HTML snippets for an election.
"""

import functools
import logging

import jinja2
from jinja2 import Environment, FileSystemLoader

import rcvresults.parsers.xml as xml_parsing
import rcvresults.parsers.xslx as excel_parsing
import rcvresults.rendering as rendering
import rcvresults.summary as summary
import rcvresults.utils as utils
from rcvresults.utils import LANG_CODE_ENGLISH

_log = logging.getLogger(__name__)


# Mapping from template name to html base name suffix.
HTML_SUFFIXES = {
    'rcv-complete.html': 'rounds',
    'rcv-summary.html': 'summary',
}


def read_election_config(config_path):
    config_data = utils.read_yaml(config_path)
    election_data = config_data['election']

    return election_data


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


def load_label_translations(translations_path):
    data = utils.read_yaml(translations_path)
    labels = data['labels']
    return labels


def load_phrases(translations_path):
    data = utils.read_yaml(translations_path)
    labels = data['labels']
    phrases = {}
    for label, translations in labels.items():
        phrase = translations[LANG_CODE_ENGLISH]
        phrases[phrase] = label

    return phrases


def make_environment(translations_path):
    env = Environment(
        loader=FileSystemLoader('templates'),
        # TODO: pass the autoescape argument?
    )

    translated_labels = load_label_translations(translations_path)
    translate_label = functools.partial(
        rendering.translate_label, translated_labels=translated_labels,
    )
    phrases = load_phrases(translations_path)
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


def _make_globals(css_dir=None):
    """
    Return the globals to pass to env.get_template().
    """
    global_vars = {
        'is_contest_leader': jinja2.pass_context(rendering.is_contest_leader),
        'get_candidate_class_prefix': (
            jinja2.pass_context(rendering.get_candidate_class_prefix)
        ),
        'candidate_was_eliminated': (
            jinja2.pass_context(rendering.candidate_was_eliminated)
        ),
    }
    if css_dir is not None:
        global_vars.update({
            'css_dir': str(css_dir),
        })

    return global_vars


def make_html_snippets(json_path, templates, output_dir, base_name):
    """
    Args:
      templates: a list of jinja2 Template objects.
      json_dir: the json output directory.
      output_dir: the html output directory.
    """
    _log.info(f'making RCV html snippets from: {json_path}')
    rcv_data = utils.read_json(json_path)
    for template in templates:
        base_name_suffix = HTML_SUFFIXES[template.name]
        html_base_name = f'{base_name}-{base_name_suffix}'
        rendering.make_rcv_contest_html(
            rcv_data, template=template, html_dir=output_dir,
            base_name=html_base_name,
        )


def process_contest(
    contest_data, reports_dir, report_suffix, templates, json_dir, output_dir,
):
    """
    Args:
      templates: a list of jinja2 Template objects.
      json_dir: the json output directory.
      output_dir: the html output directory.
    """
    base_name = contest_data['file']
    file_name = f'{base_name}.{report_suffix}'
    report_path = reports_dir / file_name
    json_path = make_rcv_json(report_path, json_dir=json_dir)
    make_html_snippets(
        json_path, templates=templates, output_dir=output_dir, base_name=base_name,
    )


def process_election(
    config_path, reports_dir, report_suffix, translations_path, output_dir,
    json_dir=None, css_dir=None,
):
    """
    Args:
      config_path: path to an election.yml config, as a Path object.
      report_suffix: a file extension specifying which RCV reports to
        read and parse. Can be one of: "xml" or "xlsx".
      json_dir: the directory to which to write the intermediate json
        files, as a Path object. Defaults to a subdirectory of the given
        output directory.
      css_dir: the path to the directory containing the default.css file,
        as a Path object, for use in the rcv-complete.html template.
        This can be a relative path.
    """
    if json_dir is None:
        json_dir = output_dir / 'json'

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    if not json_dir.exists():
        json_dir.mkdir(parents=True, exist_ok=True)

    election_data = read_election_config(config_path)
    contests_data = election_data['contests']

    env = make_environment(translations_path)
    global_vars = _make_globals(css_dir=css_dir)

    templates = [
        env.get_template(name, globals=global_vars) for name in
        ('rcv-summary.html', 'rcv-complete.html')
    ]
    for contest_data in contests_data:
        process_contest(
            contest_data, reports_dir=reports_dir, report_suffix=report_suffix,
            templates=templates, output_dir=output_dir, json_dir=json_dir,
        )