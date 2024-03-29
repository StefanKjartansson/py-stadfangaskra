# pylint: disable=line-too-long
import re
from typing import Dict, List

import geopandas
import pandas as pd
import pkg_resources

RE_STREET_ENDING = re.compile(
    r"(((hjálei|brin)g|bryggj|kirkj|s(kemm|eyl|tof|íð)|le(ir|ys))[au]|afréttu[mr]|(h(jallu|am(ra|a)|e(iða|lli)|ólmu|óla)|fjörðu|t(jarn|rað)i|(sveig|naut|teig|dal|læk)u|b(org|rún)i|(heim|krók)a|garð[au]|s(kóga|and[au]|tað[iu])|lauga|(graf|flat|sal)i|eyra|mela|aku|kó)r|(brunn|hvamm|stekk|[bk]lett|kamb|lund|reit|núp)(ur|i)|(dran|stí)g(ur|i)|(s((kerj|töp)u|kálu|ö(nd|l)u)|b(org|rún)u|h(eið|ól)u|(bö(kk|l)|g(röf|örð)|hömr)u|laugu|eyru|endu|kofu)m|(f(jöll|löt)|stöð|fold|lönd)um|tjörnum|(brekk|tung)(u[mr]?|a)|h(e(ll(um|a)|iði)|vilft|jall[ai]|amri|úsið|ólm[ai]|óll|öfn)|s(t(einn|api)|k((er|ál)i|ógi)|andi)|(strö|gru)nd|(hverf|stræ[tð]|(ger|s[tv]æ)ð|firð|eng|bæl|mýr|akr)i|((ba(kk|l)|mó)a|s(kál|tap)a|e(yj|nd)a|kofa)r|(grand|geisl|h(öfð|ag)|k(rik|im)|s(kól|már)|tang|múl|fló|rim)[ai]|((heim|krók)u|skógu|melu)[mr]|v(ellir|(an|o)g(ur|i)|ö(tnum|llu[mr]|r)|iður|eg(ur|i)|it[ai]|ík)|(h(úsin|löð)|göt)u|(h(varf|o(lt|f))|s(karð|el)|f(j(all|ós)|ell|oss)|(h(rau|or)|ló|tú)n|(bar|hli)ð|(hál|ne)s|sund|land|torg|vatn|ból|kot|gil)i|b(ja|e)rgi|h(ellu|úsi?|ól)|s(t(ein|að)|k(er|ál))|(ba(kk|l)|mó)a|s(kál|tap)a|sveig|f(jöll|löt)|tjörn|v(elli|ötn|ið)|h(varf|o(lt|f))|s(karð|el)|f(j(all|ós)|ell|oss)|(h(rau|or)|ló|tú)n|b(ja|e)rg|eyris|b(jörg|aki|ær|ót)|braut|(heim|krók)i|garði|(ba(kk|l)|mó)i|(hlað|gat|ald)a|fj(ara|öru)|l(ei(ti|ð)|aut|ind)|(b(rei|ygg|ú)|h(lí|æ)|s[lt]ó)ð|t(orf[au]|r(aða|öð))|jekdu|þ(ingi?|úf(u[mr]?|a))|ey(ri)?|b(org|rún?|ak|æ)|laug|e(yj|nd)a|kofa|naut|teig|stöð|fold|lönd|(bar|hli)ð|(hál|ne)s|sund|land|torg|vatn|endi|k(ofi|inn|lif)|mörk|öldu|mel|dal|læk|ból|kot|gil|ás)$"
)
RE_POSTCODE = re.compile(
    r"^(1(0[1-57-9]|1[0-36]|6[12])|2(0[0136]|3[035]|6[02])|34[0-25]|5(1[0-2]|2[04])|27[016]|6(0[013-7]|1[016])|(24|35|4[26]|5[46]|6[278])[0156]|(22|64)[015]|7([356][0156]|[18][015])|41[056]|(19|25|3[0178]|4[0357]|5[358]|69|7[024])[01]|8(0[013-6]|2[05]|[14][056]|[5-8][01])|(17|21|3[26]|5[07]|6[356])0|900)$"
)
RE_HOUSE_NR = re.compile(r"[\d+]?[\w+]?")


POSTCODE_MUNICIPALITY_LOOKUP: Dict[int, str] = {
    300: "Akranes",
    301: "Akranes",
    302: "Akranes",
    600: "Akureyri",
    601: "Akureyri",
    602: "Akureyri",
    603: "Akureyri",
    604: "Akureyri",
    605: "Akureyri",
    606: "Akureyri",
    607: "Akureyri",
    524: "Árneshreppur",
    685: "Bakkafjörður",
    686: "Bakkafjörður",
    465: "Bíldudalur",
    466: "Bíldudalur",
    540: "Blönduós",
    541: "Blönduós",
    415: "Bolungarvík",
    416: "Bolungarvík",
    720: "Borgarfjörður (eystri)",
    721: "Borgarfjörður (eystri)",
    310: "Borgarnes",
    311: "Borgarnes",
    760: "Breiðdalsvík",
    761: "Breiðdalsvík",
    370: "Búðardalur",
    371: "Búðardalur",
    620: "Dalvík",
    621: "Dalvík",
    765: "Djúpavogur",
    766: "Djúpavogur",
    520: "Drangsnes",
    700: "Egilsstöðir",
    701: "Egilsstöðir",
    735: "Eskifjörður",
    736: "Eskifjörður",
    820: "Eyrarbakki",
    750: "Fáskrúðsfjörður",
    751: "Fáskrúðsfjörður",
    345: "Flatey á Breiðafirði",
    425: "Flateyri",
    426: "Flateyri",
    570: "Fljótum",
    845: "Flúðir",
    846: "Flúðir",
    645: "Fosshólli",
    210: "Garðabær",
    212: "Garðabær",
    225: "Garðabær (Álftanes)",
    250: "Garður",
    251: "Garður",
    610: "Grenivík",
    616: "Grenivík",
    611: "Grímsey",
    240: "Grindavík",
    241: "Grindavík",
    350: "Grundarfjörður",
    351: "Grundarfjörður",
    220: "Hafnarfjörður",
    221: "Hafnarfjörður",
    222: "Hafnarfjörður",
    360: "Hellissandur",
    850: "Hella",
    851: "Hella",
    410: "Hnífsdalur",
    780: "Höfn í Hornafirði",
    781: "Höfn í Hornafirði",
    565: "Hofsós",
    566: "Hofsós",
    510: "Hólmavík",
    511: "Hólmavík",
    512: "Hólmavík",
    630: "Hrísey",
    640: "Húsavík",
    641: "Húsavík",
    530: "Hvammstangi",
    531: "Hvammstangi",
    810: "Hveragerði",
    860: "Hvolsvöllur",
    861: "Hvolsvöllur",
    400: "Ísafjörður",
    401: "Ísafjörður",
    235: "Keflavíkurflugvöllur",
    880: "Kirkjubæjarklaustur",
    881: "Kirkjubæjarklaustur",
    670: "Kópasker",
    671: "Kópasker",
    200: "Kópavogur",
    201: "Kópavogur",
    202: "Kópavogur",
    203: "Kópavogur",
    206: "Kópavogur",
    840: "Laugarvatn",
    650: "Laugar",
    715: "Mjóifjörður",
    270: "Mosfellsbær",
    271: "Mosfellsbær",
    276: "Mosfellsbær",
    660: "Mývatn",
    740: "Neskaupstaður",
    741: "Neskaupstaður",
    625: "Ólafsfjörður",
    626: "Ólafsfjörður",
    355: "Ólafsvík",
    816: "Ölfus",
    785: "Öræfum",
    450: "Patreksfjörður",
    451: "Patreksfjörður",
    675: "Raufarhöfn",
    676: "Raufarhöfn",
    730: "Reyðarfjörður",
    731: "Reyðarfjörður",
    380: "Reykhólahreppur",
    381: "Reykhólahreppur",
    320: "Reykholt í Borgarfirði",
    230: "Reykjanesbær",
    232: "Reykjanesbær",
    233: "Reykjanesbær",
    260: "Reykjanesbær",
    262: "Reykjanesbær",
    101: "Reykjavík",
    102: "Reykjavík",
    103: "Reykjavík",
    104: "Reykjavík",
    105: "Reykjavík",
    107: "Reykjavík",
    108: "Reykjavík",
    109: "Reykjavík",
    110: "Reykjavík",
    111: "Reykjavík",
    112: "Reykjavík",
    113: "Reykjavík",
    116: "Reykjavík",
    121: "Reykjavík",
    123: "Reykjavík",
    124: "Reykjavík",
    125: "Reykjavík",
    127: "Reykjavík",
    128: "Reykjavík",
    129: "Reykjavík",
    130: "Reykjavík",
    132: "Reykjavík",
    161: "Reykjavík",
    162: "Reykjavík",
    245: "Sandgerði",
    246: "Sandgerði",
    550: "Sauðárkrókur",
    551: "Sauðárkrókur",
    800: "Selfoss",
    801: "Selfoss",
    802: "Selfoss",
    803: "Selfoss",
    804: "Selfoss",
    805: "Selfoss",
    806: "Selfoss",
    170: "Seltjarnarnes",
    172: "Seltjarnarnes",
    710: "Seyðisfjörður",
    711: "Seyðisfjörður",
    580: "Siglufjörður",
    581: "Siglufjörður",
    545: "Skagaströnd",
    546: "Skagaströnd",
    356: "Snæfellsbær",
    500: "Staður",
    755: "Stöðvarfjörður",
    756: "Stöðvarfjörður",
    825: "Stokkseyri",
    340: "Stykkishólmur",
    341: "Stykkishólmur",
    342: "Stykkishólmur",
    420: "Súðavík",
    421: "Súðavík",
    430: "Suðureyri",
    431: "Suðureyri",
    460: "Tálknafjörður",
    461: "Tálknafjörður",
    560: "Varmahlíð",
    561: "Varmahlíð",
    900: "Vestmannaeyjar",
    902: "Vestmannaeyjar",
    870: "Vík",
    871: "Vík",
    190: "Vogar",
    191: "Vogar",
    690: "Vopnafjörður",
    691: "Vopnafjörður",
    470: "Þingeyri",
    471: "Þingeyri",
    815: "Þorlákshöfn",
    680: "Þórshöfn",
    681: "Þórshöfn",
}


ADMINISTRATIVE_DIVISIONS: Dict[str, List[str]] = {
    "Seltjarnarnesbær": ["Seltjarnarnes"],
    "Ísafjarðarbær": ["Ísafjörður"],
}

data_path = pkg_resources.resource_filename("stadfangaskra.data", "df.parquet.gzip")

_df = pd.read_parquet(data_path)

df = _df = geopandas.GeoDataFrame(
    _df, geometry=geopandas.points_from_xy(_df.lon, _df.lat), crs=4326
)
df = df.drop(["lat", "lon"], axis=1)

for c in ["municipality_code"]:
    df[c] = pd.Categorical(df[c].astype(pd.Int32Dtype()))


regions = pd.read_parquet(
    pkg_resources.resource_filename("stadfangaskra.data", "regions.parquet")
)

REGION_MAP = {
    k: list(v)
    for (k, v) in regions.groupby("region")["municipality"].unique().to_dict().items()
}

ADMINISTRATIVE_DIVISIONS = {
    k: list(v)
    for (k, v) in regions.groupby("municipality")["name"].unique().to_dict().items()
}
del_keys = []
for k, v in ADMINISTRATIVE_DIVISIONS.items():
    if len(v) == 1 and k == v[0]:
        del_keys.append(k)
for k in del_keys:
    del ADMINISTRATIVE_DIVISIONS[k]
ADMINISTRATIVE_DIVISIONS.update(
    {
        "Seltjarnarnesbær": ["Seltjarnarnes"],
        "Ísafjarðarbær": ["Ísafjörður"],
        "Garðabær": ["Garðabær", "Garðabær (Álftanes)"],
    }
)
