#  pylint: disable=redefined-outer-name
import pytest
from numpy import testing

from stadfangaskra import lookup

my_text = """
Nóatún Austurveri er að Háaleitisbraut 68, 103 Reykjavík en ég bý á Laugavegi 11, 101 Reykjavík
""".strip()


def test_edge_cases() -> None:
    res = lookup.query("Hagasmári 1, 201 Kópavogi")
    assert len(res) == 1


def test_query_dataframe(structured_df):
    res = lookup.query_dataframe(structured_df)
    testing.assert_array_equal(structured_df.postcode.values, res.postcode.values)
    testing.assert_array_equal(
        res.street_nominative.values, ["Laugavegur", "Hagasmári", "Laugavegur"]
    )


def test_query_text_body() -> None:
    results = lookup.query_text_body(my_text)
    testing.assert_array_equal(results.postcode.values, ["103", "101"])
    testing.assert_array_equal(
        results.street_nominative.values, ["Háaleitisbraut", "Laugavegur"]
    )


def test_multiple_matches() -> None:
    res = lookup.query("Hafnarbraut 1")
    print(res)
    testing.assert_array_equal(res.postcode, [""])
    testing.assert_array_equal(res.municipality, [""])
    testing.assert_array_equal(res.house_nr, [""])
    testing.assert_array_equal(res.geometry, [None])


@pytest.mark.parametrize(
    "query,postcode,municipality,house_nr",
    [
        ("Lindarbraut 25, Seltjarnarnesbær", "170", "Seltjarnarnes", "25"),
    ],
)
def test_weird_cases(
    query: str, postcode: str, municipality: str, house_nr: str
) -> None:
    res = lookup.query(query)
    print(res)
    testing.assert_array_equal(res.postcode, [postcode])
    testing.assert_array_equal(res.municipality, [municipality])
    testing.assert_array_equal(res.house_nr, [house_nr])
