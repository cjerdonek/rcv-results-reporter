"""
Supports parsing Dominion XML (.xml) RCV result reports.
"""

import logging
import xml.etree.ElementTree as ET


_log = logging.getLogger(__name__)

NAMESPACE = '{RcvShortReport}'


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


def _get_choice_rounds(choice_group):
    round_group_collection = _get_descendant(choice_group, [
        'roundGroup_Collection'
    ])
    choice_rounds = []
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
        round = {
            'percent': percent,
            'transfer': transfer,
            'votes': votes,
        }
        choice_rounds.append(round)

    return choice_rounds


def _get_results(root, get_descendant):
    """
    Extract and return the contest rounds data.
    """
    tablix_5 = get_descendant(root, [
        'Tablix1', 'precinctGroup_Collection', 'precinctGroup', 'Tablix5',
    ])
    choice_group_collection = get_descendant(tablix_5, [
        'choiceGroup_Collection',
    ])
    rounds = {}
    for choice_group in choice_group_collection:
        text_box = _get_descendant(choice_group, ['Textbox70'])
        name = text_box.attrib['choiceName']
        # The "Remainder Points" subtotal isn't applicable.
        if name == 'Remainder Points':
            continue

        choice_rounds = _get_choice_rounds(choice_group)
        rounds[name] = choice_rounds

    results = {
        'rounds': rounds,
    }
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
