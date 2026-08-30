# -*- coding: utf-8 -*-
"""v3.9.910 - Ein Rechtefehler sah aus wie eine leere Tabelle.

    if(!r.ok){ if(_isAuthErr(r.status)){ _onAuthFail(r.status); return[]; } ... }

Bei 401 und 403 gaben `_sbGet`, `_sbGetOrder` und `_sbGetUsersSafe` ein leeres
Array zurueck - auf dem **Erfolgspfad**. Fuer rund 150 Aufrufer ist das
ununterscheidbar von *die Tabelle ist leer*, und **kein Auffangzweig kann es je
sehen**: es kommt gar kein Fehler an. Bei 403 tut `_onAuthFail` zudem bewusst
nur ein `console.warn`, weil die Sitzung ja gueltig ist.

Das ist die Wurzel unter einer ganzen Familie von Befunden dieses Tages
(v3.9.898, v3.9.908, v3.9.909): dort wurden ueberall die AUSWIRKUNGEN behandelt
- eine 0, die wie ein Ergebnis aussieht. Hier steht die Quelle.

Es ist zugleich der Fall, der in den Projektnotizen steht: **`select=*` ist kein
vollstaendiger Angriff** - ein 403 aus entzogenen Spaltenrechten galt bei einer
Sicherheitsmessung als *sicher*, weil die Antwort leer aussah.

────────────────────────────────────────────────────────────────────────────
Was dieser Schritt tut - und was ausdruecklich NICHT
────────────────────────────────────────────────────────────────────────────
Der Umbau ist **additiv**: das leere Array traegt jetzt `__rlsFehler` und
`__rlsTab`, und jeder Fall landet in `window.__EP_RLS` - nach dem Vorbild von
`window.__EP_ERRORS`, das es seit langem gibt und das beim Dispo-Absturz die
Zeilennummer geliefert haette.

`.length` bleibt 0, `Array.isArray` bleibt wahr, `.filter`/`.map` arbeiten
unveraendert. **Kein einziger der ~150 Aufrufer aendert sein Verhalten** - das
war die Bedingung, unter der dieser Umbau ueberhaupt vertretbar ist. Ein
`return null` haette hunderte Aufrufer mit `.filter is not a function`
zerrissen.

**Keine Kachel zeigt deshalb schon etwas anderes.** Dieser Schritt macht das
Unsichtbare sichtbar - mehr nicht. Aber ohne ihn laesst sich die Anzeige gar
nicht bauen, denn bis heute konnte niemand am Code erkennen, ob eine leere
Liste ein Ergebnis oder ein Rechtefehler war.

Der Repo-Praezedenzfall existiert bereits: der Kiosk zeigt bei genau diesem
Fall einen Fehlerhinweis statt einer leeren Liste.
"""
from _hilfen import nur_code


def test_das_leere_array_traegt_seinen_grund(index_html):
    code = nur_code(index_html)
    n = code.count("_leerRls.__rlsFehler=r.status")
    assert n == 3, (
        "Erwartet werden DREI markierte Fehlerzweige (_sbGet, _sbGetOrder, "
        "_sbGetUsersSafe) - gefunden: %d. Ein unmarkierter Helfer liefert "
        "weiter eine leere Tabelle, die in Wahrheit ein Rechtefehler ist." % n
    )


def test_kein_helfer_gibt_mehr_ein_nacktes_leeres_array(index_html):
    """Der alte Zweig darf nicht zurueckkehren - auch nicht in einem vierten
    Helfer, den jemand spaeter dazuschreibt."""
    code = nur_code(index_html)
    assert "_onAuthFail(r.status);return[];" not in code, (
        "Ein Abrufhelfer gibt wieder ein unmarkiertes leeres Array zurueck. "
        "Damit sieht ein Rechtefehler erneut aus wie eine leere Tabelle."
    )


def test_es_gibt_eine_merkliste(index_html):
    code = nur_code(index_html)
    assert "window.__EP_RLS" in code, (
        "Die Merkliste fehlt - dann ist ein Rechtefehler weiterhin nirgends "
        "nachlesbar."
    )
    assert "if(window.__EP_RLS.length>50)" in code, (
        "Die Merkliste ist nicht gedeckelt - sie waechst dann unbegrenzt im "
        "Speicher. __EP_ERRORS macht es genauso, mit 50."
    )


def test_die_merkliste_nennt_tabelle_status_und_zeit(index_html):
    i = index_html.find("function _merkeRlsFehler(")
    assert i != -1, "Die Merk-Funktion fehlt"
    fn = index_html[i:i + 620]
    for feld in ("tab:", "status:", "ts:"):
        assert feld in fn, (
            "Der Eintrag nennt %s nicht - ohne Tabelle, Status und Zeit ist "
            "die Liste beim Nachsehen wertlos." % feld
        )


def test_sie_faellt_nie_selbst_um(index_html):
    """Ein Diagnose-Werkzeug, das seinerseits wirft, macht aus einem
    Rechtefehler einen Absturz. Deshalb der Auffangzweig und die
    typeof-Abfrage: die Helfer laufen auch in Node-Tests, wo es kein window
    gibt."""
    i = index_html.find("function _merkeRlsFehler(")
    fn = index_html[i:i + 620]
    assert "try{" in fn and "catch(_mr){}" in fn, (
        "Die Merk-Funktion ist nicht abgesichert."
    )
    assert "typeof window==='undefined'" in fn, (
        "Sie prueft nicht auf window - in Node-Tests wuerde sie werfen."
    )


def test_die_aufrufer_aendern_ihr_verhalten_nicht(index_html):
    """DIE WICHTIGSTE GEGENPROBE. Der Umbau ist nur vertretbar, WEIL er
    additiv ist: es wird weiterhin ein echtes Array zurueckgegeben, kein null
    und kein Objekt. Ein `return null` haette hunderte Aufrufer zerrissen."""
    code = nur_code(index_html)
    assert "var _leerRls=[];" in code, (
        "Es wird kein echtes Array mehr zurueckgegeben - dann brechen die "
        "Aufrufer mit '.filter is not a function'."
    )
    assert "return _leerRls;}" in code, (
        "Der Fehlerzweig gibt nicht mehr das markierte Array zurueck."
    )


def test_403_loest_weiterhin_keine_neuanmeldung_aus(index_html):
    """Gegenprobe zur Abgrenzung: bei 403 ist die Sitzung GUELTIG, es fehlen
    nur Rechte. Ein Toast 'Sitzung abgelaufen' waere dort eine Falschaussage -
    diese Version durfte daran nichts aendern."""
    i = index_html.find("function _onAuthFail(status){")
    assert i != -1
    fn = index_html[i:i + 260]
    assert "if(status===403)" in fn and "return;" in fn, (
        "Der 403-Sonderweg in _onAuthFail hat sich veraendert - dort darf "
        "keine Neuanmeldung verlangt werden."
    )


# ══ Umkehrprobe ═════════════════════════════════════════════════════════════

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    z = index_html.replace("_merkeRlsFehler(_tabRls,r.status);", "", 1)
    assert z != index_html, "Rueckbau griff nicht"
    assert nur_code(z).count("_merkeRlsFehler(_tabRls,r.status);") == 2, (
        "Umkehrprobe: der Zaehl-Riegel wuerde einen fehlenden Helfer nicht "
        "bemerken"
    )

    z2 = index_html.replace("var _leerRls=[];", "var _leerRls=null;", 1)
    assert z2 != index_html, "Rueckbau 2 griff nicht"
    assert "var _leerRls=[];" in nur_code(z2), (
        "Umkehrprobe: es gibt nur noch eine Rueckgabestelle - dann misst der "
        "Additiv-Riegel zu wenig"
    )
