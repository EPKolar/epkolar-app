"""v3.9.687 Flotte Phase F4 — Auswertung (Tageskilometer, Geschwindigkeit, Filter/Favoriten).

Baut ausschliesslich auf Vorhandenem: Segmente aus _fzSegmente (v3.9.679), Rohpunkte aus
fz_positions, Charts aus der bestehenden SVG-Engine (SvgBar/SvgLine). Keine neue Bibliothek,
keine neue Datenquelle.

fz_positions ist weiterhin leer (Tracker nicht bestellt) — alles gegen Mock-Daten getestet.
"""
import json

from conftest import run_node_snippet, _extract_fn


def _harness(index_html, *names):
    teile = []
    for n in names:
        fn = _extract_fn(index_html, n)
        assert fn, f"{n} nicht gefunden"
        teile.append(fn)
    return "\n".join(teile) + "\n"


def _eval(node_exe, index_html, ausdruck, *names):
    snip = _harness(index_html, *names) + f"process.stdout.write(JSON.stringify({ausdruck}));"
    return json.loads(run_node_snippet(node_exe, snip))


def _ms(iso):
    """Lokale Zeit als ms — die Engine liefert beginn/ende auch als ms."""
    return f"new Date('{iso}').getTime()"


# ── Tageskilometer ──────────────────────────────────────────────────────────

def test_tageskm_gruppiert_und_summiert(node_exe, index_html):
    segs = (
        "[{beginn:" + _ms("2026-07-13T07:00:00") + ",km:12.5,dauerMin:20},"
        "{beginn:" + _ms("2026-07-13T15:00:00") + ",km:7.5,dauerMin:15},"
        "{beginn:" + _ms("2026-07-14T08:00:00") + ",km:30.0,dauerMin:45}]"
    )
    r = _eval(node_exe, index_html, f"_fzTagesKm({segs})", "_fzTagesKm")
    assert len(r) == 2
    assert r[0]["tag"] == "2026-07-13"
    assert r[0]["km"] == 20.0
    assert r[0]["fahrten"] == 2
    assert r[0]["dauerMin"] == 35
    assert r[1]["tag"] == "2026-07-14"
    assert r[1]["km"] == 30.0


def test_tageskm_aufsteigend_sortiert(node_exe, index_html):
    segs = (
        "[{beginn:" + _ms("2026-07-16T07:00:00") + ",km:5},"
        "{beginn:" + _ms("2026-07-13T07:00:00") + ",km:5},"
        "{beginn:" + _ms("2026-07-15T07:00:00") + ",km:5}]"
    )
    r = _eval(node_exe, index_html, f"_fzTagesKm({segs})", "_fzTagesKm")
    assert [x["tag"] for x in r] == ["2026-07-13", "2026-07-15", "2026-07-16"]


def test_tageskm_abendfahrt_bleibt_am_richtigen_tag(node_exe, index_html):
    """Der Tagesschluessel wird LOKAL gebildet.

    Mit toISOString() waere eine Fahrt um 23:30 Ortszeit im Sommer (UTC+2) auf den Vortag
    gerutscht — die Tageskilometer haetten stillschweigend im falschen Balken gelandet.
    """
    segs = "[{beginn:" + _ms("2026-07-13T23:30:00") + ",km:9}]"
    r = _eval(node_exe, index_html, f"_fzTagesKm({segs})", "_fzTagesKm")
    assert r[0]["tag"] == "2026-07-13"


def test_tageskm_robust(node_exe, index_html):
    segs = (
        "[null,{beginn:NaN,km:5},{beginn:" + _ms("2026-07-13T07:00:00") + ",km:'abc'},"
        "{beginn:" + _ms("2026-07-13T09:00:00") + ",km:-3}]"
    )
    r = _eval(node_exe, index_html, f"_fzTagesKm({segs})", "_fzTagesKm")
    # Kaputte ts fliegen raus; die zwei gueltigen Tage-Eintraege zaehlen als Fahrten, aber
    # Muell-km gehen NICHT in die Summe.
    assert len(r) == 1
    assert r[0]["km"] == 0
    assert r[0]["fahrten"] == 2


def test_tageskm_leer(node_exe, index_html):
    for a in ("_fzTagesKm([])", "_fzTagesKm(null)"):
        assert _eval(node_exe, index_html, a, "_fzTagesKm") == []


# ── Geschwindigkeit ─────────────────────────────────────────────────────────

SEG = "{beginn:" + _ms("2026-07-13T07:00:00") + ",ende:" + _ms("2026-07-13T07:30:00") + "}"


def test_speed_nur_punkte_der_fahrt(node_exe, index_html):
    pos = (
        "[{ts:'2026-07-13T06:50:00',speed:50},"   # vor der Fahrt
        "{ts:'2026-07-13T07:05:00',speed:60},"
        "{ts:'2026-07-13T07:20:00',speed:80},"
        "{ts:'2026-07-13T07:45:00',speed:70}]"    # nach der Fahrt
    )
    r = _eval(node_exe, index_html, f"_fzSpeedReihe({pos},{SEG})", "_fzSpeedReihe")
    assert [x["v"] for x in r] == [60, 80]


def test_speed_null_ist_kein_stillstand(node_exe, index_html):
    """JS-Falle: Number(null) ist 0. Ein Punkt OHNE Geschwindigkeit wuerde sonst als 0 km/h in die
    Kurve gezeichnet — die Fahrt saehe aus, als waere sie staendig stehengeblieben."""
    pos = (
        "[{ts:'2026-07-13T07:05:00',speed:null},"
        "{ts:'2026-07-13T07:10:00',speed:''},"
        "{ts:'2026-07-13T07:15:00',speed:'abc'},"
        "{ts:'2026-07-13T07:20:00',speed:55}]"
    )
    r = _eval(node_exe, index_html, f"_fzSpeedReihe({pos},{SEG})", "_fzSpeedReihe")
    assert len(r) == 1, "nur der eine echte Messwert darf durchkommen"
    assert r[0]["v"] == 55


def test_speed_echte_null_zaehlt_schon(node_exe, index_html):
    """speed:0 ist eine ECHTE Messung (Fahrzeug steht an der Ampel) — die gehoert in die Kurve."""
    pos = "[{ts:'2026-07-13T07:05:00',speed:0},{ts:'2026-07-13T07:10:00',speed:40}]"
    r = _eval(node_exe, index_html, f"_fzSpeedReihe({pos},{SEG})", "_fzSpeedReihe")
    assert [x["v"] for x in r] == [0, 40]


def test_speed_unsortiert_wird_sortiert(node_exe, index_html):
    pos = "[{ts:'2026-07-13T07:20:00',speed:80},{ts:'2026-07-13T07:05:00',speed:60}]"
    r = _eval(node_exe, index_html, f"_fzSpeedReihe({pos},{SEG})", "_fzSpeedReihe")
    assert [x["v"] for x in r] == [60, 80]


def test_speed_ohne_fahrt(node_exe, index_html):
    pos = "[{ts:'2026-07-13T07:05:00',speed:60}]"
    assert _eval(node_exe, index_html, f"_fzSpeedReihe({pos},null)", "_fzSpeedReihe") == []


def test_speed_kennzahlen(node_exe, index_html):
    r = _eval(
        node_exe, index_html,
        "_fzSpeedKennzahlen([{t:1,v:60},{t:2,v:80},{t:3,v:40}])",
        "_fzSpeedKennzahlen",
    )
    assert r == {"max": 80, "schnitt": 60, "punkte": 3}


def test_speed_kennzahlen_leer(node_exe, index_html):
    for a in ("_fzSpeedKennzahlen([])", "_fzSpeedKennzahlen(null)"):
        assert _eval(node_exe, index_html, a, "_fzSpeedKennzahlen") == {
            "max": 0, "schnitt": 0, "punkte": 0,
        }


# ── Struktur-Guards ─────────────────────────────────────────────────────────

def test_bestehende_chart_engine(index_html):
    # Keine neue Bibliothek — SvgBar/SvgLine sind seit v3.9.366 da.
    assert "h(SvgBar,{data:balken,color:'#0ea5e9'" in index_html
    assert "h(SvgLine,{data:speedReihe.map(" in index_html


def test_geschwindigkeit_haengt_an_einer_fahrt(index_html):
    # Eine Kurve ueber den ganzen Zeitraum waere Kaffeesatz (Naechte, Wochenenden, Luecken).
    assert "const [analyseSeg,setAnalyseSeg]=_react.useState.call(void 0, null);" in index_html
    assert "const speedReihe=_fzSpeedReihe(pos,analyseSeg);" in index_html


def test_leerzustand_analyse(index_html):
    # v3.9.690: Der Leer-Zustand haengt jetzt am Panel-Render (eine Stelle statt zweier).
    assert "Keine Fahrten im gewählten Zeitraum" in index_html
    assert "der Tracker hat sie nicht mitgeliefert" in index_html


def test_filter_und_favoriten(index_html):
    assert "const [fzFilter,setFzFilter]=_react.useState.call(void 0, '');" in index_html
    assert "localStorage.setItem('epk_flotte_fav'" in index_html
    # Favoriten stehen oben.
    # v3.9.689: Sortierung liegt jetzt in der pure Funktion _fzFleetSort.
    assert "var fa=fav(a.f.id)?0:1, fb=fav(b.f.id)?0:1;" in index_html
    # Fahrer ist mitsuchbar — _fahrerName nimmt das FAHRZEUG, nicht die id.
    assert "String(_fahrerName(f)||'')" in index_html


def test_filter_faelscht_die_zaehler_nicht(index_html):
    """Die Kopfzeile zaehlt den ganzen Fuhrpark. Wuerde sie mitgefiltert, suggerierte ein Filter,
    es gaebe nur noch drei Fahrzeuge — und jemand haelt das fuer den Bestand."""
    assert "var fleetView=_fq?fleet.filter(" in index_html
    # v3.9.689: Zaehler vierstufig + "ohne Tracker" — aber weiterhin ueber den GANZEN Fuhrpark.
    assert "_nAkt+' aktiv · '+_nInakt+' inaktiv · '+_nWart+' wartet'" in index_html
    # v3.9.690: die Liste rendert getrennt nach mit/ohne Tracker (Gruppe am Ende).
    assert "_mitTracker.map(_fleetZeile)" in index_html
    assert "const _mitTracker=fleetView.filter(function(r){return r.hatTracker;});" in index_html
