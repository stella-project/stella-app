import random
from app.models import db, Result, System
from flask import current_app


def tdi(item_dict_base, item_dict_exp):
    # team draft interleaving
    # implementation taken from https://bitbucket.org/living-labs/ll-api/src/master/ll/core/interleave.py
    result = {}
    result_set = set([])

    max_length = len(item_dict_exp.values())

    pointer_exp = 0
    pointer_base = 0

    ranking_exp = list(item_dict_exp.values())
    ranking_base = list(item_dict_base.values())
    length_ranking_exp = len(ranking_exp)
    length_ranking_base = len(ranking_base)

    length_exp = 0
    length_base = 0

    pos = 1

    while (
        pointer_exp < length_ranking_exp
        and pointer_base < length_ranking_base
        and len(result) < max_length
    ):
        if length_exp < length_base or (
            length_exp == length_base and bool(random.getrandbits(1))
        ):
            result.update({pos: {"docid": ranking_exp[pointer_exp], "type": "EXP"}})
            result_set.add(ranking_exp[pointer_exp])
            length_exp += 1
            pos += 1
        else:
            result.update({pos: {"docid": ranking_base[pointer_base], "type": "BASE"}})
            result_set.add(ranking_base[pointer_base])
            length_base += 1
            pos += 1
        while (
            pointer_exp < length_ranking_exp and ranking_exp[pointer_exp] in result_set
        ):
            pointer_exp += 1
        while (
            pointer_base < length_ranking_base
            and ranking_base[pointer_base] in result_set
        ):
            pointer_base += 1
    return result


def interleave_rankings(ranking_exp, ranking_base):
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
    base = {k: v.get("docid") for k, v in ranking_base.items.items()}
    exp = {k: v.get("docid") for k, v in ranking_exp.items.items()}

    item_dict = tdi(base, exp)

    ranking = Result(
        session_id=ranking_exp.session_id,
        system_id=ranking_exp.system_id,
        type="RANK",
        q=ranking_exp.q,
        q_date=ranking_exp.q_date,
        q_time=ranking_exp.q_time,
        num_found=ranking_exp.num_found,
        hits=ranking_base.num_found,
        page=ranking_exp.page,
        rpp=ranking_exp.rpp,
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
