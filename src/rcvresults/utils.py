import glob
import json
from pathlib import Path

import yaml


# The key to use in the template context for the current language.
CURRENT_LANG_KEY = 'current_lang'

LANG_CODE_ENGLISH = 'en'

# A dict of the languages that should appear in the language toggle
# at the top of the html, in the order they should appear.
#
# The dict maps the language's 2-letter language code to the label for
# the language in the translations.yml file.
LANGUAGES = {
    LANG_CODE_ENGLISH: 'language_english',
    # Spanish
    'es': 'language_spanish',
    # Filipino
    'tl': 'language_filipino',
    # Chinese
    'zh': 'language_chinese',
}


class NonCandidateLabel:

    CONTINUING = 'continuing'
    BLANK = 'blanks'
    EXHAUSTED = 'exhausted'
    OVERVOTE = 'overvotes'
    NON_TRANSFERABLE = 'non_transferable'


NON_CANDIDATE_SUBTOTAL_LABELS = [
    NonCandidateLabel.CONTINUING,
    NonCandidateLabel.BLANK,
    NonCandidateLabel.EXHAUSTED,
    NonCandidateLabel.OVERVOTE,
    NonCandidateLabel.NON_TRANSFERABLE,
]


def read_json(path):
    with path.open() as f:
        data = json.load(f)
    return data


def read_yaml(path):
    with path.open() as f:
        data = yaml.safe_load(f)
    return data


def write_json(data, path):
    with path.open('w') as f:
        json.dump(data, f, indent='    ', sort_keys=True)


def make_rcv_snippet_name(base_name, lang_code):
    """
    Construct and return an RCV html snippet file name.
    """
    return f'{base_name}-{lang_code}.html'


def get_paths(dir_path, suffix):
    """
    Return the paths in the given directory, as a sorted list of Path objects.
    """
    glob_path = dir_path / f'*.{suffix}'
    raw_paths = glob.glob(str(glob_path))
    paths = [Path(raw_path) for raw_path in sorted(raw_paths)]
    return paths


# TODO: also use this for parsing Excel.
def initialize_results(candidates):
    non_candidate_subtotals = NON_CANDIDATE_SUBTOTAL_LABELS.copy()
    subtotals = list(candidates) + non_candidate_subtotals
    return {
        'candidates': candidates,
        'non_candidate_subtotals': non_candidate_subtotals,
        'subtotals': subtotals,
    }


def get_translation(label_translations, label, lang):
    """
    Return the translation for a label in translations.yml.
    """
    translations = label_translations[label]
    try:
        translation = translations[lang]
    except KeyError:
        if lang == LANG_CODE_ENGLISH:
            raise RuntimeError(
                f'label {label!r} is missing an english '
                f'({LANG_CODE_ENGLISH!r}) translation'
            ) from None

        try:
            translation = translations[LANG_CODE_ENGLISH]
        except KeyError:
            raise RuntimeError(
                f'label {label!r} is missing a default english '
                f'({LANG_CODE_ENGLISH!r}) translation for {lang!r}'
            )

    return translation
