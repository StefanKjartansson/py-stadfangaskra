import numpy as np
import pandas as pd
import geopandas
from pandas._typing import FilePathOrBuffer

RENAMED = {
    "BOKST": "house_char",
    "HEITI_NF": "street_nominative",
    "HEITI_TGF": "street_dative",
    "HNITNUM": "id",
    "HUSNR": "house_nr",
    "LAT_WGS84": "lat",
    "LONG_WGS84": "lon",
    "POSTNR": "postcode",
    "SVFNR": "municipality",
}


def merge_house_char(
    house_nr_arr: np.ndarray, house_char_arr: np.ndarray
) -> np.ndarray:
    """
    Merges house nr & house char arrays in to a single array.    
    """
    out = np.zeros(len(house_nr_arr), dtype=np.dtype("U5"))
    for idx, h in enumerate(house_nr_arr):
        val = ""
        if not np.isnan(h):
            val += str(int(h))
        c = house_char_arr[idx]
        if isinstance(c, float) and not np.isnan(c):
            val += str(int(c))
        elif isinstance(c, str):
            val += c
        out[idx] = val.strip().lower()
    return out


def parse(
    filepath_or_buffer: FilePathOrBuffer = "ftp://ftp.skra.is/skra/STADFANG.dsv.zip",
) -> pd.DataFrame:
    """
    Reads the Staðfangaskrá, trimming it down to the RENAMED
    columns and converting data types.

    Examples
    --------
    >>> import stadfangaskra
    >>> df = stadfangaskra.parse('ftp://ftp.skra.is/skra/STADFANG.dsv.zip')
    >>> df = stadfangaskra.parse('STADFANG.dsv.zip')

    :param filepath_or_buffer: Path to Staðfangaskrá file or url.
    :returns: DataFrame.
    """
    df = pd.read_csv(filepath_or_buffer, delimiter="|", usecols=list(RENAMED.keys()))
    df = df.rename(columns=RENAMED).set_index("id")

    df["house_nr"] = merge_house_char(df.house_nr.values, df.house_char.values)
    df = df.drop(["house_char"], axis=1)
    df["postcode"] = df["postcode"].fillna(-1).astype(int)
    df["municipality"] = df["municipality"].fillna(-1).astype(int)
    df["lat"] = df["lat"].str.replace(",", ".").astype(float)
    df["lon"] = df["lon"].str.replace(",", ".").astype(float)

    df = df.dropna()
    return geopandas.GeoDataFrame(df, geometry=geopandas.points_from_xy(df.lon, df.lat))
