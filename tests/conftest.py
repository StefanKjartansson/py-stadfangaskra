import pandas as pd
import pytest

pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 500)
pd.set_option("display.width", 1000)


@pytest.fixture(scope="module")
def structured_df() -> pd.DataFrame:
    # returns DF with structured data
    return pd.DataFrame(
        {
            "someother_col": ["a", "b", "c"],
            "postcode": [101, 201, 101],
            "street": ["Laugavegur", "Hagasmári", "Laugavegi"],
            "house_nr": [22, 1, 3],
        }
    )


@pytest.fixture(scope="module")
def address_df() -> pd.DataFrame:
    # Dataframe with address string
    return pd.DataFrame(
        {
            "address": [
                "Laugavegur 22, 101 Reykjavík",
                "Hagasmári 1, 201 Kópavogi",
                "Funafold 95",
                "Heimilisfang vantar",
                "Tjarnarflöt 1-2, Garðabær",
                "Bjarmastígur 13, Akureyri",
                "Gilsbakki 4, Fjarðabyggð",
                "Heimilisfang vantar aftur",
                "",
                "Suðurtún 5, Garðabær",
            ]
        }
    )
