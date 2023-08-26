

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
    candidates = results['candidates']
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
        # TODO: rename this to candidate_names.
        'candidates': candidates,
        'highest_round': highest_round,
        'leading_candidates': leading_candidates,
    })
