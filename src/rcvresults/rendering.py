"""
Supports rendering Jinja2 templates.
"""


from rcvresults.utils import ENGLISH_LANG


def format_int(value):
    # Add comma separators, and don't show a decimal point.
    return f'{value:,.0f}'


def format_percent(value):
    # Show 2 decimal places.
    percent = 100 * value
    return f'{percent:.2f}%'


def _get_language(context):
    """
    Return the language set in the context, as a 2-letter language code
    (e.g. "en").
    """
    return context.get('lang', ENGLISH_LANG)


# We apply jinja2.pass_context() to this function elsewhere in our code.
def translate_label(context, label, lang=None, translations=None):
    """
    Translate the given label into the language set in the given Jinja2
    context.

    Args:
      lang: an optional 2-letter language code.  Defaults to the context's
        current language.
      translations: the dict of translations, where the keys are the labels.
    """
    if lang is None:
        lang = _get_language(context)

    if not label:
        raise ValueError(
            f'no label provided: {label!r}. '
            'Make sure to pass a string as the label.'
        )

    phrases = translations[label]
    try:
        translation = phrases[lang]
    except KeyError:
        if lang == ENGLISH_LANG:
            raise RuntimeError(
                f'label {label!r} is missing an english '
                f'({ENGLISH_LANG!r}) translation'
            ) from None

        try:
            translation = phrases[ENGLISH_LANG]
        except KeyError:
            raise RuntimeError(
                f'label {label!r} is missing a default english '
                f'({ENGLISH_LANG!r}) translation for {lang!r}'
            )

    return translation


# TODO: implement this.
def translate_phrase():
    raise NotImplementedError()


def render_contest(template, results, path):
    candidates = results['candidates']
    html = template.render(results)
    path.write_text(html)
