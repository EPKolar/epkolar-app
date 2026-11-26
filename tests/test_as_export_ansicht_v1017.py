"""v3.9.1017 GF "export sauber machen": Der Arbeitsschein-Excel-Export ignorierte die Listenfilter
(Suche, Monteur, Art, SB, Schnellfilter) und nahm immer ALLE Scheine des gewaehlten Status.
Neu: Option "Aktuelle Ansicht (n)" exportiert genau `sorted` (gefiltert + sortiert wie am Bildschirm).
Die bisherigen Optionen bleiben zeichengleich (OFFA-Export-Grenze)."""
import re


def _export_fn(src):
    i = src.index("const exportOffa=(statusFilter)=>{")
    return src[i:src.index("\n  };", i)]


def test_option_aktuelle_ansicht_steht_zuerst(index_html):
    assert '[["ansicht","Aktuelle Ansicht ("+sorted.length+(sorted.length===1?" Schein)":" Scheine)")],["offen_bearb","Offen (alle)"],' in index_html


def test_ansicht_nimmt_die_gefilterte_sortierte_liste(index_html):
    fn = _export_fn(index_html)
    # v1017 GF: weiter die Bildschirmliste, in der Datei aber nach Scheinnummer sortiert
    assert 'const _ansicht=statusFilter==="ansicht";' in fn and '_ansicht?[...sorted].sort(' in fn
    assert 'statusFilter==="ansicht"?"Aktuelle Ansicht":' in fn


def test_bisherige_zweige_unveraendert(index_html):
    fn = _export_fn(index_html)
    alt_src = ('statusFilter==="alle"?arbeitsscheine:arbeitsscheine.filter(a=>statusFilter==="offen_bearb"?'
               'AS_GRP_OFFEN.includes(a.scheinstatus):a.scheinstatus===statusFilter);')  # v1017: toter Zweig "fertig" entfernt (Menue bot ihn nie an)
    assert alt_src in fn
    assert 'genXls("\U0001F4CB OFFA Export — "+lbl+" ("+data.length+")"' in fn, "Titel/OFFA-Weiche unveraendert"
    for k in ("offen_bearb", "aufgenommen", "freigegeben", "in_bearbeitung", "aufgeschoben", "erledigt",
              "abgerechnet", "bar_bezahlt", "storniert", "alle"):
        assert '["%s",' % k in index_html


def test_sorted_ist_die_bildschirmliste(index_html):
    # dieselbe Liste, deren Laenge die Seite als "n von m Arbeitsscheine" zeigt
    assert 'sorted.length, " von "  , _asSicht.length, " Arbeitsscheine"' in index_html  # v1126: _asSicht = Rollen-Sicht der Liste
    i = index_html.index("const sorted=_react.useMemo.call(void 0, ()=>[...filtered].sort(")
    assert i < index_html.index("const exportOffa=(statusFilter)=>{")


def test_umkehrprobe(index_html):
    kaputt = index_html.replace('_ansicht?[...sorted].sort(', "_ansicht?arbeitsscheine.sort(", 1)
    assert '_ansicht?[...sorted].sort(' not in _export_fn(kaputt)
