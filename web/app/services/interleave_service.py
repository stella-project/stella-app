import random

from app.models import Result, System, db
from flask import current_app


def team_draft_interleave(result_list_base, result_list_exp, rpp):
    # implementation based on https://bitbucket.org/living-labs/ll-api/src/master/ll/core/interleave.py
    """
    Perform Team Draft Interleaving between two ranked lists.
    
    Args:
        result_list_base (List[str]): Ranked list of document IDs from BASE.
        result_list_exp (List[str]): Ranked list of document IDs from EXP.

    Returns:
        interleaved (Dict): The interleaved list of document IDs.
    """
    # Initialize state
    interleaved = {}
    picked_docs = set()

    # Create iterators for both rankers
    iter_base = iter(result_list_base)
    iter_exp = iter(result_list_exp)
    team_iters = {"BASE": iter_base, "EXP": iter_exp}

    # Randomize who starts
    teams = ["BASE", "EXP"]
    random.shuffle(teams)

    unique_docs = set(result_list_base) | set(result_list_exp)
    result_limit = min(len(unique_docs), rpp)
    # Continue drafting until interleaved list is full
    while len(interleaved) < result_limit:
        for team in teams:
            try:
                # Keep trying to pick a new doc
                while True:
                    doc = next(team_iters[team])
                    if doc not in picked_docs:
                        interleaved[len(interleaved)+1] = {"docid": doc, "type": team}
                        picked_docs.add(doc)
                        break
            except StopIteration:
                continue
            if len(interleaved) >= result_limit:
                break

    return interleaved

def interleave_rankings(ranking_exp, ranking_base, system_type, rpp):
    """
    Create interleaved ranking from experimental and baseline system
    Used method: Team-Draft-Interleaving (TDI) [1]

    [1] "How Does Clickthrough Data Reflect Retrieval Quality?"
        Radlinski, Kurup, Joachims
        Published in CIKM '15 2015

    @param ranking_exp:     experimental ranking (Result)
    @param ranking_base:    baseline ranking (Result)
    @return:                interleaved ranking (dict)
    """
    # Extract the IDs of the documents from the rankings for tdi
    base = [v.get("docid") for v in ranking_base.items.values()]
    exp = [v.get("docid") for v in ranking_exp.items.values()]

    item_dict = team_draft_interleave(base, exp, rpp)

    ranking = Result(
        session_id=ranking_exp.session_id,
        system_id=ranking_exp.system_id,
        type="RANK" if system_type == "ranking" else "REC",
        q=ranking_exp.q,
        q_date=ranking_exp.q_date,
        q_time=ranking_exp.q_time,
        num_found=ranking_exp.num_found,
        hits=ranking_base.num_found,
        page=ranking_exp.page,
        rpp=rpp,
        items=item_dict,
    )

    db.session.add(ranking)
    db.session.commit()

    ranking_id = ranking.id
    ranking.tdi = ranking_id
    ranking_exp.tdi = ranking_id
    ranking_base.tdi = ranking_id

    db.session.add_all([ranking_exp, ranking_base])
    db.session.commit()

    return ranking
