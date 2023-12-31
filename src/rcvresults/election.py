"""
Support for generating RCV HTML snippets for an election.
"""

import functools
import logging

import jinja2
from jinja2 import Environment, FileSystemLoader

import rcvresults.rendering as rendering
from rcvresults.rendering import CONTEXT_KEY_PAGE_NAMES
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
        'iter_languages': jinja2.pass_context(rendering.iter_languages),
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


def make_rcv_contest_html(template, rcv_data, output_dir, contest_base):
    """
    Create the html snippets for an RCV contest, one for each language.

    Args:
      template: a jinja2 Template object for the contest html (e.g.
        constructed from "rcv-complete.html" or "rcv-summary.html").
      rcv_data: the contest data parsed from the xml or Excel results
        report for the contest. This can also be read from a contest
        json file.
      output_dir: the directory to which to write the rendered html files.
      contest_base: the contest base name (e.g. "da_short").
    """
    # This is the output file stem without the language code suffix.
    html_base_name = make_html_base_name(template.name, contest_base=contest_base)

    # Make the initial template context. We start by copying the rcv_data
    # dict so we can add to it without affecting the original.
    context = rcv_data.copy()
    page_names = utils.make_page_names(html_base_name)
    context[CONTEXT_KEY_PAGE_NAMES] = page_names

    for lang_code in LANGUAGES:
        html_name = page_names[lang_code]
        output_path = output_dir / html_name
        rendering.render_template(
            template, output_path=output_path, context=context,
            lang_code=lang_code,
        )


# TODO: pass in HTML_FILE_SUFFIXES similar to output_dirs?
# TODO: make base_name optional?
def make_html_snippets(json_path, templates, output_dirs, base_name):
    """
    Render the html snippets for a single contest.

    Args:
      json_path: path to a json file of contest data, as a Path object.
      templates: a list of jinja2 Template objects.
      output_dirs: a dict mapping string template name to the output
        directory for the template.
      base_name: the contest base name (e.g. "da_short").
    """
    _log.info(f'making RCV html snippets from: {json_path}')
    rcv_data = utils.read_json(json_path)
    for template in templates:
        output_dir = output_dirs[template.name]
        make_rcv_contest_html(
            template, rcv_data=rcv_data, output_dir=output_dir,
            contest_base=base_name,
        )


# TODO: pass in dict mapping template name to output_dir?
# TODO: choose a better name for this function.
def process_election(
    json_paths, config_path, translations_path, output_dir, css_dir=None,
):
    """
    This function creates the json_dir and output_dir directories if they
    don't already exist.

    Args:
      json_paths: iterable of paths of json files of contest data (one
        per contest), as Path objects.
      config_path: path to an election.yml config, as a Path object.
      output_dir: the directory to which to write the RCV html snippets,
        as a Path object.
      css_dir: the path to the directory containing the default.css file,
        as a Path object, for use in the rcv-complete.html template.
        This can be a relative path.
    """
    output_dirs = {}
    for template_name, output_dir_name in HTML_OUTPUT_DIR_NAMES.items():
        template_output_dir = output_dir / output_dir_name
        template_output_dir.mkdir(parents=True, exist_ok=True)
        output_dirs[template_name] = template_output_dir

    election_data = read_election_config(config_path)

    env = make_environment(translations_path)
    global_vars = _make_globals(css_dir=css_dir)
    global_vars['election'] = election_data

    templates = [
        env.get_template(name, globals=global_vars) for name in
        ('rcv-summary.html', 'rcv-complete.html')
    ]

    file_count = len(json_paths)
    _log.info(f'processing {file_count} contests (json files)...')
    for i, json_path in enumerate(json_paths, start=1):
        _log.info(f'reading json file {i} (of {file_count}): {json_path}')
        base_name = json_path.stem
        make_html_snippets(
            json_path, templates=templates, output_dirs=output_dirs,
            base_name=base_name,
        )
    _log.info(f'wrote output files for {file_count} contests to directory: {output_dir}')
