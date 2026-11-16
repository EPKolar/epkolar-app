# -*- coding: utf-8 -*-
"""Schnellbuchung "Wie letzte Woche" (Zeiterfassung, Auftrag GF 16.11.2026).

Gemessen wird:
  * die REINE Verschiebe-/Filterlogik `_wieLetzteWoche` am echten Code per node
    (aus index.html geschnitten, mit den echten Zeit-Helfern): +7 Tage,
    Jahreswechsel KW 53 -> KW 1, Feiertag, Abwesenheit, schon gebuchter Tag,
    Dublette (DB-Unique worker_id,date,von,bis nach 5-Minuten-Raster),
    Arbeitsschein-Buchung, Gehen <= Kommen, inaktives Projekt, Sommerzeit;
  * der Riegel, dass die Uebernahme NUR ueber addEntry schreibt (kein eigener
    Schreibweg) - mit Umkehrprobe, dass der Sucher einen eigenen Weg saehe;
  * Umkehrproben an der Logik: ohne die Belegt-/Dubletten-Pruefung werden die
    Faelle rot.
"""
import json
import re

from conftest import run_node_snippet, _extract_fn

NAMEN = ("_zeitParse", "_zeitFmt", "_zeitRundVon", "_zeitRundBis",
         "_wrapHrs", "_zeitEffektiveStunden", "_zeitDauerUngueltig",
         "_wieLetzteWoche")


def _bausatz(index_html, ersetzen=None):
    teile = []
    for n in NAMEN:
        f = _extract_fn(index_html, n)
        assert f, "Funktion nicht gefunden: " + n
        teile.append(f)
    code = "var ZEIT_RASTER_MIN=5;\n" + "\n".join(teile) + "\n"
    if ersetzen:
        alt, neu = ersetzen
        assert alt in code, "Umkehrprobe greift ins Leere: " + alt
        code = code.replace(alt, neu)
    return code


def _lauf(node_exe, code, faelle):
    snippet = code + (
        "const F=" + json.dumps(faelle) + ";"
        "process.stdout.write(JSON.stringify(F.map(f=>_wieLetzteWoche("
        "f.e,f.mo,f.ft||[],f.ab||{},f.best||[],"
        "f.inaktiv?{projektAktiv:p=>f.inaktiv.indexOf(p)<0}:undefined))));"
    )
    return json.loads(run_node_snippet(node_exe, snippet))


def _e(datum, von="07:00", bis="16:00", pause=1, **kw):
    d = {"id": "x" + datum + von, "date": datum, "von": von, "bis": bis,
         "pause": pause, "hours": 8, "project_id": "p1", "taetigkeit": "Montage",
         "gewerk": "elektro", "bemerkung": "alte Bemerkung", "arbeitsschein_id": ""}
    d.update(kw)
    return d


FAELLE = [
    # 0 normal KW46 -> KW47/2026
    {"mo": "2026-11-16", "e": [
        _e("2026-11-09"),
        _e("2026-11-13", "07:00", "12:00", 0, project_id="", taetigkeit="Lager", gewerk="hkls"),
        _e("2026-11-02"),  # vorvorige Woche -> ignoriert
        _e("2026-11-16"),  # Zielwoche selbst -> ignoriert
    ]},
    # 1 Jahreswechsel KW53/2026 -> KW1/2027, 06.01. Feiertag
    {"mo": "2027-01-04", "ft": ["2027-01-06"], "e": [
        _e("2026-12-28"), _e("2026-12-30"), _e("2026-12-31"), _e("2027-01-01"),
    ]},
    # 2 in KW53 hinein (KW52 -> KW53/2026)
    {"mo": "2026-12-28", "e": [_e("2026-12-21"), _e("2026-12-27", "08:00", "12:00", 0)]},
    # 3 bestehende Eintraege, Abwesenheit, Dublette (auch nach Raster), Arbeitsschein, Nacht, inaktiv
    {"mo": "2026-11-16", "inaktiv": ["p9"],
     "ab": {"2026-11-18": "Urlaub"},
     "best": [{"date": "2026-11-17", "von": "07:00", "bis": "15:00"}],
     "e": [
         _e("2026-11-09"),
         _e("2026-11-09", "07:02", "16:00"),          # rundet auf 07:05 -> KEINE Dublette
         _e("2026-11-09", "06:58", "16:00"),          # Kommen rundet AUF 07:00 -> Dublette der ersten
         _e("2026-11-10"),                            # Di belegt
         _e("2026-11-11"),                            # Mi Urlaub
         _e("2026-11-12", arbeitsschein_id="as1"),    # Arbeitsschein
         _e("2026-11-13", "16:00", "07:00"),          # Nacht -> ungueltig
         _e("2026-11-13", "06:00", "07:00", 0, project_id="p9"),  # inaktiv
         _e("2026-11-14", "07:00", "11:00", 0, project_id="", taetigkeit=""),  # ohne Bezeichnung
     ]},
    # 4 Sommerzeit-Ende 25.10.2026 liegt in der Vorwoche
    {"mo": "2026-10-26", "e": [_e("2026-10-19"), _e("2026-10-25", "08:00", "10:00", 0)]},
]


def test_verschieben_und_filtern_am_echten_code(node_exe, index_html):
    r = _lauf(node_exe, _bausatz(index_html), FAELLE)

    a = r[0]
    assert [z["datum"] for z in a] == ["2026-11-16", "2026-11-20"], a
    assert all(z["ok"] for z in a)
    assert a[0]["hours"] == 8 and a[0]["typ"] == "projekt" and a[0]["project_id"] == "p1"
    assert a[0]["taetigkeit"] == "Montage" and a[0]["pause"] == 1
    assert a[1]["typ"] == "frei" and a[1]["taetigkeit"] == "Lager" and a[1]["hours"] == 5
    assert a[1]["gewerk"] == "hkls"
    assert all(z["bemerkung"] == "" and z["arbeitsschein_id"] == "" for z in a), \
        "Bemerkung oder Arbeitsschein-Verknuepfung wurde uebernommen"

    b = r[1]
    assert [(z["quelle"], z["datum"]) for z in b] == [
        ("2026-12-28", "2027-01-04"), ("2026-12-30", "2027-01-06"),
        ("2026-12-31", "2027-01-07"), ("2027-01-01", "2027-01-08")], b
    assert [z["grund"] for z in b] == ["", "Feiertag", "", ""]

    c = r[2]
    assert [z["datum"] for z in c] == ["2026-12-28", "2027-01-03"], c
    assert all(z["ok"] for z in c)

    d = r[3]
    gruende = [(z["datum"], z["von"], z["grund"]) for z in d]
    assert gruende == [
        ("2026-11-16", "06:58", ""),
        ("2026-11-16", "07:00", "doppelt (gleiche Zeit)"),
        ("2026-11-16", "07:02", ""),
        ("2026-11-17", "07:00", "Tag schon gebucht"),
        ("2026-11-18", "07:00", "Urlaub"),
        ("2026-11-19", "07:00", "Arbeitsschein-Buchung"),
        ("2026-11-20", "06:00", "Projekt nicht aktiv"),
        ("2026-11-20", "16:00", "Zeit ungültig"),
        ("2026-11-21", "07:00", "ohne Bezeichnung"),
    ], gruende
    assert [z["ok"] for z in d] == [True, False, True] + [False] * 6
    assert d[5]["typ"] == "schein" and d[5]["arbeitsschein_id"] == ""

    e = r[4]
    assert [z["datum"] for z in e] == ["2026-10-26", "2026-11-01"], e


def test_umkehrprobe_ohne_belegt_pruefung_wird_der_tag_doppelt_gebucht(node_exe, index_html):
    code = _bausatz(index_html, ("else if(belegt[ziel])grund='Tag schon gebucht';", ""))
    d = _lauf(node_exe, code, [FAELLE[3]])[0]
    di = [z for z in d if z["datum"] == "2026-11-17"][0]
    assert di["ok"] is True, "Umkehrprobe: ohne Pruefung muesste der belegte Tag durchgehen"


def test_umkehrprobe_ohne_dubletten_pruefung_geht_die_dublette_durch(node_exe, index_html):
    code = _bausatz(index_html, ("else if(von&&bis&&zeiten[_key(ziel,von,bis)])grund='doppelt (gleiche Zeit)';", ""))
    d = _lauf(node_exe, code, [FAELLE[3]])[0]
    assert [z["ok"] for z in d][:3] == [True, True, True], \
        "Umkehrprobe: ohne Pruefung muesste die Dublette durchgehen"


# ── Riegel: es gibt keinen eigenen Schreibweg ──

SCHREIB = re.compile(r"SQ\.push|_sbPost|_sbPatch|_sbPut|_sbDelete|fetch\(|API\.(add|create|save|update|post|put)", re.I)


def _wlw_block(index_html):
    a = index_html.index("const _wlwAbs=")
    b = index_html.index("// Totals", a)
    return index_html[a:b]


def test_uebernahme_schreibt_nur_ueber_addEntry(index_html):
    blk = _wlw_block(index_html)
    assert "ok=await addEntry();" in blk, "Die Uebernahme ruft addEntry nicht mehr auf"
    assert not SCHREIB.search(blk), "Eigener Schreibweg in der Uebernahme: " + SCHREIB.search(blk).group(0)
    fn = _extract_fn(index_html, "_wieLetzteWoche")
    assert not SCHREIB.search(fn), "Die reine Funktion schreibt"


def test_umkehrprobe_der_sucher_saehe_einen_eigenen_schreibweg():
    attrappe = 'const _wlwUebernehmen=async()=>{SQ.push({url:"/api/entries",method:"POST",body:{}});};'
    assert SCHREIB.search(attrappe)


def test_addEntry_liest_die_zeile_und_meldet_erfolg(index_html):
    fn = _extract_fn(index_html, "addEntry", r"const\s+addEntry\s*=\s*async\s*\(")
    assert fn
    assert "const _wl=_wlwRef.current;" in fn
    assert "=_wl||_zeForm();" in fn
    i_post = fn.index('SQ.push({url:"/api/entries",method:"POST"')
    i_ret = fn.index("if(_wl)return true;")
    assert i_post < i_ret, "Erfolg wird gemeldet, bevor die SyncQueue den Eintrag hat"
    # Rundung, Nachtarbeit-Abweisung und Plausi bleiben im gemeinsamen Weg
    assert "_zeitRundVon(addVon)" in fn and "_zeitDauerUngueltig(_rVon,_rBis)" in fn
    assert "_zeTagPlausi(_exTag,h,_rVon,_rBis)" in fn
    assert "gewerk:_gw" in fn


# ── UI-Regeln am neuen Block ──

def test_ui_regeln(index_html):
    blk = _wlw_block(index_html)
    knopf = index_html[index_html.index("'data-wlw-knopf'") - 200:index_html.index("'data-wlw-knopf'") + 400]
    assert '_ik("kopie",16),"Wie letzte Woche"' in knopf
    for teil in (blk, knopf):
        assert not re.search(r"[\U0001F300-\U0001FAFF☀-➿]", teil), "Emoji im neuen Block"
        assert not re.search(r"fontSize:\s*\d", teil), "nackte Schriftgroesse statt UI.*-Token"
    assert "minHeight:44" in blk, "Zeilen ohne 44-px-Ziel"
    assert "accentColor:UI.marke" in blk
