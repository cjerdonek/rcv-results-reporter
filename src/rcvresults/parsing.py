"""
Support for parsing XML and Excel result reports and writing the data to JSON.
"""

import logging

import rcvresults.parsers.xml as xml_parsing
import rcvresults.parsers.xslx as excel_parsing
import rcvresults.utils as utils


_log = logging.getLogger('parse-results')


def make_candidate_summary(rounds, name):
    # Initialize highest_round to 1 in case the candidate has zero
    # votes in the first round.
    highest_round = 1
    highest_vote = 0
    for round_number, round_data in enumerate(rounds, start=1):
        votes = round_data['votes']
        if not votes:
            # Then the candidate had zero votes in the first round or is
            # eliminated in this round.
            break

        highest_round = round_number
        # The vote totals should only stay the same or increase.
        if votes < highest_vote:
            raise AssertionError(
                f'votes decreased in round {round_number} for {name!r}: '
                f'{votes} < {highest_vote}'
            )
        highest_vote = votes

    summary = {
        'highest_round': highest_round,
        'highest_vote': highest_vote,
    }
    return summary


def add_summary(results):
    """
    Add summary data to the parsed data dict.
    """
    candidates = results['candidate_names']
    rounds = results['rounds']
    candidate_summaries = {}
    for name in candidates:
        candidate_rounds = rounds[name]
        candidate_summaries[name] = make_candidate_summary(
            candidate_rounds, name=name,
        )

    highest_round = max(
        summary['highest_round'] for summary in candidate_summaries.values()
    )
    # Set the elimination_round for each candidate.
    for name, candidate_summary in candidate_summaries.items():
        highest_candidate_round = candidate_summary['highest_round']
        if highest_candidate_round != highest_round:
            # Then the candidate was eliminated in their highest round.
            candidate_summary['elimination_round'] = highest_candidate_round

    vote_totals = {
        name: summary['highest_vote'] for name, summary in
        candidate_summaries.items()
    }
    def sort_key(name):
        return vote_totals[name]

    # Sort candidates from highest to lowest vote total.
    candidates = sorted(candidates, key=sort_key, reverse=True)

    highest_vote = max(vote_totals.values())
    # Use a list in case more than one candidate is tied.
    leading_candidates = [
        name for name, total in vote_totals.items() if total == highest_vote
    ]
    results.update({
        'candidate_summaries': candidate_summaries,
        'candidate_names': candidates,
        'highest_round': highest_round,
        'leading_candidates': leading_candidates,
    })


def make_json_file(path, output_dir):
    _log.info(f'parsing: {path}')
    suffix = path.suffix
    if suffix == '.xlsx':
        parse_report_file = excel_parsing.parse_excel_file
    else:
        assert suffix == '.xml'
        parse_report_file = xml_parsing.parse_xml_file

    try:
        results = parse_report_file(path)
    except Exception:
        raise RuntimeError(f'error parsing report file: {path}')

    metadata = results['_metadata']
    contest_name = metadata['contest_name']
    candidates = results['candidate_names']
    _log.info(f'parsed contest: {contest_name!r} ({len(candidates)} candidates)')
    add_summary(results)

    json_path = output_dir / f'{path.stem}.json'
    _log.info(f'writing: {json_path}')
    utils.write_json(results, path=json_path)

    return json_path
