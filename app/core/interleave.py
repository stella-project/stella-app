import random


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

    while pointer_exp < length_ranking_exp and pointer_base < length_ranking_base and len(result) < max_length:
        if length_exp < length_base or (length_exp == length_base and bool(random.getrandbits(1))):
            result.update({pos: {"docid": ranking_exp[pointer_exp], 'type': 'EXP'}})
            result_set.add(ranking_exp[pointer_exp])
            length_exp += 1
            pos += 1
        else:
            result.update({pos: {"docid":  ranking_base[pointer_base], 'type': 'BASE'}})
            result_set.add(ranking_base[pointer_base])
            length_base += 1
            pos += 1
        while pointer_exp < length_ranking_exp and ranking_exp[pointer_exp] in result_set:
            pointer_exp += 1
        while pointer_base < length_ranking_base and ranking_base[pointer_base] in result_set:
            pointer_base += 1
    return result


def tdi_rec(item_dict_base, item_dict_exp):
    # team draft interleaving
    # implementation taken from https://bitbucket.org/living-labs/ll-api/src/master/ll/core/interleave.py

    result = {}
    result_set = set([])

    max_length = len(item_dict_exp.values())

    pointer_exp = 0
    pointer_base = 0

    recommendation_exp = [rec['id'] for rec in item_dict_exp.values()]
    recommendation_base = [rec['id'] for rec in item_dict_base.values()]
    length_ranking_exp = len(recommendation_exp)
    length_ranking_base = len(recommendation_base)

    length_exp = 0
    length_base = 0

    pos = 1

    while pointer_exp < length_ranking_exp and pointer_base < length_ranking_base and len(result) < max_length:
        if length_exp < length_base or (length_exp == length_base and bool(random.getrandbits(1))):
            result.update({pos: {"docid": recommendation_exp[pointer_exp], 'type': 'EXP'}})
            result_set.add(recommendation_exp[pointer_exp])
            length_exp += 1
            pos += 1
        else:
            result.update({pos: {"docid":  recommendation_base[pointer_base], 'type': 'BASE'}})
            result_set.add(recommendation_base[pointer_base])
            length_base += 1
            pos += 1
        while pointer_exp < length_ranking_exp and recommendation_exp[pointer_exp] in result_set:
            pointer_exp += 1
        while pointer_base < length_ranking_base and recommendation_base[pointer_base] in result_set:
            pointer_base += 1
    return result