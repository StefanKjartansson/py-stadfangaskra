from typing import Dict, List, Tuple, Union

import geopandas
import numpy as np
import pandas as pd

from .matches import iter_matches
from .static import ADMINISTRATIVE_DIVISIONS, POSTCODE_MUNICIPALITY_LOOKUP
from .static import df as STATIC_DF

INDEX_COLS = ["municipality", "postcode", "street_nominative", "house_nr"]


def is_valid_idx(x: Tuple[str, str, str, str]):
    if not x[0] and not x[1] and not x[2]:
        return False
    return True


def merge_tuples(
    sq: Tuple[
        Union[str, slice], Union[str, slice], Union[str, slice], Union[str, slice]
    ],
    res: pd.MultiIndex,
) -> Tuple[str, str, str, str]:
    """Replace tuple values where the index is an empty slice.

    Behaviour change in pandas 1.4, in previous versions the full index was returned.
    Post 1.4, pandas returns only the missing levels.

    :param sq: query tuple
    :type sq: Tuple[ Union[str, slice], Union[str, slice], Union[str, slice], Union[str, slice] ]
    :param res: index part
    :type res: Tuple
    :return: Full lookup value
    :rtype: Tuple[str, str, str, str]
    """
    out = list(sq)
    for n in res.names:
        idx = INDEX_COLS.index(n)
        out[idx] = res.get_level_values(n)[0]
    return tuple(out)


def _build_municipality_street_to_postcode(
    df: pd.DataFrame,
) -> Dict[Tuple[str, str], str]:
    """Builds a lookup table of

    (municipality, street) => postcode

    Non unique matches, i.e. a street spanning more than a single postcode are dropped.

    :param df: [description]
    :type df: pd.DataFrame
    :return: [description]
    :rtype: Dict[Tuple[str, str], str]
    """
    out = {}
    delete_list = []
    for t, sn, sd, pc in (
        df[["municipality", "street_nominative", "street_dative", "postcode"]]
        .drop_duplicates()
        .values
    ):
        if (t, sn) in out and out[(t, sn)] != str(pc):
            delete_list.append((t, sn))
            continue
        out[(t, sn)] = str(pc)
        out[(t, sd)] = str(pc)
    for k in delete_list:
        out.pop(k, None)
    return out


class Lookup:
    """
    Utility class for doing reverse geocoding lookups from the dataframe.

    How it works:
    - The dataframe has a few categorical columns whose code values are used
      for constructing a multidimensional search tree.
    - When querying, a best-effort approach is used to translate the
      input string into a vector to query the tree.
    """

    df: pd.DataFrame
    town_street_to_postcode: Dict[Tuple[str, str], str]
    streets: List[str]
    house_nrs: List[str]
    postcodes: List[str]
    municipalities: List[str]
    street_dative: Dict[str, str]

    def __init__(self) -> "Lookup":
        self.df = STATIC_DF.copy().sort_index()
        self.town_street_to_postcode = _build_municipality_street_to_postcode(self.df)
        self.streets = self.df.index.levels[2]
        self.house_nrs = self.df.index.levels[3]
        self.postcodes = self.df.index.levels[1]
        self.municipalities = self.df.index.levels[0]
        self.street_dative = dict(
            self.df[["street_dative", "street_nominative"]]
            .reset_index(drop=True)
            .values
        )

    def text_to_vec(  # pylint: disable=too-many-branches
        self, s: str
    ) -> Tuple[str, str, str, str]:
        """Builds a tuple out of an address string.

        * index 0, category value of the "municipality" category.
        * index 1, category value of the "postcode" category.
        * index 2, category value of the "street_nominative" category.
        * index 3, category value of the "house_nr" category.

        :param s: string containing address
        :type s: str
        :return: Address tuple
        :rtype: Tuple[str, str, str, str]
        """
        municipality = ""
        postcode = ""
        street = ""
        house_nr = ""
        admin_unit = ""

        # Exit early if the string is empty
        if not s:
            return ("", "", "", "")

        for w in s.split(" "):
            w = w.strip(",.")

            if not street and w in self.streets:
                street = w

            if not house_nr and (w.upper() in self.house_nrs or "-" in w):
                house_nr = w

            if not postcode and w in self.postcodes and w != house_nr:
                postcode = w
                municipality = POSTCODE_MUNICIPALITY_LOOKUP.get(int(postcode), "")

            if not postcode and not municipality and w in self.municipalities:
                municipality = w
            if not municipality and w in ADMINISTRATIVE_DIVISIONS:
                admin_unit = w

        if admin_unit and street:
            for tn in ADMINISTRATIVE_DIVISIONS[admin_unit]:
                postcode = self.town_street_to_postcode.get((tn, street), "")
                if not postcode:
                    continue
                municipality = tn
                break

        # if we have municipality and street but no postcode, try looking it up
        if municipality and street and not postcode:
            postcode = self.town_street_to_postcode.get((municipality, street), "")
            # Álftanes has a special case
            if not postcode and municipality == "Garðabær":
                postcode = self.town_street_to_postcode.get(
                    ("Garðabær (Álftanes)", street)
                )
                if postcode:
                    municipality = "Garðabær (Álftanes)"

        if house_nr and "-" in house_nr:
            house_nr = house_nr.split("-")[0]

        return (
            municipality or "",
            postcode or "",
            street or "",
            (house_nr or "").upper(),
        )

    def __query_vector_dataframe(self, q: pd.DataFrame) -> pd.DataFrame:
        """Given a data frame with index:
          [municipality, postcode, street_nominative, house_nr]
        and columns "qidx" (query index) and "order", matches exact and
        partial matches to the address dataframe.

        :param q: query dataframe
        :type q: pd.DataFrame
        :return: query dataframe with additional address columns
        :rtype: pd.DataFrame
        """

        # get intersecting indexes
        found = self.df.index.intersection(q.index)

        idx_names = self.df.index.names

        # find indexes in the query dataframe which couldn't be found,
        # these could be empty queries or partial matches.
        missing = q.index.difference(found).unique()

        if len(missing):
            # create a set of the found values, the purpose is to have a mutable
            # data structure to work with.
            found_missing = set(found.values)
            # get unique set of missing queries
            miss_df = q.loc[missing].drop_duplicates()

            # keep track of query idx that have not been found
            not_found_qidx = set()

            missing_data = []

            miss_df = miss_df.loc[miss_df.index.map(is_valid_idx)]

            # as the address dataframe is fairly large, constrict the search
            # space to the records loosely matching what's being queried for. For
            # large datasets, this speeds up querying considerably.
            search_selector = [
                slice(None) if (i[0] == "" and len(i) == 1) else i
                for i in [
                    i.values.tolist()
                    for i in miss_df.index.remove_unused_levels().levels
                ]
            ]

            search_space = self.df.loc[tuple(search_selector), :]

            # iterate rows of valid missing indexes
            for tvec, row in miss_df.iterrows():
                qidx = row["qidx"]

                # the index is 4 levels, [municipality, postcode, street, house_nr],
                # all of these values are allowed to be an empty string, except at
                # this point it is clear that a key with an empty string could not
                # be found in the index.
                # Replace all empty strings with a None slice and query the address dataframe
                sq = tuple((i or slice(None) for i in tvec))
                # NOTE: Author has not founded a vectorized approach to querying the
                # source dataframe and matching the query index back with the result.
                try:
                    res = search_space.loc[sq]
                except KeyError:
                    continue

                # if an exact match could be found, assign it as the value of the query
                # dataframe for the given index. In case there are duplicates, check
                # if it's already been found
                if len(res) == 1:
                    # mark the returned tuple for addition to the found indexes
                    res_val = merge_tuples(sq, res.index)
                    found_missing.add(res_val)
                    # create a new row for the missing data
                    missing_data.append(res_val + tuple(row))

                    # mark old data query index for deletion
                    not_found_qidx.add(qidx)

                # NOTE: here there are multiple matches, theoretically possible to train
                # a model which would give higher priority to a generic address determined
                # by its frequency over a corpus.

            # delete found qidx from the original query frame
            q = q[~q["qidx"].isin(not_found_qidx)]
            # concat the missing data found with the query data frame
            q = pd.concat(
                [
                    q,
                    pd.DataFrame(
                        missing_data, columns=idx_names + q.columns.tolist()
                    ).set_index(idx_names),
                ]
            )
            # rebuild the multiindex after mutating it
            found = pd.MultiIndex.from_tuples(list(found_missing), names=idx_names)

        # select indexable records, right join with the query dataframe
        # and sort by the original query order.
        out = self.df.loc[found].join(q, how="right").sort_values("order")

        # fill NaN string values
        out[
            [
                "municipality",
                "postcode",
                "special_name",
                "house_nr",
                "street_dative",
                "street_nominative",
            ]
        ] = out[
            [
                "municipality",
                "postcode",
                "special_name",
                "house_nr",
                "street_dative",
                "street_nominative",
            ]
        ].fillna(
            value=""
        )

        out.reset_index(level=[0, 1, 2, 3], drop=True, inplace=True)
        return out

    def query_dataframe(
        self,
        q: pd.DataFrame,
    ) -> pd.DataFrame:
        """Queries a data frame containing structued data,
        columns [postcode, house_nr, street/street_nominative] are
        required, [municipality] is optional.

        :param q: query dataframe
        :type q: pd.DataFrame
        :return: query dataframe with additional address columns
        :rtype: pd.DataFrame
        """

        cols = q.columns
        q["postcode"] = q["postcode"].astype(str)
        if "municipality" not in cols:
            q["municipality"] = q["postcode"].apply(
                lambda pc: POSTCODE_MUNICIPALITY_LOOKUP.get(
                    int(pc) if pc.isdigit() else -1, ""
                )
            )
        q["house_nr"] = q["house_nr"].astype(str)
        if "street" in cols and "street_nominative" not in cols:
            q = q.rename(columns={"street": "street_nominative"})

        q["street_nominative"] = q["street_nominative"].apply(
            lambda v: self.street_dative.get(v, v)
        )

        q["qidx"] = pd.Categorical(
            q[self.df.index.names].apply(
                lambda x: "/".join(x.dropna().astype(str).values), axis=1
            )
        ).codes
        q["order"] = list(range(len(q)))

        q = q.set_index(keys=self.df.index.names)

        return self.__query_vector_dataframe(q)

    def query(  # pylint: disable=too-many-locals
        self, text: Union[str, List[str], np.ndarray]
    ) -> geopandas.GeoDataFrame:
        """Given text input, returns a dataframe with matching addresses

        :param text: string containing a single address or an iterator
                     containing multiple addresses.
        :type text: Union[str, List[str], np.ndarray]
        :return: Data frame containg addresses
        :rtype: geopandas.GeoDataFrame
        """
        if isinstance(text, str):
            text = [text]

        # strip whitespace from text
        text = [t.strip() for t in text]

        # tokenize strings into a list of tuples,
        # [municipality, postcode, street_nominative, house_nr]
        vecs = [self.text_to_vec(t) for t in text]

        # construct dataframe from parsed results
        q = pd.DataFrame(vecs, columns=self.df.index.names)

        # Set original search query and idx of the query
        q["query"] = text
        # there might be duplicated values, cast the query as a category
        # this is used as the id of the query
        q["qidx"] = q["query"].astype("category").cat.codes

        # keep the original order of the query
        q["order"] = list(range(len(text)))

        # set the tokenized vector of
        # [municipality, postcode, street_nominative, house_nr] as the index
        q = q.set_index(keys=self.df.index.names)
        return self.__query_vector_dataframe(q)

    def query_text_body(self, text: str) -> pd.DataFrame:
        """Queries a body of text.

        This is a special case API for parsing multiple addresses from
        a block of text.

        :param text: block of text
        :type text: str
        :return: Data frame containg addresses
        :rtype: pd.DataFrame
        """

        arr = []

        for m in iter_matches(text):
            if not m:  # pragma: no cover
                break
            arr.append(m)

        df = pd.DataFrame(arr)
        return self.query_dataframe(df)
