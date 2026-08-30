"""v3.9.112 — Bug-Hunt Welle 2c: Übernacht-von/bis + Logout-Token-Fenster."""
import re
import json
from conftest import run_node_snippet, _extract_fn
from _hilfen import nur_code

# Der lokale _extract_fn-Klon ist entfernt (13.07.2026): sein Brace-Zaehler nahm die erste
# `{` nach dem Funktionsnamen als Body-Start und griff damit bei destrukturierten Parametern
# (function X({a,b}){...}) die Parameterliste statt des Rumpfs. Hier war das folgenlos, weil
# _wrapHrs/_sbAuthLogout normale Parameter haben — aber latent kaputt. Master ist der
# gefixte Extraktor in conftest.py (Commit 6f3f12b).


def test_wraphrs_behavior(node_exe, index_html):
    fn = _extract_fn(index_html, "_wrapHrs")
    assert fn, "_wrapHrs nicht gefunden"
    snippet = fn + (
        "process.stdout.write(JSON.stringify(["
        "_wrapHrs('08:00','16:30'),"   # same-day 8.5h
        "_wrapHrs('22:00','06:00'),"   # overnight 8h
        "_wrapHrs('07:00','07:00'),"   # 0
        "_wrapHrs('06:00','14:30')"    # 8.5
        "]));"
    )
    res = json.loads(run_node_snippet(node_exe, snippet))
    assert res == [8.5, 8.0, 0.0, 8.5], f"_wrapHrs falsch: {res}"


# ---------------------------------------------------------------------------
# BENANNTE STELLEN STATT GESAMTZAHL (v3.9.922)
#
# Vorher stand hier `index_html.count("_wrapHrs(") == 14` - eine Festzahl ueber
# die ganze Datei, ROH gezaehlt. Zwei Loecher, beide nachgemessen:
#
# 1. EINE FESTZAHL BLEIBT BEIM TAUSCH GRUEN. Wandert die Neuberechnung aus dem
#    "Von"-Feld ins "Bis"-Feld, bleibt die Summe 14 - obwohl ein Eingabefeld
#    seine Neuberechnung verloren hat. Genau das stellt die Umkehrprobe unten
#    nach: alte Zahl gruen, neuer Riegel rot.
# 2. ROH GEZAEHLT ZAEHLT KOMMENTARE MIT. Wer den Ausbau einer Stelle daneben
#    erklaert und dabei `_wrapHrs(` schreibt, faerbt den Riegel falsch rot.
#    Deshalb `nur_code()`. Gemessen 30.08.2026: roh 14, kommentarblind 14 -
#    die Umstellung aendert heute NICHTS am Ergebnis.
#
# Und die eigentliche Eigenschaft ("hier wird nicht von Hand gerechnet") hing
# nie an der Zahl: eine handgeschriebene 15. Rechnung SENKT sie nicht. Sie
# haengt daran, dass die Uhrzeit-Arithmetik NUR in `_wrapHrs` steht - das ist
# `_ZEITMATHE` unten, ein "nirgendwo sonst" statt eines Zaehlers.
# ---------------------------------------------------------------------------

# Die zwei Erfassungskomponenten. Beide haben denselben Aufbau: ein
# Speichern-/Neuberechnungs-Kopf und danach die drei Eingabefelder.
_KOMPONENTEN = ("VZeit", "ZeiterfassungView")
# Der Helfer, der Anzeige und Speichern aus EINER Quelle speist (v3.9.885) -
# er BENUTZT _wrapHrs, ist also kein Verstoss, sondern der Beleg dafuer.
_HELFER = "_zeitEffektiveStunden"

# Geschnitten wird an den Feld-Ankern; jeder kommt in seiner Komponente GENAU
# EINMAL vor (gemessen v3.9.922) - der Schnitt ist damit eindeutig. Es sind
# Rollen-Anker ("das Von-Feld"), keine abgeschriebene Rechen-Schreibweise.
_FELDANKER = ("value:addVon", "value:addBis", "value:addPause")
# Rolle -> erwartete Zahl von _wrapHrs-Aufrufen, in Quelltext-Reihenfolge.
_ROLLEN = (
    ("Neuberechnung im Speichern-Weg", 1),
    ("Von-Feld (onChange + onBlur)", 2),
    ("Bis-Feld (onChange + onBlur)", 2),
    ("Pause-Feld (onChange)", 1),
)

# Die Uhrzeit-Arithmetik selbst. Beide Ausdruecke duerfen AUSSCHLIESSLICH im
# Rumpf von _wrapHrs stehen - sonst rechnet jemand von Hand und verliert den
# Uebernacht-Fall. Gemessen v3.9.922 (kommentarblind): `new Date("2000-01-01T`
# 2x, `36e5` 1x, alle drei im _wrapHrs-Rumpf. Das ersetzt das fruehere
# Einzelverbot `new Date("2000-01-01T"+addBis)`, das nur EINE Schreibweise
# kannte und schon bei einer anderen Variablenbenennung blind war.
_ZEITMATHE = ('new Date("2000-01-01T', "36e5")


def _abschnitte(region):
    """Kopf + die drei Feld-Abschnitte, oder None wenn die Anker nicht passen."""
    if any(region.count(anker) != 1 for anker in _FELDANKER):
        return None
    stellen = [region.find(anker) for anker in _FELDANKER]
    if not (0 < stellen[0] < stellen[1] < stellen[2]):
        return None
    return (region[:stellen[0]], region[stellen[0]:stellen[1]],
            region[stellen[1]:stellen[2]], region[stellen[2]:])


def _mangel(code):
    """Alle Abweichungen von den benannten Stellen. Leere Liste = gruen."""
    aus = []
    if code.count("function _wrapHrs(") != 1:
        aus.append("Definition `function _wrapHrs(` kommt %dx vor statt 1x"
                   % code.count("function _wrapHrs("))
    summe = code.count("function _wrapHrs(")

    rumpf = _extract_fn(code, "_wrapHrs") or ""
    for ausdruck in _ZEITMATHE:
        drinnen, gesamt = rumpf.count(ausdruck), code.count(ausdruck)
        if drinnen != gesamt:
            aus.append("Uhrzeit-Arithmetik %r steht %dx ausserhalb von _wrapHrs "
                       "- da rechnet jemand von Hand"
                       % (ausdruck, gesamt - drinnen))

    helfer = _extract_fn(code, _HELFER)
    if not helfer:
        aus.append("Helfer %s nicht gefunden" % _HELFER)
    else:
        ist = helfer.count("_wrapHrs(")
        summe += ist
        if ist != 1:
            aus.append("%s: %d _wrapHrs-Aufrufe statt 1" % (_HELFER, ist))

    for komp in _KOMPONENTEN:
        region = _extract_fn(code, komp)
        if not region:
            aus.append("Komponente %s nicht gefunden" % komp)
            continue
        teile = _abschnitte(region)
        if teile is None:
            aus.append("%s: Feld-Anker %r nicht mehr genau einmal und in "
                       "Reihenfolge - der Schnitt ist nicht mehr eindeutig"
                       % (komp, _FELDANKER))
            continue
        for (rolle, erwartet), teil in zip(_ROLLEN, teile):
            ist = teil.count("_wrapHrs(")
            summe += ist
            if ist != erwartet:
                aus.append("%s / %s: %d _wrapHrs-Aufrufe statt %d"
                           % (komp, rolle, ist, erwartet))

    gesamt = code.count("_wrapHrs(")
    if summe != gesamt:
        aus.append("%d _wrapHrs-Vorkommen ausserhalb ALLER benannten Stellen "
                   "(benannt %d, gesamt %d)" % (gesamt - summe, summe, gesamt))
    return aus


def test_wraphrs_an_jeder_benannten_stelle(index_html):
    """JEDE von/bis-Stundenrechnung laeuft ueber _wrapHrs - je Feld einzeln."""
    assert _mangel(nur_code(index_html)) == []


def test_umkehrprobe_tausch_wird_rot(index_html):
    """DER GRUND DER UMSTELLUNG. Eine Rechnung wandert vom Von- ins Bis-Feld:
    die Gesamtzahl bleibt gleich (die alte Zahl WAERE gruen), der neue Riegel
    wird rot und benennt beide Seiten."""
    code = nur_code(index_html)
    region = _extract_fn(code, "VZeit")
    kopf, von, bis, pause = _abschnitte(region)
    getauscht = (kopf
                 + von.replace("_wrapHrs(", "_vonHandGerechnet(", 1)
                 + bis.replace("_wrapHrs(", "_wrapHrs(_wrapHrs(", 1)
                 + pause)
    kaputt = code.replace(region, getauscht, 1)
    assert kaputt != code, "Umkehrprobe hat nichts veraendert"
    assert kaputt.count("_wrapHrs(") == code.count("_wrapHrs("), (
        "Vorbedingung der Probe: die Gesamtzahl MUSS beim Tausch gleich "
        "bleiben - sonst zeigt die Probe nicht, was sie zeigen soll"
    )
    schaden = _mangel(kaputt)
    assert (any("Von-Feld" in s for s in schaden)
            and any("Bis-Feld" in s for s in schaden)), (
        "Der Tausch wird nicht bemerkt - der Riegel misst wieder nur die "
        "Gesamtzahl. Gemeldet wurde: %r" % (schaden,)
    )


def test_umkehrprobe_handrechnung_wird_rot(index_html):
    """Eine handgeschriebene Uebernacht-Rechnung ausserhalb von _wrapHrs: die
    Zahl der Aufrufe steigt dadurch NICHT (die alte Zahl waere gruen) - rot
    muss es trotzdem werden."""
    code = nur_code(index_html)
    handrechnung = ('let _hx=(new Date("2000-01-01T"+bis)-'
                    'new Date("2000-01-01T"+von))/36e5;')
    kaputt = code + chr(10) + handrechnung
    assert kaputt.count("_wrapHrs(") == code.count("_wrapHrs("), \
        "Vorbedingung: die Handrechnung darf die Aufrufzahl nicht veraendern"
    assert any("von Hand" in s for s in _mangel(kaputt)), (
        "Eine handgeschriebene von/bis-Rechnung ausserhalb _wrapHrs bleibt "
        "unbemerkt - genau der Fehler, den dieser Riegel finden soll"
    )


def test_umkehrprobe_entfall_wird_rot(index_html):
    """Faellt eine Stelle ersatzlos weg, muss sie NAMENTLICH gemeldet werden."""
    code = nur_code(index_html)
    region = _extract_fn(code, "ZeiterfassungView")
    kopf, von, bis, pause = _abschnitte(region)
    ohne = kopf + von + bis + pause.replace("_wrapHrs(", "_vonHandGerechnet(", 1)
    kaputt = code.replace(region, ohne, 1)
    assert any("ZeiterfassungView / Pause-Feld" in s for s in _mangel(kaputt)), \
        "Entfall im Pause-Feld wird nicht benannt gemeldet"


def test_logout_nulls_token_before_fetch(index_html):
    body = _extract_fn(index_html, "_sbAuthLogout")
    assert body, "_sbAuthLogout nicht gefunden"
    # Token wird in _tok gekapselt und _authToken SOFORT genullt, DANN fetch mit _tok.
    i_capture = body.index("const _tok=_authToken;_authToken=null")
    i_fetch = body.index('fetch(_SB_AUTH+"/logout"')
    assert i_capture < i_fetch, "Token muss VOR dem Logout-fetch synchron genullt werden"
    assert '"Bearer "+_tok' in body, "Logout-fetch muss den gekapselten _tok nutzen"
