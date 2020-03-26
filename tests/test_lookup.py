import pandas as pd
import pytest
from numpy import testing
from stadfangaskra import Lookup

lookup = None


def setup_module(module):  # pylint: disable=unused-argument
    global lookup  # pylint: disable=global-statement
    if lookup is None:
        lookup = Lookup.from_resource()


def test_array() -> None:
    df = pd.DataFrame(
        {
            "postcode": [101, 201],
            "street": ["Laugavegur", "Hagasmári"],
            "house_nr": ["11", "1"],
        }
    )
    df["lat"], df["lon"] = lookup.coordinates_from_array(
        df.postcode.values, df.street.values, df.house_nr.values,
    )


@pytest.mark.parametrize(
    "args",
    [
        (101,),
        (101, "Laugavegur"),
        (101, "Laugavegur", 22),
        (101, "Laugavegi"),
        (101, "Laugavegi", 22),
        (101, "laugavegi", 22),
    ],
)
def test_single(args) -> None:
    assert lookup.single(*args)


def test_case_sensitive():
    assert lookup.single(101, "Laugavegi", 22) == lookup.single(101, "laugavegi", 22)


def test_scan_text():
    text = """
    Einu sinni bjó ég á Háaleitisbraut 68, 103 Reykjavík en
    svo flutti ég á Laugavegi 11, 101 Reykjavík
    """
    res = list(lookup.scan_text(text))
    assert len(res) == 2


def test_hydrate_text_array() -> None:
    df = pd.DataFrame(
        {"address": ["Laugavegur 22, 101 Reykjavík", "Hagasmári 1, 201 Kópavogi",]}
    )

    df[["postcode", "street", "house_nr", "lat", "lon", "municipality"]] = pd.DataFrame(
        lookup.hydrate_text_array(df.address.values), index=df.index
    )

    testing.assert_array_equal(df.postcode.values, [101, 201])
    testing.assert_array_equal(df.street.values, ["Laugavegur", "Hagasmári"])
    testing.assert_array_equal(df.house_nr.values, ["22", "1"])
    testing.assert_array_equal(df.municipality.values, ["Reykjavík", "Kópavogur"])
