import pytest

from silicon_archaeology.stratigraphy import (
    EPOCHS,
    classify_epoch,
    known_hardware_database,
)


def test_known_hardware_match_is_normalized_and_serializable():
    result = classify_epoch(" intel ", "  4004  ", 1971)

    assert result == {
        "epoch_number": 1,
        "era_name": "Pre-VLSI",
        "rarity_score": 96,
        "matched_known_hardware": {
            "cpu_family": "Intel",
            "model": "4004",
            "year": 1971,
            "epoch": 1,
            "rarity_score": 96,
        },
    }


@pytest.mark.parametrize(
    ("year", "expected_epoch", "expected_rarity"),
    [
        (1977, 1, 85),
        (1978, 2, 70),
        (1986, 2, 70),
        (1987, 3, 58),
        (1994, 3, 58),
        (1995, 4, 38),
        (2015, 4, 38),
        (2016, 5, 24),
    ],
)
def test_unknown_hardware_uses_year_boundary_edges(year, expected_epoch, expected_rarity):
    result = classify_epoch("Acme", f"Prototype {year}", year)

    assert result["epoch_number"] == expected_epoch
    assert result["era_name"] == EPOCHS[expected_epoch]
    assert result["rarity_score"] == expected_rarity
    assert result["matched_known_hardware"] is None


def test_unknown_risc_v_family_gets_modern_rarity_boost():
    result = classify_epoch("RISC-V", "Experimental Board", 2024)

    assert result["epoch_number"] == 5
    assert result["era_name"] == "Post-Moore"
    assert result["rarity_score"] == 34
    assert result["matched_known_hardware"] is None


def test_unknown_intel_core_model_gets_commonality_discount():
    result = classify_epoch("Intel", "Core Ultra 9", 2024)

    assert result["epoch_number"] == 5
    assert result["rarity_score"] == 16
    assert result["matched_known_hardware"] is None


def test_known_hardware_database_returns_independent_dicts():
    first = known_hardware_database()
    first[0]["model"] = "mutated"

    second = known_hardware_database()

    assert second[0]["model"] == "PDP-8"
    assert all({"cpu_family", "model", "year", "epoch", "rarity_score"} <= set(row) for row in second)
