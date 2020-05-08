# py-stadfangaskra

![Python package](https://github.com/StefanKjartansson/py-stadfangaskra/workflows/Python%20package/badge.svg)

Utility library for working with the [Icelandic address registry][stadfangaskra], [pandas] & [geopandas].

### Installation

`pip install py-stadfangaskra`

#### Development

Clone the [repository] and install `dev` extras.

```bash
$ git clone git@github.com:StefanKjartansson/py-stadfangaskra.git
$ cd py-stadfangaskra
# python3.6 & python3.8 are supported as well
$ python3.7 -m venv venv
$ . venv/bin/activate
$ pip install .[dev]
$ py.test
```

### Usage

```python
import stadfangaskra

# Load a dataframe directly from hardcoded ftp path, same as df = stadfangaskra.parse('ftp://ftp.skra.is/skra/STADFANG.dsv.zip'),
# fetches the database from ftp, fairly slow
df = stadfangaskra.parse()
# or use cached local copy, much faster
df = stadfangaskra.parse('STADFANG.dsv.zip')

# Lookup is a utility class for hydrating data using the dataframe.
lookup = stadfangaskra.Lookup.from_dataframe(df)

# Example semi-structured dataframe
some_df = pd.DataFrame({"address": [
    'Laugavegur 22, 101 Reykjavík',
    'Þórsgata 1, 101 Reykjavík',
]})
# hydrate the dataframe, adding columns for postcode, street, house number, latitude, longitude & municipality.
some_df[["postcode", "street", "house_nr", "lat", "lon", "municipality"]] = pd.DataFrame(
    lookup.hydrate_text_array(some_df.address.values), index=some_df.index
)

# Or used to fill latitude & longitude columns in structured datasets
other_df = pd.DataFrame({
    "postcode": [101, 201],
    "street": ["Laugavegur", "Hagasmári"],
    "house_nr": [22, 1],
})

other_df["lat"], other_df["lon"] = (
    lookup.coordinates_from_array(
        df.postcode.values,
        df.street.values,
        df.house_nr.values
    )
)

# Or be used to iterate address matches in text.
my_text = """
Nóatún Austurveri er að Háaleitisbraut 68, 103 Reykjavík en ég bý á Laugavegi 11, 101 Reykjavík
"""

for m in lookup.lookup_text(my_text):
    print(m)
```

[stadfangaskra]: https://github.com/StefanKjartansson/py-stadfangaskra
[pandas]: https://pandas.pydata.org/
[geopandas]: https://geopandas.org/
[repository]: https://opingogn.is/dataset/stadfangaskra
