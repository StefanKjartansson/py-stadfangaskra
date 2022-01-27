# py-stadfangaskra

![Python package](https://github.com/StefanKjartansson/py-stadfangaskra/workflows/Python%20package/badge.svg)

Utility library for working with the [Icelandic address registry][stadfangaskra], [pandas] & [geopandas]. The primary use-case is to
hydrate address data.

### Installation

`pip install py-stadfangaskra`

#### Development

FIX: Clone the [repository] and install `dev` extras.

```bash
$ git clone git@github.com:StefanKjartansson/py-stadfangaskra.git
$ cd py-stadfangaskra
# python3.6 & python3.8 are supported as well
$ python3.9 -m venv venv
$ . venv/bin/activate
$ pip install .[dev]
$ py.test
```

### Usage example

#### Hydrating datasets

```python
import pandas as pd

# importing the library registers a pandas dataframe accessor
import stadfangaskra

# Given a data frame with an address field
df = pd.DataFrame(
    {
        "address": [
            "Laugavegur 22, 101 Reykjavík",
            "Þórsgata 1, 101 Reykjavík",
            "Funafold 93",
        ]
    }
)

# hydrate returns a geopandas dataframe with expanded address data & geometry
print(df.stadfangaskra.hydrate())

   index                       address                         query municipality postcode street_nominative street_dative house_nr                    geometry
0      0  Laugavegur 22, 101 Reykjavík  Laugavegur 22, 101 Reykjavík    Reykjavík      101        Laugavegur     Laugavegi       22  POINT (-21.92913 64.14558)
1      1     Þórsgata 1, 101 Reykjavík     Þórsgata 1, 101 Reykjavík    Reykjavík      101          Þórsgata      Þórsgötu        1  POINT (-21.93151 64.14402)
2      2                   Funafold 93                   Funafold 93    Reykjavík      112          Funafold      Funafold       93  POINT (-21.80640 64.13422)


# Also works with structured data
df = pd.DataFrame(
    {
        "postcode": [101, 201],
        "street": ["Laugavegur", "Hagasmári"],
        "house_nr": [22, 1],
    }
)

print(df.stadfangaskra.hydrate())
  municipality_code street_nominative street_dative house_nr special_name municipality postcode                    geometry
0                 0        Laugavegur     Laugavegi       22                 Reykjavík      101  POINT (-21.92913 64.14558)
1              1000         Hagasmári     Hagasmára        1    Smáralind    Kópavogur      201  POINT (-21.88327 64.10105)
```

#### Hydrating without using accessor

```python
from stadfangaskra import lookup

# hydrate string
lookup.query("Hagasmári 1, 201 Kópavogi")
# or list of strings
lookup.query(["Hagasmári 1, Kópavogi", "Laugavegur 22, 101 Reykjavík"])

# or iterate matches in a text body
txt = "Nóatún Austurveri er að Háaleitisbraut 68, 103 Reykjavík en ég bý á Laugavegi 11, 101 Reykjavík"

print(lookup.query_text_body(txt))
```



[stadfangaskra]: https://github.com/StefanKjartansson/py-stadfangaskra
[pandas]: https://pandas.pydata.org/
[geopandas]: https://geopandas.org/
[repository]: https://opingogn.is/dataset/stadfangaskra
