import pandas as pd
import pytest
from numpy import testing

import stadfangaskra


def test_hydrate_string_field(address_df) -> None:
    print(address_df)
    res = address_df.stadfangaskra.hydrate()
    assert len(res)
    print(res)

    testing.assert_array_equal(
        res.postcode.values,
        ["101", "201", "112", "", "210", "600", "740", "", "", "225"],
    )
    testing.assert_array_equal(
        res.street_nominative.values,
        [
            "Laugavegur",
            "Hagasmári",
            "Funafold",
            "",
            "Tjarnarflöt",
            "Bjarmastígur",
            "Gilsbakki",
            "",
            "",
            "Suðurtún",
        ],
    )
    testing.assert_array_equal(
        res.house_nr.values, ["22", "1", "95", "", "1", "13", "4", "", "", "5"]
    )
    testing.assert_array_equal(
        res.municipality.values,
        [
            "Reykjavík",
            "Kópavogur",
            "Reykjavík",
            "",
            "Garðabær",
            "Akureyri",
            "Neskaupstaður",
            "",
            "",
            "Garðabær (Álftanes)",
        ],
    )


def test_hydrate_structured_fields(structured_df):
    res = structured_df.stadfangaskra.hydrate()
    testing.assert_array_equal(structured_df.postcode.values, res.postcode.values)
    testing.assert_array_equal(
        res.street_nominative.values, ["Laugavegur", "Hagasmári", "Laugavegur"]
    )


def test_hydrate_structured_fields_idx(structured_df):
    structured_df = structured_df.set_index("someother_col")
    res = structured_df.stadfangaskra.hydrate()
    testing.assert_array_equal(structured_df.postcode.values, res.postcode.values)
    testing.assert_array_equal(
        res.street_nominative.values, ["Laugavegur", "Hagasmári", "Laugavegur"]
    )


def test_hydrate_structured_fields_partial():
    df = pd.DataFrame(
        {
            "postcode": ["", ""],
            "street": ["Funafold", "Funafold"],
            "house_nr": ["95", "95"],
        }
    )
    res = df.stadfangaskra.hydrate()
    testing.assert_array_equal(["112", "112"], res.postcode.values)
    testing.assert_array_equal(res.municipality.values, ["Reykjavík", "Reykjavík"])


def test_assert_raises_attribute_error() -> None:
    df = pd.DataFrame()
    with pytest.raises(AttributeError):
        df.stadfangaskra.hydrate_address()


def test_with_index() -> None:
    df = pd.DataFrame({
        "address": ["Hraungata 18, Garðabær", "Víðigrund 57, Kópavogur", "Reykás 21, Reykjavík"],
        "idx": ["a", "b", "c"],
    }).set_index("idx")
    res = df.stadfangaskra.hydrate()
    print(res)
    testing.assert_array_equal(["a", "b", "c"], res.index.values)
    #assert False
