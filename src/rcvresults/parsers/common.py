"""
Contains code needed for parsing both XML and Excel formats.
"""

from rcvresults.utils import NonCandidateLabel


# The non-candidate names that appear in both the XML and Excel reports.
# TODO: call this something other than Name?
class NonCandidateName:

    CONTINUING = 'Continuing Ballots Total'
    BLANK = 'Blanks'
    EXHAUSTED = 'Exhausted'
    OVERVOTE = 'Overvotes'
    NON_TRANSFERABLE = 'Non Transferable Total'
    # This one isn't applicable to IRV.
    REMAINDER = 'Remainder Points'


# Mapping from NonCandidateName to NonCandidateLabel.
NON_CANDIDATE_SUBTOTAL_LABELS = {
    NonCandidateName.BLANK: NonCandidateLabel.BLANK,
    NonCandidateName.CONTINUING: NonCandidateLabel.CONTINUING,
    NonCandidateName.EXHAUSTED: NonCandidateLabel.EXHAUSTED,
    NonCandidateName.NON_TRANSFERABLE: NonCandidateLabel.NON_TRANSFERABLE,
    NonCandidateName.OVERVOTE: NonCandidateLabel.OVERVOTE,
}


def get_subtotal_label(name):
    return NON_CANDIDATE_SUBTOTAL_LABELS[name]
