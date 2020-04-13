# py-stadfangaskra

Utility library for working with the Icelandic address registry and pandas. Development is at a "scratching my own itch" stage.


### Installation

Until it's packages properly, it can be installed from GitHub.

`pip install git+https://github.com/StefanKjartansson/py-stadfangaskra`

### Usage

```python
import stadfangaskra

# Load a dataframe directly from hardcoded ftp path, same as df = stadfangaskra.parse('ftp://ftp.skra.is/skra/STADFANG.dsv.zip'), 
# fetches the database via ftp, fairly slow
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
    lookup.hydrate_text_array(some_df.address.values), index=df.index
)
```
