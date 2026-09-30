# -*- coding: utf-8 -*-
"""Drei Befunde aus zwei Messungen, die zum ersten Mal ueberhaupt gefahren
worden sind: „Berechtigungen gegen Oberflaeche" und „Kiosk-Anzeigen".

## R1 — der Waechter deckte die TABELLE, aber nicht den WEG

Seit v3.9.994 fuehrt `_RLS_SILENT_DENIAL_LABELS` 23 Tabellen: antwortet die
Datenbank auf eine Aenderung mit HTTP 200 und einem **leeren Array**, gilt
das nicht mehr als Erfolg, sondern als Abweisung des Zeilenschutzes.

Der Waechter sass aber **nur im Uebersetzer der Warteschlange**. Gemessen:
**21 Schreibaufrufe** laufen baulich daran vorbei, weil sie `_sbPatch` direkt
rufen. **Fuenf davon treffen Tabellen, die in der Tafel stehen** —
`fahrzeuge` (drei Stellen), `werkzeuge`, `fz_termine`. Der Eintrag
`fahrzeuge` war dort also eine **Attrappe**: er sieht nach Deckung aus und
konnte von diesen Wegen nie feuern. Besonders schief, weil laut Kommentar
genau der stille Tank-/km-Verlust der Grund war, den Waechter zu bauen.

**Kur an EINER Stelle statt an fuenf:** die Pruefung steht jetzt in
`_sbPatch` selbst. Damit sind alle 21 Umwege gedeckt und jeder kuenftige auch.

🔴 **Warum das kein Fehlalarm wird — gemessen, nicht angenommen:**
`_sbPatch` sendet ueber `_sbWH()` die Kopfzeile `Prefer: return=representation`.
Die Antwort traegt also die geaenderten Zeilen; leer heisst bei einem Zugriff
ueber `id=eq.<kennung>` wirklich null Zeilen. Gemeldet wird nur fuer die 23
Tabellen der Tafel — genau die Menge, die dafuer durchgesehen worden ist.

## R6 — der Hinweis auf verworfene Eingaben nannte die KENNUNG

Wird ein Eintrag nach fuenf Versuchen verworfen, sagt die App es — aber sie
nannte das letzte Stueck der Adresse, bei einem PATCH die Zeilenkennung. Der
Monteur liest „verworfen: 1730384921_7f3a" und weiss nicht, **was** weg ist.
Jetzt steht der Name der Handlung aus derselben Waechtertafel da.

🔴 **Ein eigener Irrtum, hier festgehalten:** beim ersten Lesen sah es aus,
als stuende die Zaehlung **im** `catch` des Fehlschlag-Protokolls — dann
waere der Hinweis im Regelfall nie erschienen. Das war falsch; das `catch`
ist eine Zeile vorher geschlossen. Aufgefallen ist es nur, weil der Anker
nicht passte und ich den echten Text aus der Datei geschnitten habe, statt
ihn zu tippen.

## B4 — der „Stand" auf der Wochenplantafel war die UHR

**Am Schirm gemessen**, nicht im Quelltext: die Tafel lief 40 Minuten ohne
Netz. Die Zwillingstafel schrieb „Daten von 14:18 · seit 40 min nicht
aktualisiert", die Wochenplantafel „Stand 14:58". Sie behauptete Frische,
die sie nie geprueft hat — an einer Wand, an der niemand nachfragt.

Der Grund stand in einer Zeile: ein Zeitgeber, der eine Uhr weiterstellte,
ohne jede Verbindung zu einem Abruf.

**Dieselbe Kur gibt es seit v3.9.939 fuer die Zwillingstafel** und ist hier
**abgeschrieben, nicht nachgebaut**: zwei getrennte Merker, und der Stand
bewegt sich nur nach einem erfolgreichen Abruf.

🔴 **Was dieser Stand misst, und was nicht:** die Tafel holt selbst nur die
Abwesenheitszeilen. Namen und Fahrzeuge kommen als Eigenschaften von aussen
und werden nach dem Start **nie wieder** geholt — eigener Befund (B7), bleibt
offen. Der Stand sagt also: so alt ist der letzte erfolgreiche Abruf *dieser*
Tafel. Weniger, als man erwarten koennte — aber wahr, und eine Uhr war es
nicht.
"""
import io
import os
import re

HIER = os.path.dirname(os.path.abspath(__file__))
PFAD = os.path.join(HIER, "..", "index.html")


def _text():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _ohne_kommentare(s):
    """🔴 Die Kur-Kommentare zitieren die alten Formen woertlich."""
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return re.sub(r"//[^\n]*", "", s)


def test_koeder_die_kommentarbehandlung_traegt():
    mit = "/* HIER STAND setStand(new Date()),60000 */ x=1;"
    assert "setStand(new Date()),60000" not in _ohne_kommentare(mit), (
        "Ein Kommentar, der die alte Form zitiert, wird mitgezaehlt.")


def test_r1_der_waechter_sitzt_in_sbpatch():
    code = _ohne_kommentare(_text())
    i = code.find("async function _sbPatch(")
    assert i > 0, "\U0001F534 _sbPatch ist weg."
    rumpf = code[i:i + 1600]
    assert "_RLS_SILENT_DENIAL_LABELS[table]" in rumpf, (
        "\U0001F534 Die Pruefung auf die stille Abweisung ist aus _sbPatch "
        "verschwunden.\n  Dann laufen 21 Schreibaufrufe wieder ungedeckt "
        "daran vorbei, davon fuenf auf\n  Tabellen, die in der Waechtertafel "
        "STEHEN - der Eintrag dort waere wieder eine\n  Attrappe.")
    assert "_pr.length===0" in rumpf, (
        "\U0001F534 Der Test auf die leere Antwort fehlt.")


def test_r1_koeder_die_kopfzeile_traegt_die_pruefung():
    """🔴 Gegenprobe zur Praemisse der Kur.

    Die Pruefung ist nur sinnvoll, weil `_sbWH()` `return=representation`
    sendet - sonst kaeme IMMER eine leere Antwort und die Meldung feuerte bei
    jedem Schreibvorgang. Genau dieser Fehlalarm ist am 30.09. schon einmal
    gebaut worden (B2, `limit=1`). Faellt die Kopfzeile weg, gehoert die Kur
    zurueckgenommen - und dieser Riegel sagt es.
    """
    code = _ohne_kommentare(_text())
    assert 'return=representation' in code and "_sbWH" in code, (
        "\U0001F534 `Prefer: return=representation` ist weg. Dann ist eine "
        "leere Antwort der\n  NORMALFALL, und die Pruefung in _sbPatch "
        "meldet bei JEDEM Schreibvorgang.\n  Das waere der Fehlalarm aus "
        "v3.9.995 noch einmal.")


def test_r6_der_hinweis_nennt_die_handlung_nicht_die_kennung():
    code = _ohne_kommentare(_text())
    assert '_dropNames.push((item.url||"").split("/").pop());' not in code, (
        "\U0001F534 Der Hinweis nennt wieder das letzte Stueck der Adresse - "
        "bei einem PATCH\n  die Zeilenkennung. Der Monteur liest dann "
        "\"verworfen: 1730384921_7f3a\".")
    assert "_dropNames.push(_sqDropName(item));" in code, (
        "\U0001F534 Der Name der Handlung fehlt.")
    assert code.count("function _sqDropName(") == 1, (
        "\U0001F534 Der Helfer, der die Adresse in einen Namen uebersetzt, "
        "ist weg.")


def test_b4_der_stand_der_wochenplantafel_ist_nicht_die_uhr():
    code = _ohne_kommentare(_text())
    assert "setInterval(()=>setStand(new Date()),60000)" not in code, (
        "\U0001F534 Der Zeitgeber stellt wieder den STAND statt der Uhr. "
        "Dann behauptet die\n  Tafel an der Wand Frische, die sie nie "
        "geprueft hat - am Schirm gemessen:\n  40 min ohne Netz, und sie "
        "zeigte trotzdem die aktuelle Uhrzeit.")
    i = code.find("function WochenplanTafel(props){")
    assert i > 0, "\U0001F534 Die Wochenplantafel ist weg."
    rumpf = code[i:i + 30000]
    assert "setJetzt(Date.now())" in rumpf, (
        "\U0001F534 Der zweite Merker fehlt. Ohne ihn waechst der Alterstext "
        "nicht mit.")
    assert "setAbsRows(j);setStand(new Date());" in rumpf, (
        "\U0001F534 Der Stand wird nicht mehr am ERFOLGREICHEN Abruf "
        "gesetzt.")
    assert "_wpTafelAlter(stand,jetzt)" in rumpf, (
        "\U0001F534 Die Anzeige sagt nicht mehr das Alter.")


def test_b4_der_alterstext_nennt_beides_text_und_faerbung():
    """🔴 Nie Farbe allein.

    Auf einer Baustelle steht man in der Sonne, und Rot-Gruen ist die
    haeufigste Farbsehschwaeche. Die Zwillingstafel haelt das seit v3.9.939
    so; hier wird es mitgemessen, damit die Uebertragung nicht auf halbem
    Weg stehenbleibt.
    """
    t = _text()
    i = t.find("function _wpTafelAlter(")
    assert i > 0, "\U0001F534 Der Alterstext ist weg."
    rumpf = t[i:i + 1200]
    assert "nicht aktualisiert" in rumpf, (
        "\U0001F534 Der Klartext fehlt - dann bleibt nur eine Uhrzeit, und "
        "die sagt nichts\n  ueber das Alter der Daten.")
    assert "Daten von " in rumpf, (
        "\U0001F534 Der Zeitpunkt des letzten Abrufs wird nicht mehr "
        "genannt.")
    assert "KIOSK_STAND_WARN_MS" in rumpf, (
        "\U0001F534 Die Schwelle der Zwillingstafel wird nicht mehr benutzt. "
        "Zwei Tafeln mit\n  zwei verschiedenen Schwellen sind schlimmer als "
        "eine.")
