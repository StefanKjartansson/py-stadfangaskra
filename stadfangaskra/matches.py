from dataclasses import dataclass
from typing import Iterator, Optional

from .static import RE_HOUSE_NR, RE_POSTCODE, RE_STREET_ENDING


@dataclass
class Match:
    postcode: int
    street: Optional[str]
    house_nr: Optional[str]


def iter_matches(text: str) -> Iterator[Match]:
    """
    Finds address match candidates in text. The parsing algorithm
    assumes that addresses are written in a common format, e.g.
    "Street number, postcode".

    This is a bit simplistic but should work for most semi-structured
    data sets. It's not designed to be able to parse every possible
    variation in existence.

    :param text: source text
    """
    postcode = None
    street = None
    house_nr = None

    def reset():
        nonlocal postcode
        nonlocal street
        nonlocal house_nr
        postcode = None
        street = None
        house_nr = None

    for w in text.split(" "):
        w = w.strip(",.")
        if RE_STREET_ENDING.search(w):
            street = w
        elif RE_POSTCODE.search(w):
            postcode = int(w)
        elif RE_HOUSE_NR.match(w):
            house_nr = w
        if (postcode and street and house_nr) or (postcode and street) or postcode:
            yield Match(postcode, street, house_nr)
            reset()
