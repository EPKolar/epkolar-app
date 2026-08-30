# -*- coding: utf-8 -*-
"""v3.9.915 - Ein Feiertag haette ab Ende September die GANZE Dispo abgeraeumt.

    if(absAbz>=t.normMin){gruende.push(_dispoAbwLabel(ab.type));}

Seit v3.9.884 hat ein Feiertag `normMin === 0`. Hat der Monteur an diesem Tag
KEINEN Abwesenheitseintrag, ist `ab` undefined und `absAbz` 0 - und `0 >= 0` ist
wahr. Also wurde `ab.type` gelesen: TypeError.

WARUM DAS NICHT EIN TAG WAR, SONDERN ALLES
──────────────────────────────────────────
Der Aufruf steht in `try{ ... }catch(e){ return null; }`. Der Wurf macht also
nicht eine Zelle kaputt, sondern `_built` zu `null` - und die Ansicht zeigt
statt des Rasters den Satz "Vorschlagsplanung konnte nicht berechnet werden".
Ein einziger Feiertag im Vier-Wochen-Horizont loescht die gesamte Dispo.

WARUM ES NOCH NIEMAND GESEHEN HAT
─────────────────────────────────
Es trifft nur Feiertage von Montag bis Freitag - am Wochenende gibt es keine
Tagesspalte. Mit der echten Funktion `_isATFeiertag` gemessen, kommen in den
naechsten zwoelf Monaten NEUN solche Tage; der erste ist Montag, 26.10.2026,
im Vier-Wochen-Horizont sichtbar ab etwa 28.09.2026. Zwischen v3.9.884 und
heute ist keiner hineingerutscht. Es war kein Glueck, sondern ein Kalender.

WARUM DER BESTEHENDE RIEGEL IHN NICHT SEHEN KONNTE
──────────────────────────────────────────────────
`test_dispo_feiertag_v884` prueft die `wtage`-Zeile, also die STELLE, an der
`normMin` auf 0 gesetzt wird. Er ruft `_dispoBuildInput` nie mit einem Feiertag
im Horizont auf. **Er teilt die Luecke des Geprueften** - dieselbe Krankheit wie
am 28.08. beim fehlenden Nationalfeiertag und wie bei v899.

Schlimmer noch: `test_dispo_asfrische_abw_v767` verlangte die abstuerzende Zeile
WOERTLICH. Er hat den Fehler nicht gefunden, sondern FESTGEHALTEN - und waere
gegen seine Reparatur rot geworden. Beide Riegel messen seit v3.9.915 die
Eigenschaft, und beide benutzen denselben Schnitt aus `tests/_hilfen.py`.

ZWEI DINGE WAREN ZU TUN, NICHT EINES
────────────────────────────────────
Nur `if(ab && ...)` haette den Wurf beseitigt und die Zelle stumm gelassen: am
Feiertag ist die Kapazitaet 0, die Zelle also hart gesperrt - aber ohne Grund
daneben. Eine Wand ohne Beschriftung. Der Feiertag braucht seinen eigenen Chip,
und er steht VOR der Abwesenheit: wer am Feiertag Urlaub eingetragen hat, soll
trotzdem lesen, dass es ein Feiertag ist.
"""
import re

from pathlib import Path

from _hilfen import dispo_zelle_lauf, dispo_zelle_programm

WURZEL = Path(__file__).resolve().parents[1]
INDEX = WURZEL / "index.html"

WERKTAG = {"key": "d", "iso": "2026-10-27", "wtag": "Di", "normMin": 510, "feiertag": False}
FEIERTAG = {"key": "d", "iso": "2026-10-26", "wtag": "Mo", "normMin": 0, "feiertag": True}
URLAUB_FEI = {"Huber_2026-10-26": {"type": "urlaub", "status": "genehmigt", "hours": 0}}
URLAUB_DI = {"Huber_2026-10-27": {"type": "urlaub", "status": "genehmigt", "hours": 0}}

FAELLE = [
    {"t": WERKTAG, "absMap": {}},
    {"t": FEIERTAG, "absMap": {}},
    {"t": FEIERTAG, "absMap": URLAUB_FEI},
    {"t": WERKTAG, "absMap": URLAUB_DI},
]


def test_feiertag_wirft_nicht_und_nennt_seinen_grund(tmp_path):
    programm = dispo_zelle_programm(INDEX.read_text(encoding="utf-8"))
    aus = dispo_zelle_lauf(programm, tmp_path, FAELLE, "jetzt.js")

    for i, r in enumerate(aus):
        assert r["ok"], "Fall {} wirft: {}".format(i, r.get("fehler"))

    assert aus[0]["labels"] == [], "Werktag ohne Abwesenheit: kein Grund-Chip"
    assert aus[1]["labels"] == ["Feiertag"], \
        "Feiertag OHNE Abwesenheitseintrag muss 'Feiertag' nennen, nicht stumm sperren"
    assert aus[2]["labels"] == ["Feiertag"], \
        "Feiertag schlaegt Urlaub - der Feiertag ist die staerkere Aussage"
    assert aus[3]["labels"] == ["Urlaub"], \
        "Am Werktag muss die Abwesenheit weiterhin ihren eigenen Grund nennen"


def test_gegenprobe_die_alte_bedingung_wirft(tmp_path):
    """Ohne diese Umkehr waere nicht belegt, dass der Aufbau den Fehler SIEHT.

    Genau das war der Mangel der sechs Form-Riegel: gruen, und trotzdem blind.
    """
    programm = dispo_zelle_programm(INDEX.read_text(encoding="utf-8"))

    alt = re.sub(
        r'if\(t\.feiertag\)\{gruende\.push\(\{icon:"[^"]*",label:"Feiertag"\}\);\}\s*'
        r'else if\(ab&&absAbz>=t\.normMin\)',
        "if(absAbz>=t.normMin)", programm, count=1)
    assert alt != programm, "Die Umkehr hat nichts ersetzt - der Riegel misst nichts"

    aus = dispo_zelle_lauf(alt, tmp_path, FAELLE, "alt.js")
    assert aus[0]["ok"], "Der Werktag hat auch frueher nicht geworfen"
    assert not aus[1]["ok"], \
        "Die alte Bedingung MUSS am Feiertag ohne Eintrag werfen - sonst misst dieser Riegel nichts"
    assert "type" in aus[1]["fehler"], aus[1]["fehler"]
