

def get_candidate_summary(rounds, name):
    highest_round = 0
    highest_vote = 0
    for round_number, round_data in enumerate(rounds, start=1):
        votes = round_data['votes']
        if votes is not None and votes > 0:
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
    candidates = results['candidates']
    rounds = results['rounds']
    candidate_summaries = {}
    for name in candidates:
        candidate_rounds = rounds[name]
        candidate_summaries[name] = get_candidate_summary(
            candidate_rounds, name=name,
        )

    results['candidate_summaries'] = candidate_summaries

    vote_totals = {
        name: summary['highest_vote'] for name, summary in
        candidate_summaries.items()
    }
    def sort_key(name):
        return vote_totals[name]

    # Sort candidates from highest to lowest vote total.
    candidates = sorted(candidates, key=sort_key, reverse=True)
    results['candidates'] = candidates

    highest_vote = max(vote_totals.values())
    # Use a list in case more than one candidate is tied.
    leading_candidates = [
        name for name, total in vote_totals.items() if total == highest_vote
    ]
    results['leading_candidates'] = leading_candidates
