"""
Supports rendering Jinja2 templates.
"""

import logging

import rcvresults.utils as utils
from rcvresults.utils import LANG_CODE_ENGLISH, LANGUAGES


_log = logging.getLogger(__name__)

# Below are some of the template context keys we use.
# TODO: put these keys in a class?
#
# The key for the language being rendered. The value is the 2-letter
# language code (e.g. "en" for English or "es" for Spanish).
CONTEXT_KEY_CURRENT_LANG = 'current_lang'
# The value is a dict mapping 2-letter language code to the name in that
# language of the page being rendered.
CONTEXT_KEY_PAGE_NAMES = 'page_names'


def render_template(template, output_path, context=None, lang_code=None):
    """
    Args:
      context: the context to pass to template.render().
      lang_code: optional 2-letter language code (e.g. "en" for English
        or "es" for Spanish).
    """
    if context is None:
        context = {}
    if lang_code is not None:
        # Copy the context since we are modifying it.
        context = context.copy()
        context[CONTEXT_KEY_CURRENT_LANG] = lang_code

    _log.info(f'rendering template to (lang={lang_code!r}): {output_path}')
    html = template.render(context)
    output_path.write_text(html)


def format_int(value):
    if value is None:
        return 'None'

    if value == '':
        # TODO: replace this with something else.
        return 'XXX'
    try:
        # Add comma separators, and don't show a decimal point.
        return f'{value:,.0f}'
    except Exception:
        raise RuntimeError(f'error with value: {value!r}')


def format_percent(value):
    # Show 2 decimal places.
    percent = 100 * value
    return f'{percent:.2f}%'


def is_contest_leader(context, candidate):
    """
    Args:
      context: the template context.
    """
    return candidate in context['leading_candidates']


def candidate_was_eliminated(context, candidate, round_number):
    """
    Return whether the candidate was eliminated in a **previous** round.

    Args:
      context: the template context.
    """
    summaries = context['candidate_summaries']
    summary = summaries[candidate]
    elimination_round = summary.get('elimination_round')
    if elimination_round is None:
        return False

    return elimination_round < round_number


def get_candidate_class_prefix(context, candidate, round_number):
    """
    Returns one of: "Leader", "Winner", "Eliminated", or "", per the
    pre-2019 RCV tables.
    """
    if is_contest_leader(context, candidate=candidate):
        if round_number == context['highest_round']:
            return 'Winner'
        return 'Leader'

    summaries = context['candidate_summaries']
    candidate_summary = summaries[candidate]
    if round_number == candidate_summary.get('elimination_round'):
        return 'Eliminated'

    return ''


def _get_language(context):
    """
    Return the language set in the context, as a 2-letter language code
    (e.g. "en").
    """
    return context.get(CONTEXT_KEY_CURRENT_LANG, LANG_CODE_ENGLISH)


def iter_languages(context):
    """
    Yield a dict of information about each language, in the order the
    languages should appear in the language toggle at the top of the html page.
    """
    page_names = context[CONTEXT_KEY_PAGE_NAMES]
    for lang_code, lang_label in LANGUAGES.items():
        page_name = page_names[lang_code]
        lang = {
            'code': lang_code,
            'label': lang_label,
            'page_name': page_name,
        }
        yield lang


# We apply jinja2.pass_context() to this function elsewhere in our code.
def translate_label(context, label, lang=None, label_translations=None):
    """
    Translate the given label into the language set in the given Jinja2
    context.

    Args:
      lang: an optional 2-letter language code.  Defaults to the context's
        current language.
      label_translations: the dict of translations, where the keys are the
        labels.
    """
    if lang is None:
        lang = _get_language(context)

    if not label:
        raise ValueError(
            f'no label provided: {label!r}. '
            'Make sure to pass a string as the label.'
        )

    translation = utils.get_translation(
        label_translations, label=label, lang=lang,
    )
    return translation


# We apply jinja2.pass_context() to this function elsewhere in our code.
def translate_phrase(
    context, phrase, lang=None, label_translations=None, phrases=None,
):
    """
    Translate the given phrase into the language set in the given Jinja2
    context.

    Args:
      lang: an optional 2-letter language code.  Defaults to the context's
        current language.
      label_translations: the dict of translations, where the keys are the
        labels.
      phrases: a dict of all phrases, mapping phrase to label.
    """
    label = phrases[phrase]
    translation = translate_label(
        context, label=label, lang=lang, label_translations=label_translations,
    )
    return translation


def make_rcv_contest_html(context, template, output_dir, base_name):
    """
    Create the html snippets for an RCV contest, one for each language.

    Args:
      context: the context to pass to template.render(). This should
        include the contest data parsed from the xml or Excel results
        report for the contest.
      output_dir: the directory to which to write the rendered html files.
      base_name: the output file stem without the language code suffix.
    """
    for lang_code in LANGUAGES:
        html_name = utils.make_rcv_snippet_name(base_name, lang_code=lang_code)
        output_path = output_dir / html_name
        render_template(
            template, output_path=output_path, context=context,
            lang_code=lang_code,
        )
