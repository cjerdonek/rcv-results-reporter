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
def translate_label(context, label, lang=None, translated_labels=None):
    """
    Translate the given label into the language set in the given Jinja2
    context.

    Args:
      lang: an optional 2-letter language code.  Defaults to the context's
        current language.
      translated_labels: the dict of translations, where the keys are the
        labels.
    """
    if lang is None:
        lang = _get_language(context)

    if not label:
        raise ValueError(
            f'no label provided: {label!r}. '
            'Make sure to pass a string as the label.'
        )

    translations = translated_labels[label]
    try:
        translation = translations[lang]
    except KeyError:
        if lang == ENGLISH_LANG:
            raise RuntimeError(
                f'label {label!r} is missing an english '
                f'({ENGLISH_LANG!r}) translation'
            ) from None

        try:
            translation = translations[ENGLISH_LANG]
        except KeyError:
            raise RuntimeError(
                f'label {label!r} is missing a default english '
                f'({ENGLISH_LANG!r}) translation for {lang!r}'
            )

    return translation


# We apply jinja2.pass_context() to this function elsewhere in our code.
def translate_phrase(
    context, phrase, lang=None, translated_labels=None, phrases=None,
):
    """
    Translate the given phrase into the language set in the given Jinja2
    context.

    Args:
      lang: an optional 2-letter language code.  Defaults to the context's
        current language.
      translated_labels: the dict of translations, where the keys are the
        labels.
      phrases: a dict of all phrases, mapping phrase to label.
    """
    label = phrases[phrase]
    translation = translate_label(
        context, label=label, lang=lang, translated_labels=translated_labels,
    )
    return translation
