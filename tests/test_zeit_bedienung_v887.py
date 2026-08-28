# -*- coding: utf-8 -*-
"""v3.9.887 - Drei Reibungspunkte, die den Monteur jeden Abend Zeit kosten.

Zielgruppe im Blick: die App wird einhaendig am Handy bedient, auf der Baustelle,
oft mit schmutzigen oder behandschuhten Fingern, bei Sonnenlicht, am Feierabend.
Jeder ueberfluessige Tipp kostet Akzeptanz - und wenn Zeiterfassung laestig ist,
wird sie falsch oder gar nicht gemacht. Das trifft direkt den Lohn.

────────────────────────────────────────────────────────────────────────────
1 - Der Knopf "Zeit" oeffnete die PLANUNG.
────────────────────────────────────────────────────────────────────────────
Die Bottom-Nav gruppiert die Reiter; ein Gruppenknopf sprang auf `grTabs[0]`,
also den ERSTEN Reiter der Gruppe. In Gruppe 2 steht Planung (`g:2`) vor
Zeiterfassung (`g:2`) - der Knopf mit der Stoppuhr oeffnete also die
Wochenplanung, und der Monteur musste ein zweites Mal tippen.

Jeden Abend. Bei jedem App-Start.

FIX: eine Gruppe darf ihr Ziel benennen (`ziel:"zeiterfassung"`). Die
Reiterleiste bleibt unveraendert - sie umzusortieren waere ein groesserer
Eingriff mit mehr Nebenwirkungen, und die Reihenfolge oben ist gewollt. Gruppen
ohne `ziel` verhalten sich exakt wie bisher.

────────────────────────────────────────────────────────────────────────────
2 - Der eigene Arbeitsschein konnte in der Auswahl schlicht fehlen.
────────────────────────────────────────────────────────────────────────────
    (arbeitsscheine||[]).slice(0,50)

Ohne Filter auf den gewaehlten Monteur, ohne Statusfilter, ohne Sortierung - und
geladen werden die Scheine ebenfalls ohne `order=`. Der eigene offene Schein
KONNTE also schlicht nicht unter den ersten 50 sein. Dann war er ueber diesen Weg
unerreichbar, und der Monteur buchte auf "frei" oder gar nicht.

FIX: die eigenen zuerst, offene vor abgeschlossenen, neueste zuerst. Und die
Kappung ist keine stille Obergrenze mehr - sie sagt, wenn sie greift.

────────────────────────────────────────────────────────────────────────────
3 - Kein Weg zurueck zur laufenden Woche.
────────────────────────────────────────────────────────────────────────────
Es gab nur die Pfeile und ein "Aktuell"-Abzeichen, das anzeigt, dass man richtig
liegt - nicht, wie man zurueckkommt. Die Tageskarten sehen in jeder KW gleich
aus. Wer eine Woche zurueckblaettert und es vergisst, bucht in die falsche
LOHNWOCHE.

Die Projekt-Zeiterfassung und die Planung haben so einen Knopf laengst. Nur die
Hauptansicht, in der am meisten gebucht wird, hatte keinen.
"""
import re


# ══ 1 - Der Zeit-Knopf ══════════════════════════════════════════════════════

def test_die_zeit_gruppe_nennt_ihr_ziel(index_html):
    assert '{i:"⏱️",l:"Zeit",g:2,c:"#3b82f6",ziel:"zeiterfassung"}' in index_html, (
        "Die Zeit-Gruppe benennt ihr Ziel nicht mehr - dann springt sie wieder "
        "auf den ersten Reiter der Gruppe, und das ist die Planung."
    )


def test_das_ziel_wird_auch_ausgewertet(index_html):
    assert 'var _grZiel=gr.ziel?grTabs.find(function(t){return t.perm===gr.ziel;}):null;' in index_html, (
        "Das Gruppenziel wird nicht mehr aufgeloest - dann ist die Angabe "
        "wirkungslos und der Knopf oeffnet wieder die Planung."
    )
    assert "const grFirst=_grZiel?tabs.indexOf(_grZiel):(grTabs[0]?tabs.indexOf(grTabs[0]):0);" in index_html, (
        "grFirst benutzt das aufgeloeste Ziel nicht."
    )


def test_gruppen_ohne_ziel_verhalten_sich_wie_bisher(index_html):
    """Bewusste Grenze: nur die Zeit-Gruppe bekommt ein Ziel. Alle anderen
    springen weiter auf ihren ersten Reiter - das war und ist richtig."""
    n = len(re.findall(r'ziel:"[a-z_]+"\}', index_html))
    assert n == 1, (
        "Erwartet genau EINE Gruppe mit Ziel (Zeit), gefunden %d. Weitere Ziele "
        "sind moeglich, muessen aber begruendet sein - sonst wird die Navigation "
        "unvorhersehbar." % n
    )
    assert "(grTabs[0]?tabs.indexOf(grTabs[0]):0)" in index_html, (
        "Der Rueckfall auf den ersten Reiter ist weg - Gruppen ohne Ziel haetten "
        "dann gar kein Ziel mehr."
    )


def test_die_reiterleiste_bleibt_unveraendert(index_html):
    """Gegenprobe: die Reihenfolge oben wurde NICHT umsortiert. Sie zu drehen
    waere der groessere Eingriff gewesen und haette andere Ansichten getroffen."""
    i_plan = index_html.find('{l:"Planung",i:"📅"')
    i_zeit = index_html.find('{l:"Zeiterfassung",i:"⏱️"')
    assert i_plan != -1 and i_zeit != -1, "Reiter nicht gefunden"
    assert i_plan < i_zeit, (
        "Die Reiterleiste wurde umsortiert. Der Fix sollte das Gruppenziel "
        "benennen, nicht die Reihenfolge aendern."
    )


# ══ 2 - Die Scheinauswahl ═══════════════════════════════════════════════════

def test_die_eigenen_scheine_kommen_zuerst(index_html):
    assert 'var _mine=(arbeitsscheine||[]).filter(function(a){return a&&(!selWorker||a.monteur===selWorker);});' in index_html, (
        "Die Scheinauswahl sortiert die eigenen nicht mehr nach vorn - dann kann "
        "der eigene offene Schein wieder ausserhalb der Kappung liegen."
    )


def test_offene_vor_abgeschlossenen(index_html):
    assert "AS_GRP_OFFEN.indexOf(a.scheinstatus)>=0)?0:1;" in index_html, (
        "Offene Scheine werden nicht mehr vorgereiht."
    )


def test_die_kappung_ist_nicht_mehr_still(index_html):
    """Der eigentliche Fehler war nicht die Zahl 50, sondern dass niemand
    erfuhr, dass gekappt wurde."""
    assert "weitere nicht angezeigt" in index_html, (
        "Die Kappung meldet sich nicht mehr - eine stille Obergrenze sieht aus "
        "wie 'es gibt nicht mehr', und genau daran ist der eigene Schein "
        "unauffindbar geworden."
    )
    assert "var _kap=_liste.slice(0,200);" in index_html, (
        "Die Obergrenze ist nicht mehr 200 - kleiner ist riskant, groesser macht "
        "das Auswahlfeld auf dem Handy unbedienbar."
    )


def test_die_alte_willkuerliche_kappung_ist_weg(index_html):
    assert "(arbeitsscheine||[]).slice(0,50)" not in index_html, (
        "Die ungefilterte 50er-Kappung ist zurueck."
    )


# ══ 3 - Der Heute-Knopf ═════════════════════════════════════════════════════

def test_es_gibt_einen_weg_zurueck(index_html):
    assert "kw!==curKw&&React.createElement('button',{onClick:()=>switchKw(curKw)," in index_html, (
        "Der Heute-Knopf fehlt - wer eine Woche zurueckblaettert und es vergisst, "
        "bucht in die falsche Lohnwoche."
    )


def test_er_erscheint_nur_wenn_er_etwas_tut(index_html):
    """Ein Knopf, der in der aktuellen Woche sichtbar ist und nichts bewirkt,
    ist schlechter als keiner."""
    assert "kw!==curKw&&React.createElement('button'" in index_html, (
        "Der Heute-Knopf ist nicht mehr an die Bedingung geknuepft."
    )


def test_er_ist_mit_handschuh_treffbar(index_html):
    """Das Repo misst selbst gegen 44px."""
    i = index_html.find("Zurueck zur laufenden Woche")
    assert i != -1, "Heute-Knopf nicht gefunden"
    block = index_html[i:i + 320]
    assert "minHeight:isMob?44:0" in block, (
        "Der Heute-Knopf ist am Handy unter 44px - genau die Groesse, die mit "
        "Handschuh danebengeht:\n" + block[:200]
    )


# ══ Umkehrprobe ═════════════════════════════════════════════════════════════

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    z1 = index_html.replace(',ziel:"zeiterfassung"}', "}", 1)
    assert z1 != index_html, "Rueckbau 1 griff nicht"
    assert 'ziel:"zeiterfassung"' not in z1, (
        "Umkehrprobe: der Ziel-Riegel wuerde nicht anschlagen"
    )

    z2 = index_html.replace("var _kap=_liste.slice(0,200);", "", 1)
    assert z2 != index_html, "Rueckbau 2 griff nicht"
    assert "var _kap=_liste.slice(0,200);" not in z2, (
        "Umkehrprobe: der Kappungs-Riegel wuerde nicht anschlagen"
    )

    z3 = index_html.replace("kw!==curKw&&React.createElement('button',{onClick:()=>switchKw(curKw),",
                            "false&&React.createElement('button',{onClick:()=>switchKw(curKw),", 1)
    assert z3 != index_html, "Rueckbau 3 griff nicht"
    assert "kw!==curKw&&React.createElement('button',{onClick:()=>switchKw(curKw)," not in z3, (
        "Umkehrprobe: der Heute-Riegel wuerde nicht anschlagen"
    )
