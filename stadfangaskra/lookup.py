from dataclasses import dataclass
from typing import Dict, Iterator, Optional, Tuple

import numpy as np
import pandas as pd
from numpy.lib import recfunctions as rfn
from pandas._typing import FilePathOrBuffer

from .matches import Match, iter_matches
from .parser import parse
from .static import POSTCODE_MUNICIPALITY_LOOKUP

Coordinates = Tuple[float, float]
LookupKey = Tuple[int, Optional[str], Optional[str]]
LookupDictT = Dict[LookupKey, Coordinates]


@dataclass
class FullMatch(Match):
    coordinates: Coordinates
    municipality: str


def build_inner_lookup(df: pd.DataFrame) -> LookupDictT:
    """
    Constructs a LookupDictT dictionary from a data frame. It contains keys for
    all combinations of (postcode, street, house number), mean
    values grouped by (postcode, street) and (postcode) which are used when
    no exact match is found.

    :returns: LookupDictT dictionary.
    """
    # match both cases
    cases = ["nominative", "dative"]
    data: LookupDictT = {}
    for case in cases:

        # full matches
        for _, pc, street, house_nr, lat, lon in df[
            ["postcode", f"street_{case}", "house_nr", "lat", "lon"]
        ].to_records():
            data[(pc, street.lower(), house_nr)] = (lat, lon)

        # group by postcode & street name
        for pc, street, lat, lon in (
            df.groupby(["postcode", f"street_{case}"])[["lat", "lon"]]
            .mean()
            .to_records()
        ):
            data[(pc, street.lower(), None)] = (lat, lon)

    # group by postcode
    for pc, lat, lon in df.groupby("postcode")[["lat", "lon"]].mean().to_records():
        data[(pc, None, None)] = (lat, lon)

    return data


class Lookup:
    """
    Lookup 
    """

    data: LookupDictT

    def __init__(self, data: LookupDictT):
        self.data = data

    @staticmethod
    def from_dataframe(df: pd.DataFrame) -> "Lookup":
        """
        Constructs a Lookup instance from a data frame.

        :param df: Dataframe
        :returns: Lookup instance.
        """
        return Lookup(build_inner_lookup(df))

    @staticmethod
    def from_resource(
        filepath_or_buffer: FilePathOrBuffer = "ftp://ftp.skra.is/skra/STADFANG.dsv.zip",
    ) -> "Lookup":
        """
        Construct a Lookup instance from a filepath or buffer, convenience function
        wrapping parse:

        :param filepath_or_buffer: Optional path to Staðfangaskrá file.
        :returns: Lookup instance.
        """
        return Lookup.from_dataframe(parse(filepath_or_buffer=filepath_or_buffer))

    def coordinates_from_array(
        self,
        arr_postcode: np.ndarray,
        arr_streets: np.ndarray,
        arr_house_nr: np.ndarray,
    ) -> np.ndarray:
        """
        Looks up coordinates for arrays of post codes, streets & house numbers. Use when adding coordinates to relatively clean data.

        :Example:

        >>> df["lat"], df["lon"] = (
                d.coordinates_from_array(
                    df.postcodes.values,
                    df.streets.values,
                    df.house_nr.values
                )
            )

        :param arr_postcode: Numpy array of post codes
        :param arr_streets: Numpy array of street names
        :param arr_house_nr: Numpy array of house numbers
        :returns: 2 dimensional Numpy array of coordinates
        """
        arr_len = len(arr_streets)
        out = np.zeros((2, arr_len)) * np.nan
        for idx in range(arr_len):
            res = self.single(arr_postcode[idx], arr_streets[idx], arr_house_nr[idx])
            if not res:
                continue
            out[0][idx], out[1][idx] = res
        return out

    def single(
        self,
        postcode: int,
        street: Optional[str] = None,
        house_nr: Optional[str] = None,
    ) -> Optional[Coordinates]:
        """
        Looks up coordinates for postcode, street & house number. Street &
        house number are optional. F.i. if only a postcode is provided, the
        coordinates will be the average of the coordinates of the postcode,
        likewise if an exact match is not found for a house number, the average
        of coordinate for the postcode, street pair is used.

        .. todo::

            If house number is provided and not found, attempt to find the
            nearest house number and return the coordinates for it instead
            of the average over the street.

        :Example:

        >>> lat, lon = d.single(101)
        >>> lat, lon = d.single(101, "Laugavegur")
        >>> lat, lon = d.single(101, "Laugavegur", 22)

        :param postcode: postcode
        :param street: street name
        :param house number: house number
        :returns: Nearest coordinates.
        """
        key = [postcode, street.lower() if street else None, str(house_nr)]
        if tuple(key) in self.data:
            return self.data[tuple(key)]
        key[2] = None
        if tuple(key) in self.data:
            return self.data[tuple(key)]
        key[1] = None
        if tuple(key) in self.data:
            return self.data[tuple(key)]
        return None

    def scan_text(self, text: str) -> Iterator[FullMatch]:
        """
        Looks up address matches in free-form text. Can be used to find all
        addresses mentioned in a long text.

        >>> list(l.lookup_text("Nóatún Austurveri er að Háaleitisbraut 68, 103 Reykjavík en ég bý á Laugavegi 11, 101 Reykjavík"))

        :param text: free-form text
        :returns: An iterator with full matches.
        """
        for m in iter_matches(text):
            args = (m.postcode, m.street, m.house_nr)
            point = self.single(*args)
            yield FullMatch(*args, point, POSTCODE_MUNICIPALITY_LOOKUP.get(m.postcode))

    def hydrate_text_array(self, text: np.ndarray) -> np.ndarray:
        """
        Looks up matches for each string in the text array.

        Most useful when hydrating semi-structured address data.

        :Example:

        >>> arr = [
                'Laugavegur 22, 101 Reykjavík',
                'Þórsgata 1, 101 Reykjavík',
            ]
        >>> l.hydrate_text_array(arr)



        >>> df = pd.DataFrame({"address": [
                'Laugavegur 22, 101 Reykjavík',
                'Þórsgata 1, 101 Reykjavík',
            ]})
        >>> l.hydrate_text_array(arr)

        :param text: Array or List of text strings
        :returns: Structured Numpy array
        """
        arr_len = len(text)
        postcode = np.zeros(arr_len, dtype=int)
        street = np.zeros(arr_len, dtype="U30")
        house_nr = np.zeros(arr_len, dtype="U5")
        lat = np.zeros(arr_len, dtype=float)
        lon = np.zeros(arr_len, dtype=float)
        municipality = np.zeros(arr_len, dtype="U30")

        for idx, s in enumerate(text):
            m = next(self.scan_text(s))
            if not m:
                continue

            postcode[idx] = m.postcode
            street[idx] = m.street
            house_nr[idx] = m.house_nr
            lat[idx] = m.coordinates[0]
            lon[idx] = m.coordinates[1]
            municipality[idx] = m.municipality

        return rfn.merge_arrays((postcode, street, house_nr, lat, lon, municipality))
