from app.services.interleave_service import tdi, interleave_rankings
from ..create_test_data import create_result

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
    interleaved_results = tdi(item_dict_base, item_dict_exp)

    # since the interleaving is random if both systems were utelized the same, there are multiple possible results
    assert interleaved_results in possible_results


def test_interleave_rankings(sessions):
    from copy import deepcopy

    result = create_result(sessions, "ranker")

    results_base = deepcopy(result)
    results_base.items = {
        1: {"docid": "doc1", "type": "BASE"},
        2: {"docid": "doc2", "type": "BASE"},
        3: {"docid": "doc3", "type": "BASE"},
    }

    results_exp = deepcopy(result)
    results_exp.items = {
        1: {"docid": "doc11", "type": "EXP"},
        2: {"docid": "doc12", "type": "EXP"},
        3: {"docid": "doc13", "type": "EXP"},
    }
    print(results_base.items.items())

    interleaved_results = interleave_rankings(results_exp, results_base)

    # The interleaved dict is added to the Result object which is a JSON type. Therefore the keys are konverted from int to str. Here we revert this conversion.
    interleaved_results = {int(k): v for k, v in interleaved_results.items()}
    assert interleaved_results in possible_results
