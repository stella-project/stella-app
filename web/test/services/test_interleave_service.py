import random
from unittest.mock import patch

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


def test_tdi_property_validation():
    base_docs = ["doc1", "doc2", "doc3"]
    exp_docs = ["doc11", "doc12", "doc13"]

    interleaved_results = team_draft_interleave(base_docs, exp_docs, rpp=3)

    # 1. Check length
    assert len(interleaved_results) == 3

    # 2. Check that no duplicates exist
    doc_ids = [item["docid"] for item in interleaved_results.values()]
    assert len(set(doc_ids)) == 3

    # 3. Check that it pulls from both lists (since both have enough items)
    types = [item["type"] for item in interleaved_results.values()]
    assert "BASE" in types
    assert "EXP" in types

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

    interleaved_results = interleave_rankings(
        results_exp, results_base, "ranking", rpp=len(results_base.items)
    )
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

    interleaved_results = interleave_rankings(
        results_exp, results_base, "ranking", rpp=len(results_base.items)
    )

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

    interleaved_results = interleave_rankings(
        results_exp, results_base, "ranking", rpp=6
    )
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

    interleaved_results = interleave_rankings(
        results_exp, results_base, "ranking", rpp=4
    )
    interleaved_results = {int(k): v for k, v in interleaved_results.items.items()}

    assert interleaved_results in possible_results
    assert interleaved_results in possible_results


class TestInterleaving:
    @patch("random.shuffle")
    def test_number_shuffles(self, mock_shuffle):
        ranking_a = ["d1", "d2", "d3", "d4"]
        ranking_b = ["d1", "d2", "d3", "d4"]

        # Run the algorithm for a max of 4 items
        res = team_draft_interleave(ranking_a, ranking_b, rpp=4)

        assert res == {
            1: {"docid": "d1", "type": "BASE"},
            2: {"docid": "d2", "type": "EXP"},
            3: {"docid": "d3", "type": "BASE"},
            4: {"docid": "d4", "type": "EXP"},
        }

        # Both rankings are identical. Therefore, we have two ties and need to shuffle twice, first at rank 1 and second at rank 3.
        assert mock_shuffle.call_count == 2

    def test_team_draft_distribution(self):

        ranking_a = ["d1", "d2", "d3", "d4"]
        ranking_b = ["d1", "d2", "d3", "d4"]

        # Track how many times each pattern occurs
        pattern_counts = {
            "BASE_EXP_BASE_EXP": 0,
            "EXP_BASE_EXP_BASE": 0,
            "BASE_EXP_EXP_BASE": 0,
            "EXP_BASE_BASE_EXP": 0,
        }

        iterations = 1000

        for _ in range(iterations):
            result = team_draft_interleave(ranking_a, ranking_b, rpp=4)

            # Extract the sequence and join it into a string key
            sequence = [result[i]["type"] for i in sorted(result.keys())]
            pattern_key = "_".join(sequence)

            if pattern_key in pattern_counts:
                pattern_counts[pattern_key] += 1


        # Out of 1000 runs, a perfect 25% distribution is 250.
        # We allow a safe variance window between 190 and 310.
        lower_bound = 190
        upper_bound = 310

        for pattern, count in pattern_counts.items():
            # This catches the impossible 0% cases in Balanced Interleaving
            assert count >= lower_bound, (
                f"Failed: {pattern} occurred {count} times (Expected ~250)."
            )
            # This catches the inflated 50% cases in Balanced Interleaving
            assert count <= upper_bound, (
                f"Failed: {pattern} occurred {count} times (Expected ~250)."
            )
            
