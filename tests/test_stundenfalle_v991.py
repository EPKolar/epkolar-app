# -*- coding: utf-8 -*-
"""Drei Wege, auf denen eine falsche Stundenzahl in die Zeiterfassung kam.

Alle drei sind in der Nacht auf den 30.09.2026 gefunden und in v3.9.991
gekurt worden. Sie haben dieselbe Handschrift: **der Fehlerfall wurde nicht
zu Ende gedacht, und das Ergebnis sah aus wie ein Erfolg.**

---

## Z6 — eine Stunde Anwesenheit wurde als ACHT Stunden gespeichert

An ZWEI wortgleichen Stellen (`addEntry`, index.html ~16143 und ~25479):

    let _h2 = addHours;                          // Vorbelegung 8
    if(_rVon&&_rBis){
      const _d = _wrapHrs(_rVon,_rBis) - addPause;
      if(_d > 0) _h2 = Math.round(_d*100)/100;   // <- NUR bei _d > 0
    }

Von 08:00, Bis 09:00, Pause 1 h ergibt `_d = 0`. `0 > 0` ist falsch, also
blieb `_h2` auf der Vorbelegung. Gespeichert wurde
`von:"08:00", bis:"09:00", pause:1, stunden:8` - acht Stunden fuer eine
Stunde, mit den widersprechenden Uhrzeiten im selben Satz, ohne Warnung.
Der Kommentar bei 2441-2446 verspricht ausdruecklich das Gegenteil.

**Kur:** sind beide Zeiten da, gilt die Rechnung - auch wenn sie 0 oder
negativ ist. Dann faellt die vorhandene Pruefung darauf, und eine eigene
Meldung nennt die wirkliche Ursache (Pause >= Anwesenheit).

---

## P3 — `_asZeitUebernahme` schrieb ohne Plausibilitaetswaechter

Fuenf der sechs Schreibwege nach `time_entries` pruefen `0<h<=24`
(16144, 25482, 14815, 13309, 13252). Dieser nicht. Und `_hhmmToMin` (875)
liest eine **nackte Zahl als STUNDEN**: wer `90` in „Arbeitszeit (hh:mm)"
tippt und 90 **Minuten** meint, schrieb `hours: 90`. Gemessen am
geschnittenen Code: `0:00/90 -> 90`, `0:00/999:59 -> 999.98`.

Von dort geht der Wert in Bauwochenbericht, Stundenbestaetigung, Lohn-Excel,
PZE-Projektzeit und ueber die 6-h-Regel in die **Entfernungszulage** - also
in Geld.

---

## D1 — der fehlgeschlagene Patch zeigte dem Nutzer NICHTS

    await _sbPatch("time_entries",_cur.id,{hours:_h});
    if(window.__toast)window.__toast("Zeiterfassung aktualisiert: ...");
    }catch(_e){console.warn(...);}

Der Erfolgstoast stand **hinter** dem `await` im selben `try` und fiel mit
aus; das `catch` schrieb nur in die Konsole. Weder Erfolg noch Fehler waren
zu sehen - und `ze_uebernommen` blieb `true`, also gab es **keinen zweiten
Versuch**. Arbeitsschein und Zeiterfassung standen dauerhaft auf
verschiedenen Stunden.

🔴 **Der Einfuege-Zweig dreissig Zeilen darueber macht es seit v3.9.876
richtig** - eigenes try/catch, 409-Sonderfall, ehrlicher Warn-Toast. Das
Geschwister daneben wurde uebersehen. Und es ist die **dritte Auspraegung**
derselben Klasse in zwei Tagen: was nach einem `await` im selben `try`
steht, faellt bei einem Fehler mit aus (siehe
`tests/test_geo_cache_nicht_tragend_v987.py`).

---

🔴 **WAS DIESER RIEGEL NICHT MISST, und warum das hier steht:** die
allgemeine Regel „jeder Schreibweg nach `time_entries` hat einen
Plausibilitaetswaechter" braucht den Rumpf der umgebenden Funktion. Das
Werkzeug dafuer (`code_scan._klammer_zu`) **kennt keine Regex-Literale** -
in derselben Nacht gemessen: der Rumpf von `_translateAndExec` kam mit
2 195 statt 341 Zeilen zurueck. Auf einem Werkzeug, von dem man weiss, dass
es hier falsch misst, wird kein Riegel gebaut. Die Klassenregel kommt nach,
sobald das Werkzeug repariert ist.
"""
import io
import os
import re

HIER = os.path.dirname(os.path.abspath(__file__))
PFAD = os.path.join(HIER, "..", "index.html")

ALTE_FORM = "if(_d>0)_h2=Math.round(_d*100)/100;"
NEUE_FORM = "_h2=Math.round(_d*100)/100;"
SPANNE_GEPRUEFT = "if(_d<=0)"
# Erwartete Zahl der `addEntry`-Stellen mit dieser Rechnung.
ERWARTET_ADDENTRY = 2


def _text():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _ohne_kommentare(s):
    """🔴 Die Kur-Kommentare NENNEN die alte Form. Wer den rohen Text
    durchsucht, misst seine eigene Begruendung mit und wird rot."""
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return re.sub(r"//[^\n]*", "", s)


def test_koeder_der_sucher_sieht_die_alte_form():
    """🔴 Ohne Selbstprobe waere jede Null hier wertlos."""
    alt = ("let _h2=addHours;if(_rVon&&_rBis){const _d=_wrapHrs(_rVon,_rBis)"
           "-addPause;" + ALTE_FORM + "}")
    assert ALTE_FORM in _ohne_kommentare(alt), (
        "Der Sucher findet die alte Form nicht einmal in einem Text, der nur "
        "daraus besteht.")
    # 🔴 Und die Gegenprobe zur Kommentarbehandlung: ein KOMMENTAR, der die
    #    alte Form zitiert, darf den Riegel NICHT rot machen.
    nur_kommentar = "/* HIER STAND " + ALTE_FORM + " - entfernt. */"
    assert ALTE_FORM not in _ohne_kommentare(nur_kommentar), (
        "Ein Kommentar, der die alte Form zitiert, macht den Riegel rot.\n"
        "  Dann muss die Begruendung weg, damit er gruen wird - genau "
        "verkehrt herum.")


def test_die_grundgesamtheit_stimmt():
    """🔴 Gegenprobe zur Null: gibt es die beiden Rechenstellen ueberhaupt?"""
    n = _ohne_kommentare(_text()).count(NEUE_FORM)
    assert n >= ERWARTET_ADDENTRY, (
        "Nur %d Stellen mit `%s` gefunden, erwartet waren mindestens %d.\n"
        "  Entweder ist eine weggefallen - dann gehoert dieser Riegel "
        "angepasst -, oder\n  der Sucher greift daneben und die Null der "
        "anderen Pruefung ist wertlos."
        % (n, NEUE_FORM, ERWARTET_ADDENTRY))


def test_z6_die_rechnung_gilt_auch_wenn_sie_null_ergibt():
    code = _ohne_kommentare(_text())
    assert ALTE_FORM not in code, (
        "Die alte Form `%s` steht wieder im Code.\n"
        "  Sind beide Zeiten da, MUSS die Rechnung gelten - auch wenn sie 0 "
        "ergibt.\n  Sonst bleibt die Stundenzahl auf der Vorbelegung: "
        "08:00-09:00 mit 1 h Pause\n  wurde als ACHT Stunden gespeichert."
        % ALTE_FORM)


def test_z6_eine_nicht_positive_spanne_wird_abgewiesen():
    code = _ohne_kommentare(_text())
    n = code.count(SPANNE_GEPRUEFT)
    assert n >= ERWARTET_ADDENTRY, (
        "Nur %d von %d Stellen weisen eine nicht-positive Spanne ausdruecklich "
        "ab (`%s`).\n  Ohne diese Meldung sieht der Nutzer nur "
        "„Stunden muessen 0<h≤24 sein“ und\n  erfaehrt nicht, "
        "dass seine PAUSE so lang ist wie die Anwesenheit."
        % (n, ERWARTET_ADDENTRY, SPANNE_GEPRUEFT))


def test_p3_die_zeituebernahme_hat_einen_plausibilitaetswaechter():
    """Die Stelle, die als einzige von sechs keinen hatte."""
    t = _text()
    i = t.find("const _asZeitUebernahme=async(schein)=>{")
    assert i > 0, ("`_asZeitUebernahme` ist nicht mehr zu finden - dann "
                   "gehoert dieser Riegel\n  angepasst, nicht weggezaehlt.")
    # Der Waechter muss VOR dem ersten Schreibaufruf der Funktion stehen.
    j = t.find('_sbPost("time_entries"', i)
    assert j > i, "Kein Schreibaufruf nach dem Funktionsanfang gefunden."
    kopf = _ohne_kommentare(t[i:j])
    assert re.search(r"_h>0&&_h<=24", kopf), (
        "In `_asZeitUebernahme` steht vor dem ersten Schreibaufruf kein "
        "`0<h<=24`-Waechter.\n  `_hhmmToMin` liest eine nackte Zahl als "
        "STUNDEN: wer 90 tippt und 90 MINUTEN\n  meint, schreibt hours=90 - "
        "und das geht ueber die 6-h-Regel in die\n  Entfernungszulage, also "
        "in Geld.")


def test_d1_der_patch_hat_seinen_eigenen_fehlerweg():
    t = _text()
    i = t.find('await _sbPatch("time_entries",_cur.id,{hours:_h});')
    assert i > 0, ("Der Patch-Aufruf ist nicht mehr zu finden - dann gehoert "
                   "dieser Riegel angepasst.")
    # Unmittelbar davor muss ein `try{` stehen, danach ein `catch`, das den
    # Nutzer erreicht.
    davor = t[max(0, i - 120):i]
    danach = _ohne_kommentare(t[i:i + 2200])
    assert "try{" in davor, (
        "Vor dem Patch steht kein eigenes `try{`. Dann faellt der "
        "Erfolgstoast dahinter\n  bei einem Fehler mit aus, und das aeussere "
        "`catch` schreibt nur in die Konsole -\n  der Nutzer sieht WEDER "
        "Erfolg NOCH Fehler.")
    m = re.search(r"catch\s*\(\s*_ue\s*\)\s*\{(.{0,900}?)\}", danach, re.S)
    assert m, ("Nach dem Patch steht kein eigenes `catch(_ue)`.")
    rumpf = m.group(1)
    assert "__toast" in rumpf, (
        "Das `catch` um den Patch meldet dem NUTZER nichts - es schreibt nur "
        "in die\n  Konsole. Genau so stand der Fehler drei Versionen lang "
        "lautlos da:\n  Arbeitsschein und Zeiterfassung auf verschiedenen "
        "Stunden, ohne ein Wort.")
    assert "ze_uebernommen" not in rumpf, (
        "Das `catch` setzt den Uebernahme-Merker - dann gilt ein "
        "fehlgeschlagener Patch\n  als erledigt und wird nie wiederholt.")
