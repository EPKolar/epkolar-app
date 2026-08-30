# -*- coding: utf-8 -*-
"""v3.9.913 - Das Fahrtenbuch sagte "keine Fahrten", wenn es nicht laden konnte.

    }catch(e){ console.warn('[fahrtenbuch]', e && e.message || e); }
    setBusy(false); setGeladen(true);

Der Auffangzweig schluckte den Fehler in die Konsole, und **danach wurde der
Ladezustand auf fertig gesetzt**. Die Segmentliste blieb leer - also meldete die
Ansicht "Keine Fahrten im gewaehlten Zeitraum" und der Export "Keine Fahrten im
Zeitraum".

**Das Fahrtenbuch ist ein Steuerbeleg.** Ein leeres Blatt, das aus einem
Netzfehler entstanden ist, sieht genauso aus wie ein Monat ohne Fahrten - und es
wuerde genauso abgelegt und vorgelegt.

Damit ist der letzte der beiden Reste an der Wurzel von v3.9.910 geschlossen
(der andere war das stille Loeschen beim Abmelden, v3.9.912).

────────────────────────────────────────────────────────────────────────────
Warum hier ein eigener Zustand noetig war
────────────────────────────────────────────────────────────────────────────
An den Chef-Kacheln genuegte `null`, weil `_metric` Nichtwissen laengst als drei
Punkte darstellen kann (v3.9.908/909/911). Hier gibt es nichts dergleichen: die
Leermeldung ist ein fest formulierter Absatz, und der Export prueft schlicht
`segs.length`. Also ein zweiter Zustand neben dem Ladezustand - und drei
Verbraucher, die ihn lesen:

  * die Leermeldung sagt jetzt, dass der Abruf gescheitert ist und ob Fahrten
    vorliegen damit UNBEKANNT ist
  * beide Exporte VERWEIGERN - ein Steuerbeleg darf nicht aus einem Netzfehler
    entstehen

Der Merker wird zu Beginn jedes Laufs zurueckgesetzt. Ohne das bliebe die
Warnung stehen, nachdem es wieder geklappt hat - eine Warnung, die nicht mehr
weggeht, wird genauso ignoriert wie eine, die nie kommt.

────────────────────────────────────────────────────────────────────────────
Eigener Fehler beim Bauen
────────────────────────────────────────────────────────────────────────────
Mein erster Erklaerkommentar setzte zwei Bezeichner in Backticks. Die
geschweifte Klammerbilanz kippte daraufhin von 0 auf 1, obwohl der Code stimmte:
der Klammer-Riegel strippt Kommentare und Template-Literale in EINER
Alternation, und ein Backtick im Kommentar bringt ihn aus dem Tritt. Die Regel
stand seit v3.9.898 in den Notizen - ich bin trotzdem hineingelaufen.
"""
from _hilfen import nur_code


def test_es_gibt_einen_eigenen_fehlerzustand(index_html):
    code = nur_code(index_html)
    assert "const [ladeFehler,setLadeFehler]=_react.useState.call(void 0, false);" in code, (
        "Der Fehlerzustand fehlt - dann ist ein gescheiterter Abruf wieder "
        "ununterscheidbar von einem Monat ohne Fahrten."
    )


def test_der_auffangzweig_meldet_ihn(index_html):
    code = nur_code(index_html)
    assert ("catch(e){console.warn('[fahrtenbuch]',e&&e.message||e);"
            "setLadeFehler(true);") in code, (
        "Der Auffangzweig schreibt den Fehler wieder nur in die Konsole - fuer "
        "die Ansicht ist er damit unsichtbar."
    )


def test_jeder_lauf_faengt_ohne_altlast_an(index_html):
    """Eine Warnung, die nicht mehr weggeht, wird genauso ignoriert wie eine,
    die nie kommt."""
    code = nur_code(index_html)
    assert "setLadeFehler(false);" in code, (
        "Der Merker wird zu Beginn eines Laufs nicht zurueckgesetzt."
    )


def test_die_leermeldung_unterscheidet(index_html):
    code = nur_code(index_html)
    assert "ladeFehler?'Fahrten konnten nicht geladen werden'" in code, (
        "Die Leermeldung sagt weiterhin 'keine Fahrten', auch wenn der Abruf "
        "gescheitert ist."
    )
    assert "UNBEKANNT" in index_html, (
        "Der Text sagt nicht, dass unbekannt ist, ob Fahrten vorliegen - genau "
        "das ist der Unterschied zu 'es gab keine'."
    )


def test_beide_exporte_verweigern(index_html):
    """Der wichtigste Teil: ein Steuerbeleg darf nicht aus einem Netzfehler
    entstehen. Der Bildschirmtext ist aergerlich, ein abgelegtes leeres
    Fahrtenbuch ist eine Falschaussage mit Folgen."""
    code = nur_code(index_html)
    n = code.count("if(ladeFehler){if(window.__toast)window.__toast('Export nicht moeglich")
    assert n == 2, (
        "Erwartet werden ZWEI verweigernde Exporte (Excel und PDF) - gefunden: "
        "%d. Ein ungeschuetzter Export legt ein leeres Fahrtenbuch ab." % n
    )


def test_die_pruefung_auf_leer_bleibt_dahinter(index_html):
    """GEGENPROBE: der Fall 'wirklich keine Fahrten' war schon richtig und muss
    erhalten bleiben - sonst verweigerte der Export auch dann, wenn schlicht
    nichts gefahren wurde."""
    code = nur_code(index_html)
    assert code.count("if(!segs.length){if(window.__toast)"
                      "window.__toast('Keine Fahrten im Zeitraum','info');return;}") == 2, (
        "Die Leer-Pruefung der Exporte hat sich veraendert."
    )


def test_keine_backticks_im_neuen_kommentar(index_html):
    """Selbstschutz, aus eigenem Schaden: ein Backtick in einem Blockkommentar
    bringt den Klammer-Riegel aus dem Tritt - er strippt Kommentare und
    Template-Literale in EINER Alternation. Beim Bauen dieser Version kippte
    die geschweifte Bilanz genau daran von 0 auf 1."""
    i = index_html.find("v3.9.913: der Ladezustand allein reicht nicht")
    assert i != -1, "Der Erklaerkommentar fehlt"
    ende = index_html.find("*/", i)
    assert ende != -1
    assert chr(96) not in index_html[i:ende], (
        "Im Kommentar steht wieder ein Backtick."
    )


# ══ Umkehrprobe ═════════════════════════════════════════════════════════════

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    z1 = index_html.replace("setLadeFehler(true);", "", 1)
    assert z1 != index_html, "Rueckbau 1 griff nicht"
    assert ("catch(e){console.warn('[fahrtenbuch]',e&&e.message||e);"
            "setLadeFehler(true);") not in nur_code(z1), (
        "Umkehrprobe: der Auffangzweig-Riegel wuerde nicht anschlagen"
    )

    z2 = index_html.replace(
        "if(ladeFehler){if(window.__toast)window.__toast('Export nicht moeglich", "if(false){if(window.__toast)window.__toast('Export nicht moeglich", 1)
    assert z2 != index_html, "Rueckbau 2 griff nicht"
    assert nur_code(z2).count(
        "if(ladeFehler){if(window.__toast)window.__toast('Export nicht moeglich") == 1, (
        "Umkehrprobe: der Export-Riegel wuerde einen ungeschuetzten Export nicht "
        "bemerken"
    )
