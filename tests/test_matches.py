import pytest

from stadfangaskra import matches


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Laugavegur 22, 101 Reykjavík", [matches.Match(101, "Laugavegur", "22")]),
        ("Laugavegur, 101 Reykjavík", [matches.Match(101, "Laugavegur", None)]),
        ("Laugavegur, 101", [matches.Match(101, "Laugavegur", None)]),
        ("101 Reykjavík", [matches.Match(101, None, None)]),
        (
            "Þórsgata 1 101 Reykjavík, Þórsgata 1 101 Reykjavík",
            [matches.Match(101, "Þórsgata", "1"), matches.Match(101, "Þórsgata", "1")],
        ),
        (
            "Nóatún Austurveri er að Háaleitisbraut 68, 103 Reykjavík",
            [matches.Match(103, "Háaleitisbraut", "68")],
        ),
    ],
)
def test_matches(text, expected) -> None:
    assert list(matches.iter_matches(text)) == expected
