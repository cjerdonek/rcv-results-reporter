import json


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


def write_json(data, path):
    with path.open('w') as f:
        json.dump(data, f, indent='    ', sort_keys=True)


# TODO: also use this for parsing Excel.
def initialize_results(candidates):
    non_candidate_subtotals = NON_CANDIDATE_SUBTOTALS.copy()
    subtotals = list(candidates) + non_candidate_subtotals
    return {
        'candidates': candidates,
        'non_candidate_subtotals': non_candidate_subtotals,
        'subtotals': subtotals,
    }
