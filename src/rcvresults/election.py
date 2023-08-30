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
from rcvresults.utils import NonCandidateLabel, LANG_CODE_ENGLISH, LANGUAGES


_log = logging.getLogger(__name__)


# Mapping from subtotal key-name to translations.yml label, for the
# key-names that are simple one-to-one translations. The only subtotal
# key-name not included below is NonCandidateLabel.BLANK ("blanks").
SUBTOTAL_KEYS = {
    NonCandidateLabel.CONTINUING: 'total_continuing',
    NonCandidateLabel.EXHAUSTED: 'total_exhausted',
    NonCandidateLabel.OVERVOTE: 'total_overvotes',
    NonCandidateLabel.NON_TRANSFERABLE: 'total_non_transferable',
}


# Mapping from template name to the name of the subdirectory of the output
# directory to which instances of that template should be rendered.
HTML_OUTPUT_DIR_NAMES = {
    'rcv-complete.html': 'round-pages',
    'rcv-summary.html': 'summary-tables',
}
# Mapping from template name to html base name suffix.
HTML_FILE_SUFFIXES = {
    'rcv-complete.html': 'rounds',
    'rcv-summary.html': 'summary',
}


def make_html_base_name(template_name, contest_base):
    """
    Return the output file stem to use for the given template and contest,
    but without the language code suffix.

    Args:
      contest_base: the contest base name (e.g. "da_short").
    """
    base_name_suffix = HTML_FILE_SUFFIXES[template_name]
    html_base_name = f'{contest_base}-{base_name_suffix}'
    return html_base_name


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
    candidates = results['candidate_names']
    _log.info(f'parsed contest: {contest_name!r} ({len(candidates)} candidates)')
    summary.add_summary(results)

    json_path = json_dir / f'{path.stem}.json'
    _log.info(f'writing: {json_path}')
    utils.write_json(results, path=json_path)

    return json_path


def read_label_translations(translations_path):
    data = utils.read_yaml(translations_path)
    labels = data['labels']
    return labels


def make_phrase_translations(label_translations):
    phrases = {}
    for label, translations in label_translations.items():
        phrase = translations[LANG_CODE_ENGLISH]
        phrases[phrase] = label

    return phrases


def _translate_blanks(label_translations, lang_code):
    """
    Return the translation to use for the "Blanks" subtotal category.
    """
    blanks = utils.get_translation(
        label_translations, label='total_blanks', lang=lang_code,
    )
    undervotes = utils.get_translation(
        label_translations, label='total_undervotes', lang=lang_code,
    )
    return f'{blanks} ({undervotes})'


def _make_blanks_translations(label_translations):
    """
    Return a dict of all translations to use for the "Blanks" subtotal
    category.
    """
    return {
        lang_code: _translate_blanks(label_translations, lang_code=lang_code)
        for lang_code in LANGUAGES
    }


def make_subtotal_translations(label_translations):
    """
    Return a dict mapping subtotal key-name to dict of translations.

    The subtotal key-names (in the json file) are--

     * "continuing"
     * "blanks"
     * "exhausted"
     * "overvotes"
     * "non_transferable"
    """
    subtotal_translations = {}
    for key_name, label in SUBTOTAL_KEYS.items():
        translations = label_translations[label]
        subtotal_translations[key_name] = translations

    subtotal_translations[NonCandidateLabel.BLANK] = (
        _make_blanks_translations(label_translations)
    )
    return subtotal_translations


def make_environment(translations_path):
    env = Environment(
        loader=FileSystemLoader('templates'), autoescape=True,
    )

    label_translations = read_label_translations(translations_path)
    translate_label = functools.partial(
        rendering.translate_label, label_translations=label_translations,
    )

    subtotal_translations = make_subtotal_translations(label_translations)
    translate_subtotal_name = functools.partial(
        rendering.translate_label, label_translations=subtotal_translations,
    )

    phrases = make_phrase_translations(label_translations)
    translate_phrase = functools.partial(
        rendering.translate_phrase, label_translations=label_translations,
        phrases=phrases,
    )

    env.filters.update({
        'format_int': rendering.format_int,
        'format_percent': rendering.format_percent,
        'TL': jinja2.pass_context(translate_label),
        'TP': jinja2.pass_context(translate_phrase),
        'TS': jinja2.pass_context(translate_subtotal_name),
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


# TODO: pass in HTML_FILE_SUFFIXES similar to output_dirs?
def make_html_snippets(json_path, templates, output_dirs, base_name):
    """
    Render the html snippets for a single contest.

    Args:
      templates: a list of jinja2 Template objects.
      json_dir: the json output directory.
      output_dirs: a dict mapping string template name to the output
        directory for the template.
      base_name: the contest base name (e.g. "da_short").
    """
    _log.info(f'making RCV html snippets from: {json_path}')
    rcv_data = utils.read_json(json_path)
    for template in templates:
        template_name = template.name
        output_dir = output_dirs[template_name]
        html_base_name = make_html_base_name(template_name, contest_base=base_name)
        rendering.make_rcv_contest_html(
            rcv_data, template=template, output_dir=output_dir,
            base_name=html_base_name,
        )


def process_contest(
    contest_data, reports_dir, report_suffix, templates, json_dir, output_dirs,
):
    """
    Args:
      templates: a list of jinja2 Template objects.
      json_dir: the json output directory.
      output_dirs: a dict mapping string template name to the output
        directory for the template.
    """
    file_stem = contest_data['file_stem']
    file_name = f'{file_stem}.{report_suffix}'
    report_path = reports_dir / file_name
    json_path = make_rcv_json(report_path, json_dir=json_dir)
    make_html_snippets(
        json_path, templates=templates, output_dirs=output_dirs,
        base_name=file_stem,
    )


# TODO: pass in dict mapping template name to output_dir?
# TODO: make json_dir required?
def process_election(
    config_path, reports_dir, report_suffix, translations_path, output_dir,
    json_dir=None, css_dir=None,
):
    """
    This function creates the json_dir and output_dir directories if they
    don't already exist.

    Args:
      config_path: path to an election.yml config, as a Path object.
      report_suffix: a file extension specifying which RCV reports to
        read and parse. Can be one of: "xml" or "xlsx".
      output_dir: the directory to which to write the RCV html snippets,
        as a Path object.
      json_dir: the directory to which to write the intermediate json
        files, as a Path object. Defaults to a subdirectory of the given
        output directory.
      css_dir: the path to the directory containing the default.css file,
        as a Path object, for use in the rcv-complete.html template.
        This can be a relative path.
    """
    if json_dir is None:
        json_dir = output_dir / 'json'

    if not json_dir.exists():
        json_dir.mkdir(parents=True, exist_ok=True)

    output_dirs = {}
    for template_name, output_dir_name in HTML_OUTPUT_DIR_NAMES.items():
        template_output_dir = output_dir / output_dir_name
        template_output_dir.mkdir(parents=True, exist_ok=True)
        output_dirs[template_name] = template_output_dir

    election_data = read_election_config(config_path)
    contests_data = election_data['contests']

    env = make_environment(translations_path)
    global_vars = _make_globals(css_dir=css_dir)
    global_vars['election'] = election_data

    templates = [
        env.get_template(name, globals=global_vars) for name in
        ('rcv-summary.html', 'rcv-complete.html')
    ]
    for contest_data in contests_data:
        process_contest(
            contest_data, reports_dir=reports_dir, report_suffix=report_suffix,
            templates=templates, output_dirs=output_dirs, json_dir=json_dir,
        )
