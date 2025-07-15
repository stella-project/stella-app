from copy import deepcopy

from app.services.interleave_service import interleave_rankings, team_draft_interleave
from ..create_test_data import create_results

possible_results = [
    {
        1: {"docid": "doc11", "type": "EXP"},
        2: {"docid": "doc1", "type": "BASE"},
        3: {"docid": "doc2", "type": "BASE"},
    },
    {
        1: {"docid": "doc11", "type": "EXP"},
        2: {"docid": "doc1", "type": "BASE"},
        3: {"docid": "doc12", "type": "EXP"},
    },
    {
        1: {"docid": "doc1", "type": "BASE"},
        2: {"docid": "doc11", "type": "EXP"},
        3: {"docid": "doc12", "type": "EXP"},
    },
    {
        1: {"docid": "doc1", "type": "BASE"},
        2: {"docid": "doc11", "type": "EXP"},
        3: {"docid": "doc2", "type": "BASE"},
    },
    {
        1: {"docid": "doc1", "type": "BASE"},
        2: {"docid": "doc11", "type": "EXP"},
        3: {"docid": "doc2", "type": "BASE"},
        4: {"docid": "doc12", "type": "EXP"},
        5: {"docid": "doc3", "type": "BASE"},
        6: {"docid": "doc4", "type": "BASE"},
    },
    {
        1: {"docid": "doc11", "type": "EXP"},
        2: {"docid": "doc1", "type": "BASE"},
        3: {"docid": "doc12", "type": "EXP"},
        4: {"docid": "doc2", "type": "BASE"},
        5: {"docid": "doc3", "type": "BASE"},
        6: {"docid": "doc4", "type": "BASE"},
    },
    {
        1: {"docid": "doc1", "type": "BASE"},
        2: {"docid": "doc11", "type": "EXP"},
        3: {"docid": "doc2", "type": "BASE"},
        4: {"docid": "doc3", "type": "BASE"},
    },
    {
        1: {"docid": "doc11", "type": "EXP"},
        2: {"docid": "doc1", "type": "BASE"},
        3: {"docid": "doc2", "type": "BASE"},
        4: {"docid": "doc3", "type": "BASE"},
    },
]


def test_tdi():
    item_dict_base = {
        1: "doc1",
        2: "doc2",
        3: "doc3",
    }
    item_dict_exp = {
        1: "doc11",
        2: "doc12",
        3: "doc13",
    }
    interleaved_results = team_draft_interleave([v for v in item_dict_base.values()], [v for v in item_dict_exp.values()], rpp=len(item_dict_base))

    # since the interleaving is random if both systems were utelized the same, there are multiple possible results
    assert interleaved_results in possible_results


def test_interleave_rankings(sessions):
    result = create_results(sessions)

    results_base = result["ranker_base"]
    results_base.items = {
        1: {"docid": "doc1", "type": "BASE"},
        2: {"docid": "doc2", "type": "BASE"},
        3: {"docid": "doc3", "type": "BASE"},
    }

    results_exp = result["ranker"]
    results_exp.items = {
        1: {"docid": "doc11", "type": "EXP"},
        2: {"docid": "doc12", "type": "EXP"},
        3: {"docid": "doc13", "type": "EXP"},
    }

    interleaved_results = interleave_rankings(results_exp, results_base, 'ranking', rpp=len(results_base.items))
    # The interleaved dict is added to the Result object which is a JSON type. Therefore the keys are konverted from int to str. Here we revert this conversion.
    interleaved_results = {int(k): v for k, v in interleaved_results.items.items()}
    assert interleaved_results in possible_results


def test_interleave_rankings_exp_fail(sessions):
    result = create_results(sessions)

    results_base = result["ranker_base"]
    results_base.items = {
        1: {"docid": "doc1", "type": "BASE"},
        2: {"docid": "doc2", "type": "BASE"},
        3: {"docid": "doc3", "type": "BASE"},
    }

    results_exp = result["ranker"]
    results_exp.items = {}

    interleaved_results = interleave_rankings(results_exp, results_base, 'ranking', rpp=len(results_base.items))

    assert interleaved_results.items == results_base.items



def test_interleave_rankings_less_results_than_expected(sessions):
    result = create_results(sessions)

    results_base = result["ranker_base"]
    results_base.items = {
        1: {"docid": "doc1", "type": "BASE"},
        2: {"docid": "doc2", "type": "BASE"},
        3: {"docid": "doc3", "type": "BASE"},
        4: {"docid": "doc4", "type": "BASE"},
    }

    results_exp = result["ranker"]
    results_exp.items = {
        1: {"docid": "doc11", "type": "EXP"},
        2: {"docid": "doc12", "type": "EXP"},
    }

    interleaved_results = interleave_rankings(results_exp, results_base, 'ranking', rpp=6)
    interleaved_results = {int(k): v for k, v in interleaved_results.items.items()}

    assert interleaved_results in possible_results



def test_interleave_rankings_unbalanced(sessions):
    result = create_results(sessions)

    results_base = result["ranker_base"]
    results_base.items = {
        1: {"docid": "doc1", "type": "BASE"},
        2: {"docid": "doc2", "type": "BASE"},
        3: {"docid": "doc3", "type": "BASE"},
        4: {"docid": "doc4", "type": "BASE"},
    }

    results_exp = result["ranker"]
    results_exp.items = {
        1: {"docid": "doc11", "type": "EXP"},
    }

    interleaved_results = interleave_rankings(results_exp, results_base, 'ranking', rpp=4)
    interleaved_results = {int(k): v for k, v in interleaved_results.items.items()}

    assert interleaved_results in possible_results