"""
Supports parsing Dominion XML (.xml) RCV result reports.

Here is some information about the XML structure:

Report: Title, RcvStaticData, Tablix1

  Tablix1: precinctGroup_Collection

    precinctGroup_Collection: precinctGroup

      precinctGroup: Tablix5

        Tablix5: choiceGroup_Collection, Textbox70, roundGroup_Collection,
          nonTransferableGroup_Collection, Textbox70_1,
          roundGroup_Collection_1, Textbox70_2, roundGroup_Collection_2,
          Textbox70_3, roundGroup_Collection_3

          choiceGroup_Collection: each child is a choiceGroup element
            containing a roundGroup_Collection that contains rounds
            containing votes, percentage, and transfer total.

          roundGroup_Collection: each child is a roundGroup containing
            the "Continuing Ballots Total" in that round.

          nonTransferableGroup_Collection: each child is a
            nonTransferableGroup element

          roundGroup_Collection_1: each child is a roundGroup containing
            the "Non Transferable Total" in that round, i.e. the sum of
            Blanks, Exhausted, and Overvotes.

          roundGroup_Collection_2: each child is a roundGroup containing
            the majority threshold in that round.
"""

import logging
import xml.etree.ElementTree as ET

import rcvresults.utils as utils
from rcvresults.utils import NonCandidateNames


_log = logging.getLogger(__name__)

NAMESPACE = '{RcvShortReport}'

NON_CANDIDATE_CHOICE_NAMES = [
    NonCandidateNames.BLANK,
    NonCandidateNames.EXHAUSTED,
    NonCandidateNames.OVERVOTE,
    NonCandidateNames.REMAINDER,
]


def _get_child(element, tag):
    tag = f'{{RcvShortReport}}{tag}'
    return element.find(tag)


def _get_child_value(element, tag, attr_name):
    element = _get_child(element, tag=tag)
    return element.attrib[attr_name]


def _get_descendant(element, tags):
    parts = ['.']
    parts.extend(f'{{RcvShortReport}}{tag}' for tag in tags)
    path = '/'.join(parts)
    return element.find(path)


def _debug_get_descendant(element, tags):
    """
    Equivalent to _get_descendant() but with verbose logging.
    """
    path = ' -> '.join(tags)
    _log.info(f'getting descendant: {path}')
    for tag in tags:
        element_tag = element.tag.removeprefix(NAMESPACE)
        child_tags = [
            child.tag.removeprefix(NAMESPACE) for child in element
        ]
        # Put a star ("*") before the one we are getting.
        child_tags = [
            (('*' if child_tag == tag else '') + child_tag)
            for child_tag in child_tags
        ]
        child_list = ', '.join(child_tags)
        current_element = f'{element_tag} ({len(child_tags)})'
        _log.info(
            f'children: {current_element:>30}: {child_list}'
        )
        element = _get_child(element, tag=tag)

    return element


def _get_contest_name(root, get_descendant):
    """
    Extract and return the contest name.
    """
    tablix2 = get_descendant(root, ['RcvStaticData', 'Report', 'Tablix2'])
    # TODO: will this always be "Textbox24"?
    contest_name = tablix2.attrib['Textbox24']

    return contest_name


def _iter_choice_groups(tablix_5):
    """
    Yield the choiceGroup elements in the choiceGroup_Collection.
    """
    choice_group_collection = _get_child(
        tablix_5, tag='choiceGroup_Collection',
    )
    for choice_group in choice_group_collection:
        text_box = _get_child(choice_group, tag='Textbox70')
        name = text_box.attrib['choiceName']
        yield (name, choice_group)


def _get_candidate_names(tablix_5):
    choice_names = [
        name for name, _choice_group in _iter_choice_groups(tablix_5)
    ]
    if choice_names[-4:] != NON_CANDIDATE_CHOICE_NAMES:
        raise RuntimeError(
            f'last four choice names not as expected: {choice_names}'
        )
    # Remove the non-candidate choices before returning.
    return choice_names[:-4]


def _make_round_dict(votes, percent=None, transfer=None):
    return {
        'percent': None if percent is None else float(percent),
        'transfer': None if transfer is None else float(transfer),
        'votes': float(votes),
    }


def _iter_choice_rounds(choice_group):
    """
    Yield the rounds data for all choices except "Continuing Ballots Total"
    and "Non Transferable Total".

    Args:
      choice_group: a choiceGroup inside choiceGroup_Collection, which is
        the first child of the Tablix5 element.
    """
    round_group_collection = _get_child(
        choice_group, tag='roundGroup_Collection',
    )
    for round_group in round_group_collection:
        votes = _get_child_value(
            round_group, tag='Textbox9', attr_name='votes',
        )
        percent = _get_child_value(
            round_group, tag='Textbox16', attr_name='Textbox17',
        )
        transfer = _get_child_value(
            round_group, tag='transferType', attr_name='voteTransfer',
        )
        yield _make_round_dict(votes, percent=percent, transfer=transfer)


def _iter_continuing_totals(tablix_5):
    """
    Yield the rounds data for the "Continuing Ballots Total".
    """
    round_group_collection = _get_child(tablix_5, tag='roundGroup_Collection')
    for round_group in round_group_collection:
        votes = _get_child_value(
            round_group, tag='Textbox9', attr_name='continuingVotes',
        )
        yield _make_round_dict(votes)


def _iter_non_tranferable_totals(tablix_5):
    """
    Yield the rounds data for the "Non Transferable Total".
    """
    round_group_collection = _get_child(
        tablix_5, tag='roundGroup_Collection_1',
    )
    for round_group in round_group_collection:
        votes = _get_child_value(
            round_group, tag='Textbox9', attr_name='nonTransferableVotes',
        )
        yield _make_round_dict(votes)


def _get_rounds(tablix_5):
    """
    Create a return the "rounds" dict.
    """
    rounds = {}
    for name, choice_group in _iter_choice_groups(tablix_5):
        _log.info(f'processing choice: {name}')
        # The "Remainder Points" subtotal isn't applicable.
        if name == NonCandidateNames.REMAINDER:
            continue

        choice_rounds = list(_iter_choice_rounds(choice_group))
        rounds[name] = choice_rounds

    continuing_rounds = list(_iter_continuing_totals(tablix_5))
    rounds[NonCandidateNames.CONTINUING] = continuing_rounds

    non_tranferable_rounds = list(_iter_non_tranferable_totals(tablix_5))
    rounds[NonCandidateNames.NON_TRANSFERABLE] = non_tranferable_rounds

    return rounds


def _get_results(root, get_descendant):
    """
    Extract and return the contest rounds data.
    """
    tablix_5 = get_descendant(root, [
        'Tablix1', 'precinctGroup_Collection', 'precinctGroup', 'Tablix5',
    ])
    candidates = _get_candidate_names(tablix_5)
    results = utils.initialize_results(candidates)

    rounds = _get_rounds(tablix_5)
    results['rounds'] = rounds

    return results


def parse_xml_file(path, debug=True):
    """
    Parse an XML file, and return a dict of results.
    """
    if debug:
        get_descendant = _debug_get_descendant
    else:
        get_descendant = _get_descendant

    tree = ET.parse(path)
    root = tree.getroot()

    contest_name = _get_contest_name(root, get_descendant=get_descendant)
    metadata = {
        'contest_name': contest_name,
    }
    results = _get_results(root, get_descendant)
    results['_metadata'] = metadata

    return results
