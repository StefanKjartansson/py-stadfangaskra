#  pylint: disable=unsupported-assignment-operation,unsubscriptable-object
import argparse
import logging
import pathlib
import sys
import warnings
from urllib.request import urlretrieve

import numpy as np
import pandas as pd

from .config import (
    INT_CATEGORY_COLUMNS,
    POSTCODE_MUNICIPALITY_LOOKUP,
    RENAME_MAP,
    STR_CATEGORY_COLUMNS,
)

SOURCE_URL = "https://gis.skra.is/geoserver/wfs?SERVICE=WFS&VERSION=1.0.0&REQUEST=GetFeature&TYPENAME=public%3aStadfangaskra&SRSNAME=EPSG%3a3057&OutputFormat=csv"
logger = logging.getLogger("preprocess")


def download(dst: pathlib.Path) -> None:
    logger.info("Downloading source file")
    urlretrieve(SOURCE_URL, str(dst))
    logger.info(f"Source file downloaded: {dst}")


def main():
    warnings.filterwarnings("ignore", message=".*initial implementation of Parquet.*")
    default_output_path = pathlib.Path.cwd() / "stadfangaskra/data"
    parser = argparse.ArgumentParser(
        prog="preprocess",
        usage="%(prog)s [options]",
        description="Preprocess Stadfangaskra into optimized and compressed dataframe",
    )
    parser.add_argument(
        "--output-path",
        nargs="?",
        help=f"Output path, default: {default_output_path}",
        default=default_output_path,
    )
    parser.add_argument("--verbose", "-v", help="verbose logging", action="store_true")

    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    output_path = pathlib.Path(args.output_path)
    if not output_path.exists():
        logger.info("Output file folder does not exist: %s", output_path)
        sys.exit(1)
    logger.info("Starting")

    db_path = pathlib.Path.cwd() / "source.csv"
    download(db_path)
    logger.info("Parsing source file")
    df: pd.DataFrame = pd.read_csv(db_path)

    df["SERHEITI"] = df["SERHEITI"].replace(r"^\s*$", np.nan, regex=True)
    df["POSTNR"] = df["POSTNR"].fillna(0).astype(int)

    for c in INT_CATEGORY_COLUMNS:
        logger.debug("Casting %s to int category", c)
        df[c] = pd.Categorical(df[c].astype(pd.Int32Dtype()))

    logger.info("Adding municipality")
    df["municipality"] = df.POSTNR.apply(
        lambda p: POSTCODE_MUNICIPALITY_LOOKUP.get(p, np.nan)
    )

    for c in STR_CATEGORY_COLUMNS:
        logger.debug("Casting %s to str category", c)
        df[c] = df[c].fillna("").astype(str)

    keep = INT_CATEGORY_COLUMNS
    keep.extend(STR_CATEGORY_COLUMNS)
    keep.extend(["N_HNIT_WGS84", "E_HNIT_WGS84", "FID"])
    logger.debug("Discarding all columns except for %s", ", ".join(keep))
    df = df[keep]
    logger.debug("Renaming columns: %s", RENAME_MAP)
    df = df.rename(columns=RENAME_MAP)
    logger.debug("Casting house_nr to uppercase")
    df["house_nr"] = df["house_nr"].str.upper()
    idx = pd.MultiIndex.from_frame(
        df[["municipality", "postcode", "street_nominative", "house_nr"]]
    )

    df = df.set_index(idx).sort_index()

    # filter out duplicated
    df = df.loc[~df.index.duplicated(keep="first")]

    df.to_parquet(output_path / "df.parquet.gzip")


if __name__ == "__main__":
    main()
