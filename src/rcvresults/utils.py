import glob
import json
from pathlib import Path

import yaml


class NonCandidateNames:

    CONTINUING = 'Continuing Ballots Total'
    BLANK = 'Blanks'
    EXHAUSTED = 'Exhausted'
    OVERVOTE = 'Overvotes'
    NON_TRANSFERABLE = 'Non Transferable Total'
    # This one isn't applicable to IRV.
    REMAINDER = 'Remainder Points'


NON_CANDIDATE_SUBTOTALS = [
    NonCandidateNames.CONTINUING,
    NonCandidateNames.BLANK,
    NonCandidateNames.EXHAUSTED,
    NonCandidateNames.OVERVOTE,
    NonCandidateNames.NON_TRANSFERABLE,
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
    non_candidate_subtotals = NON_CANDIDATE_SUBTOTALS.copy()
    subtotals = list(candidates) + non_candidate_subtotals
    return {
        'candidates': candidates,
        'non_candidate_subtotals': non_candidate_subtotals,
        'subtotals': subtotals,
    }
