import random

from app.models import Result, System, db
from flask import current_app


def team_draft_interleave(ranking_base, ranking_exp, rpp=None):
    # team draft interleaving
    # implementation taken from https://bitbucket.org/living-labs/ll-api/src/master/ll/core/interleave.py
    result = {}
    result_set = set([])
    
    if rpp is not None:
        max_length = rpp
    else:
        max_length = min(len(ranking_exp), len(ranking_base)) * 2

    pointer_base = 0
    pointer_exp = 0

    length_ranking_base = len(ranking_base)
    length_ranking_exp = len(ranking_exp)

    length_base = 0
    length_exp = 0

    pos = 1
    while len(result) < max_length:
        base_available = pointer_base < length_ranking_base
        exp_available = pointer_exp < length_ranking_exp
        if not base_available and not exp_available:
            break

        select_base = False
        if base_available and exp_available:
            if length_base < length_exp or (length_base == length_exp and bool(random.getrandbits(1))):
                select_base = True
        elif base_available:
            select_base = True

        if select_base:
            result.update({pos: {"docid": ranking_base[pointer_base], "type": "BASE"}})
            result_set.add(ranking_base[pointer_base])
            length_base += 1
            pos += 1
        else:
            result.update({pos: {"docid": ranking_exp[pointer_exp], "type": "EXP"}})
            result_set.add(ranking_exp[pointer_exp])
            length_exp += 1
            pos += 1
        
        while (
            pointer_base < length_ranking_base
            and ranking_base[pointer_base] in result_set
        ):
            pointer_base += 1
        
        while (
            pointer_exp < length_ranking_exp and ranking_exp[pointer_exp] in result_set
        ):
            pointer_exp += 1

    return result


def add_missing_results(result_list, interleaved_results, type, rpp):
    interleaved_ids = set([v['docid'] for k, v in interleaved_results.items()])
    interleaved_length = len(interleaved_results)
    for res in result_list:
        if interleaved_length < rpp and res not in interleaved_ids:
            interleaved_length += 1
            interleaved_results[interleaved_length] = {'docid': res, 'type': type}

    return interleaved_results


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

    item_dict = team_draft_interleave(base, exp)
    if len(item_dict) < rpp:
        item_dict = add_missing_results(base, item_dict, "BASE", rpp)
        item_dict = add_missing_results(exp, item_dict, "EXP", rpp)
    elif len(item_dict) > rpp:
        # if the interleaving is longer than rpp, we cut it down to rpp. This can happen if both systems have a lot of overlap in their rankings.
        item_dict = {k: v for k, v in item_dict.items() if k <= rpp}

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
