import logging
from typing import List

import pandas as pd

from .static import df, regions
from .tree import Lookup

__all__ = ["df", "Lookup", "regions"]

lookup = Lookup()
logger = logging.getLogger("stadfangaskra")


def _is_structured(cols: List[str]) -> bool:
    return (
        "postcode" in cols
        and ("street" in cols or "street_nominative" in cols)
        and "house_nr" in cols
    )


@pd.api.extensions.register_dataframe_accessor("stadfangaskra")
class SDAccessor:  # pylint: disable=too-few-public-methods
    def __init__(self, pandas_obj):
        self._validate(pandas_obj)
        self._obj = pandas_obj

    @staticmethod
    def _validate(obj):
        cols = obj.columns
        if not _is_structured(cols) and "address" not in cols:
            raise AttributeError("Must have 'address' data.")

    def __query_structured(self) -> pd.DataFrame:
        qf: pd.DataFrame = self._obj
        should_reset_index = bool(qf.index.name)
        if should_reset_index:
            qf = qf.reset_index()
        res = lookup.query_dataframe(qf)
        if should_reset_index:
            res = res.set_index(self._obj.index.name)
        else:
            res = res.reset_index(drop=True)
        res = res.drop("fid", axis=1)
        return res

    def hydrate(self, query_column: str = "address") -> pd.DataFrame:

        qf: pd.DataFrame = self._obj
        original_index = self._obj.index.name
        is_structured = _is_structured(qf.columns)
        if is_structured:
            return self.__query_structured()

        cols = list(qf.columns)
        if query_column not in cols:
            raise AttributeError(f"query column {query_column} missing")

        addrs = qf[query_column].values

        res = lookup.query(addrs)
        logger.debug("len after lookup: %d", len(res))

        qf.reset_index(inplace=True)
        qf["query"] = qf[query_column]
        qf = qf.set_index("query")
        res.set_index("query", inplace=True)

        res = qf.join(res).sort_values("order")
        logger.debug("len after joining on query: %d", len(res))

        cols.extend(
            [
                "municipality",
                "postcode",
                "street_nominative",
                "street_dative",
                "house_nr",
                "geometry",
            ]
        )

        if original_index:
            res.set_index(original_index, inplace=True)
            res = res.loc[~res.index.duplicated(keep="first")]
            logger.debug("len after removing duplicated indices: %d", len(res))
        else:
            res.reset_index(inplace=True)

        return res[cols]
