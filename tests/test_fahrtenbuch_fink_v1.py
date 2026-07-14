"""v3.9.690 — Fahrtenbuch Fink-Parität: Zeiträume, Summen, fahrzeugübergreifender Merge.

Referenz ist FinkZeit FZE „Fahrtenbuch mit Karte". Getestet wird die pure Datenschicht;
das Layout selbst ist render-only.
"""
import json

from conftest import run_node_snippet, _extract_fn

DEPS = "const TIME_SECOND=1000;const TIME_MINUTE=60*TIME_SECOND;const TIME_HOUR=60*TIME_MINUTE;const TIME_DAY=24*TIME_HOUR;"


def _harness(index_html, *names):
    teile = [DEPS]
    for n in names:
        fn = _extract_fn(index_html, n)
        assert fn, f"{n} nicht gefunden"
        teile.append(fn)
    return "\n".join(teile) + "\n"


def _eval(node_exe, index_html, ausdruck, *names):
    snip = _harness(index_html, *names) + f"process.stdout.write(JSON.stringify({ausdruck}));"
    return json.loads(run_node_snippet(node_exe, snip))


def _now(iso):
    return f"new Date('{iso}').getTime()"


# ── Zeitraum-Presets ────────────────────────────────────────────────────────

def test_preset_monat(node_exe, index_html):
    r = _eval(node_exe, index_html, f"_fbZeitraum('monat',{_now('2026-07-14T10:00:00')})", "_fbZeitraum")
    assert r == {"von": "2026-07-01", "bis": "2026-07-31"}


def test_preset_vormonat(node_exe, index_html):
    r = _eval(node_exe, index_html, f"_fbZeitraum('vormonat',{_now('2026-07-14T10:00:00')})", "_fbZeitraum")
    assert r == {"von": "2026-06-01", "bis": "2026-06-30"}


def test_preset_vormonat_ueber_jahresgrenze(node_exe, index_html):
    """Im Januar muss der Vormonat der Dezember des VORJAHRS sein."""
    r = _eval(node_exe, index_html, f"_fbZeitraum('vormonat',{_now('2026-01-09T10:00:00')})", "_fbZeitraum")
    assert r == {"von": "2025-12-01", "bis": "2025-12-31"}


def test_preset_monat_februar_schaltjahr(node_exe, index_html):
    r = _eval(node_exe, index_html, f"_fbZeitraum('monat',{_now('2028-02-10T10:00:00')})", "_fbZeitraum")
    assert r["bis"] == "2028-02-29", "2028 ist ein Schaltjahr"


def test_preset_heute(node_exe, index_html):
    r = _eval(node_exe, index_html, f"_fbZeitraum('heute',{_now('2026-07-14T23:30:00')})", "_fbZeitraum")
    assert r == {"von": "2026-07-14", "bis": "2026-07-14"}


def test_preset_woche_montag_bis_sonntag(node_exe, index_html):
    """14.07.2026 ist ein Dienstag -> Woche = Mo 13.07. bis So 19.07."""
    r = _eval(node_exe, index_html, f"_fbZeitraum('woche',{_now('2026-07-14T10:00:00')})", "_fbZeitraum")
    assert r == {"von": "2026-07-13", "bis": "2026-07-19"}


def test_preset_woche_sonntag_gehoert_zur_laufenden_woche(node_exe, index_html):
    """Sonntag ist Tag 7, nicht Tag 1 — sonst springt die Woche am Sonntag eine zu weit."""
    r = _eval(node_exe, index_html, f"_fbZeitraum('woche',{_now('2026-07-19T10:00:00')})", "_fbZeitraum")
    assert r == {"von": "2026-07-13", "bis": "2026-07-19"}


# ── Summen ──────────────────────────────────────────────────────────────────

def test_summen(node_exe, index_html):
    f = "[{km:12.5,dauerMin:20},{km:7.25,dauerMin:15},{km:30,dauerMin:45}]"
    r = _eval(node_exe, index_html, f"_fbSummen({f})", "_fbSummen")
    assert r == {"anzahl": 3, "km": 49.75, "dauerMin": 80}


def test_summen_leer(node_exe, index_html):
    for a in ("_fbSummen([])", "_fbSummen(null)"):
        assert _eval(node_exe, index_html, a, "_fbSummen") == {"anzahl": 0, "km": 0, "dauerMin": 0}


def test_summen_ignorieren_muell(node_exe, index_html):
    """Kaputte km duerfen die Summe nicht verfaelschen — sie ist die Zahl, die im Export steht."""
    f = "[null,{km:'abc',dauerMin:10},{km:-5,dauerMin:-3},{km:10,dauerMin:20}]"
    r = _eval(node_exe, index_html, f"_fbSummen({f})", "_fbSummen")
    assert r["km"] == 10
    assert r["dauerMin"] == 30
    assert r["anzahl"] == 3, "gezaehlt werden alle echten Zeilen, auch die mit Muell-km"


# ── Merge über alle Fahrzeuge ───────────────────────────────────────────────

def test_merge_neueste_fahrt_zuerst(node_exe, index_html):
    js = (
        "_fbMerge({a:[{beginn:300,km:1},{beginn:100,km:1}],"
        "b:[{beginn:200,km:1}]}).map(function(x){return [x.fahrzeug_id,x.beginn];})"
    )
    r = _eval(node_exe, index_html, js, "_fbMerge")
    assert r == [["a", 300], ["b", 200], ["a", 100]]


def test_merge_haengt_fahrzeug_id_an(node_exe, index_html):
    """Ohne fahrzeug_id an der Fahrt liesse sich in der Alle-Ansicht nicht sagen, WESSEN Fahrt
    das ist — und der Fahrten-Schluessel (Fahrzeug+Beginn) waere nicht bildbar."""
    r = _eval(node_exe, index_html, "_fbMerge({tu1:[{beginn:1,km:2}]})", "_fbMerge")
    assert r[0]["fahrzeug_id"] == "tu1"


def test_merge_leer(node_exe, index_html):
    for a in ("_fbMerge({})", "_fbMerge(null)"):
        assert _eval(node_exe, index_html, a, "_fbMerge") == []


# ── Tacho nur wenn vorhanden ────────────────────────────────────────────────

def test_tacho_spalte_nur_bei_werten(node_exe, index_html):
    """Bis gps_ingest einen Odometer liefert, ist das immer false — dann bleibt die Spalte weg,
    statt als dauerhaft leere Saeule Platz zu fressen."""
    ohne = _eval(node_exe, index_html, "_fbHatTacho([{km:1},{km:2,tachoVon:null}])", "_fbHatTacho")
    mit = _eval(node_exe, index_html, "_fbHatTacho([{km:1},{km:2,tachoBis:123456}])", "_fbHatTacho")
    assert ohne is False
    assert mit is True


# ── Status-seit im Fink-Format ──────────────────────────────────────────────

def test_stamp_heute_nur_uhrzeit(node_exe, index_html):
    r = _eval(
        node_exe, index_html,
        f"_fzStampFink({_now('2026-07-14T08:42:00+02:00')},{_now('2026-07-14T18:00:00+02:00')})",
        "_fzStampFink",
    )
    assert r == "08:42", f"heute -> nur HH:MM, war {r!r}"


def test_stamp_aelter_mit_datum(node_exe, index_html):
    r = _eval(
        node_exe, index_html,
        f"_fzStampFink({_now('2026-07-13T08:42:00+02:00')},{_now('2026-07-14T18:00:00+02:00')})",
        "_fzStampFink",
    )
    assert "08:42" in r
    assert "13" in r and "07" in r, f"aelter -> mit Datum, war {r!r}"


def test_stamp_mitternachtsgrenze(node_exe, index_html):
    """23:58 gestern ist NICHT heute — auch wenn es nur zwei Minuten her ist.

    Der Vergleich laeuft ueber den KALENDERTAG in Europe/Vienna, nicht ueber eine Zeitdifferenz.
    """
    r = _eval(
        node_exe, index_html,
        f"_fzStampFink({_now('2026-07-13T23:58:00+02:00')},{_now('2026-07-14T00:01:00+02:00')})",
        "_fzStampFink",
    )
    assert "23:58" in r
    assert len(r) > 5, f"muss das Datum tragen, war {r!r}"


def test_stamp_leer(node_exe, index_html):
    for a in ("_fzStampFink(null,1)", "_fzStampFink(NaN,1)", "_fzStampFink(undefined,1)"):
        assert _eval(node_exe, index_html, a, "_fzStampFink") == ""


# ── Struktur-Guards ─────────────────────────────────────────────────────────

def test_alle_fahrzeuge_ein_request(index_html):
    """21 Fahrzeuge duerfen nicht 21 Requests ausloesen."""
    assert "async function _fzFetchRangeAlle(fids,fromIso,toIso){" in index_html
    assert '"&fahrzeug_id=in."+encodeURIComponent(inList)' in index_html
    assert "async function _fzFetchFahrtenAlle(fids,fromIso,toIso){" in index_html


def test_schluessel_ist_fahrzeug_plus_beginn(index_html):
    """In der Alle-Ansicht koennen zwei Fahrzeuge zur selben Sekunde losfahren — ein reiner
    Zeitschluessel wuerde die eine Fahrt still mit der anderen ueberschreiben."""
    assert (
        "const _fk=function(x){return String((x&&x.fahrzeug_id)||fid||'')+'_'+String(x?x.beginn:'');};"
        in index_html
    )


def test_pdf_export(index_html):
    assert "const exportFahrtenPdf=function(){" in index_html
    assert "orientation:'landscape',unit:'mm',format:'a4'" in index_html


def test_summenzeile_sichtbar(index_html):
    assert "'Summe: '+_n(sumKm,1)+' km · '+_fzDauerFmt(sumMin)+' h · '+summe.anzahl" in index_html


def test_drei_panels_ein_frame(index_html):
    """Kein Overlay, kein Toggle — alles gleichzeitig sichtbar (Fink)."""
    assert "const _panelListe=h('div'," in index_html
    assert "const _panelKarte=h('div'," in index_html
    assert "const _panelBuch=h(FahrtenbuchView,{" in index_html


def test_tabs(index_html):
    assert "_tabBtn('fahrten','Fahrten')" in index_html
    assert "_tabBtn('km','Tageskilometer')" in index_html
    assert "_tabBtn('speed','Geschwindigkeit')" in index_html
