import pandas as pd
import pytest
from numpy import testing

from stadfangaskra import lookup


@pytest.fixture
def duplicates_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "address": [
                "Laugavegur 22, 101 Reykjavík",
                "Laugavegur 22, 101 Reykjavík",
                "Laugavegur 22, 101 Reykjavík",
            ]
        }
    )


def test_detect_duplicates(duplicates_dataframe: pd.DataFrame) -> None:
    res = lookup.query(duplicates_dataframe.address.values)
    print(res)
    assert len(res) == 3


def test_missing_match_duplicate() -> None:
    df = pd.DataFrame(
        {
            "address": [
                "Funafold 95",
                "Funafold 95 ",
                "Funafold 95",
            ]
        }
    )
    res = lookup.query(df.address.values)
    print(res)
    assert len(res) == 3
    testing.assert_array_equal(res.postcode.values, ["112", "112", "112"])


def test_differently_formatted_duplicates() -> None:
    df = pd.DataFrame(
        {
            "address": [
                "Funafold 95",
                "Funafold 95, 112",
                "Funafold 95, 112 Reykjavík",
            ]
        }
    )
    res = lookup.query(df.address.values)
    print(res)
    assert len(res) == 3
    testing.assert_array_equal(res.postcode.values, ["112", "112", "112"])
