# -*- coding: utf-8 -*-
"""
v3.9.880 - Die Lohn- und Zeit-Dokumente. Was auf dem Blatt steht, das der
Monteur unterschreibt und der Lohnverrechner verbucht.

GEPRUEFTE DOKUMENTE (per grep gefunden, nicht geraten):
  1. _pzePdf              Z.11711  PZE-Monatsblatt (jsPDF, A4 QUER), Uebergabe
                                   an den Lohnverrechner. Zwei Aufrufer:
                                   PZEView Z.11983 und KVZulagenReport Z.11606.
  2. exportWochenStz      Z.24524  Wochen-Stundenbestaetigung (MSO-HTML/.xls),
                                   Firmen-Vorlage, MIT Unterschriftsfeld.
  3. exportTagesStz       Z.24597  Tages-Stundenbestaetigung, dieselbe Vorlage.
  4. KVZulagenReport      Z.11461  Entfernungszulagen-Report, exportiert ueber
                                   _pzePdf (seit v3.9.776 keine eigene CSV mehr).
  5. exportMonat          Z.22482  Monatsuebersicht Abrechnung (Print-Window).
  6. AbsView "PDF"        Z.21779  window.print() der Bildschirmansicht.

=========================== BEFUND 1 (GELD) ===============================
Die Wochen-Stundenbestaetigung nimmt "GE:" (Gehen) aus dem ZWEITEN Eintrag
des Tages, "KO:" (Kommen) aus dem ERSTEN.

    Z.24543   const ko=e&&e.von?esc(e.von):"";     <- e = arr[ri]
    Z.24544   const ge=e&&e.bis?esc(e.bis):"";     <- e = arr[ri]
    Z.24547   ...>KO: ${ko}<...                    <- gedruckt bei ri===0
    Z.24550   const val=ri===1?ge:ri===2?mp:"";    <- gedruckt bei ri===1

ko und ge stammen aus DEMSELBEN e, gedruckt werden sie aus VERSCHIEDENEN
Schleifendurchlaeufen. Gemessen:

    1 Buchung/Tag (der Normalfall)  -> arr[1] fehlt  -> "GE:" LEER
    2 Buchungen                     -> GE = arr[1].bis (zufaellig richtig)
    3 Buchungen                     -> GE = arr[1].bis, das Ende ist arr[2].bis

Auswirkung: das unterschriebene Blatt weist ein Kommen ohne Gehen aus.
Arbeitsrechtlich ist genau das die Aufzeichnungspflicht (Beginn UND Ende).

=========================== BEFUND 2 (Optik) ==============================
"MP:" (Mittagspause) druckt IMMER einen leeren Wert.

    Z.24545   const mp=ri===0&&i<5?"12:00-13:00":"";
    Z.24550   const val=ri===1?ge:ri===2?mp:"";

mp wird unter der Bedingung ri===0 gebildet und nur bei ri===2 ausgegeben.
ri===0 und ri===2 schliessen einander aus -> val ist bei ri===2 immer "".
Die Spalte "Pausenzeiten von - bis" bleibt zusaetzlich in JEDER Zeile leer.

=========================== BEFUND 3 (GELD) ===============================
Die Wochen-Stundenbestaetigung kennt keine Feiertage.

    Z.24554   const regelH=38.5;const diff=weekTotal-regelH;

38,5 ist hart. _isATFeiertag existiert seit v3.9.106 und kennt seit v3.9.875
den 26.10. - dieses Dokument ruft die Funktion nicht auf. Gemessen an einem
echten Datum: der 26.10.2026 ist ein MONTAG (dow=1). Ein Monteur, der in
dieser Woche Di-Fr voll arbeitet, hat 30,0 h. Das Blatt druckt

    "eventuelle Minderstunden: 8,5h"

und er unterschreibt es. Richtig waere 38,5 - 8,5 = 30,0 Sollstunden, also 0.
Die Rechnung ueber _kvTagesnorm ergibt fuer eine normale Woche exakt 38,5
(8,5*4 + 4,5) - der Ersatz ist verhaltensgleich, ausser am Feiertag.

=========================== BEFUND 4 (GELD) ===============================
Die Tages-Stundenbestaetigung rechnet Mehrstunden gegen hart 8,5 h.

    Z.24655   ${dt>8.5?"eventuelle Mehrstunden: "+_n(dt-8.5,1)+"h":...}

Die Tagesnorm ist laut _kvTagesnorm (Z.2296) Mo-Do 8,5 / Fr 4,5 /
Sa,So,Feiertag 0. Ein Monteur mit 8,0 h am FREITAG hat 3,5 h ueber der
Tagesnorm; das Blatt druckt "eventuelle Mehrstunden:" ohne Zahl. Am Samstag
sind alle Stunden Mehrstunden; das Blatt schweigt bis 8,5 h.

=========================== BEFUND 5 (Widerspruch) ========================
Die Tages-Stundenbestaetigung widerspricht sich auf demselben Blatt.

    Z.24604   const pauseStr=pauseH===0.5?"12:00 Uhr  - 12:30 Uhr":"12:00 Uhr  - 13:00 Uhr";
    Z.24621   ...>${pauseH} Stunde</td>...Mittagspause: ${pauseStr}<...   (Pausenzeile)
    Z.24653   ...>Mittagspause: 12.00 Uhr - 13.00 Uhr</td>                (Summenzeile)

Bei pause=0,5 steht oben "0.5 Stunde / Mittagspause: 12:00 - 12:30" und
darunter "Mittagspause: 12.00 Uhr - 13.00 Uhr". Ein Blatt, zwei Pausen.

=========================== BEFUND 6 (Abschneiden) ========================
Der Fuss des PZE-Monatsblatts laeuft ueber die Seite hinaus.

Format: A4 QUER -> 297 x 210 mm. Der Seiten-Fuss steht auf y=203 (v3.9.853
hat ihn dort von 290 heruntergeholt). Der Waechter vor dem Schlussblock:

    Z.11805   if(y>188){doc.addPage();y=20;}

Danach verbraucht der Block, nachgerechnet an den Zuwaechsen im Code:

    y            MONATSSUMME-Zeile          (Z.11806-11808)
    y+9          Entfernungszulage je Stufe (Z.11809 y+=9,  Z.11812)
    y+14         Summe Entfernungszulage    (Z.11813 y+=5,  Z.11814)
    y+20         Hinweiszeile 1             (Z.11815 y+=6,  Z.11816)
    y+23.5       Hinweiszeile 2             (Z.11817 ...,M,y+3.5)
    y+27         Hinweiszeile 3             (Z.11818 ...,M,y+7)

Der Waechter laesst y=188 durch. 188+27 = 215 > 210 mm Seitenhoehe:
Hinweiszeile 2 (211,5) und 3 (215) sind AUSSERHALB des Blattes, und die
fett gesetzte Zeile "Summe Entfernungszulage: X EUR" landet auf y=202 -
1 mm ueber dem Seiten-Fuss auf y=203, also uebereinander gedruckt.
Der Waechter muss bei y>172 greifen (203 - 27 - 4 mm Luft).

=========================== BEFUND 7 (Beleg) ==============================
Seite 2 des PZE-Monatsblatts traegt weder Mitarbeiter noch Zeitraum.

Der gruene Kopfbalken mit Name + Zeitraum wird EINMAL gezeichnet (Z.11720ff,
vor der Seitenschleife). head() wiederholt nur die Spaltenkoepfe. Der
Seiten-Fuss (Z.11820) traegt Datum, Firma und "x/y" - aber keinen Namen.
Ein einzelnes Folgeblatt ist keinem Mitarbeiter und keinem Monat zuzuordnen.

=========================== BEFUND 8 (GELD) ===============================
Halber Monat: _pzeBuildRows (Z.11676) iteriert den ganzen Monat und vergibt
Soll ueber _kvTagesnorm, ohne worker.eintritt zu beachten - obwohl _pzePdf
das Eintrittsdatum in den Kopf DRUCKT (Z.11758). Wer am 15. eintritt, bekommt
fuer die ersten 14 Tage Sollstunden und damit ein Minus-Saldo, das es nicht
gibt. Ein Austrittsdatum kennt der Code gar nicht.

=========================== WIDERLEGT =====================================
(a) "Inline korrigierte Stunden lassen von/bis stehen" - BESTAETIGT fuer
    updateEntryHours (Z.24364: hours:newHours, von/bis unveraendert
    weitergereicht), aber WIDERLEGT fuer addEntry/_startEditEntry: dort
    werden die Stunden aus von/bis NEU berechnet (Z.24447
    _wrapHrs(_rVon,_rBis)-addPause). Der Widerspruch entsteht also nur ueber
    den Inline-Zahlenfeld-Pfad, nicht ueber das Formular.
(b) "_ezEffTage zaehlt einen geflaggten Tag ohne Stunden nicht" - WIDERLEGT.
    Z.11288-11290 bildet ausdruecklich die VEREINIGUNG aus Anwesenheitstagen
    und geflaggten Tagen. Kein Befund.
(c) "Irgendwo steht eine zweite Feiertagsliste" - WIDERLEGT. _isATFeiertag
    ist die einzige Quelle; alle vier Aufrufer gehen darueber. Der Mangel ist
    nicht eine zweite Liste, sondern ein Dokument OHNE Liste (Befund 3/4).

ZUSTAND DIESER DATEI: Die Riegel zu Befund 1-7 sind ROT, solange der Patch
fehlt. Das ist beabsichtigt - sie beschreiben den Sollzustand. Gruen sind die
Riegel, die den heutigen Bestand festhalten (Feiertags-Einquelligkeit,
_ezEffTage-Vereinigung, die Neuberechnung im Formular-Pfad) sowie die
Umkehrprobe am Ende.
"""
import os
import re
import pytest
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import _extract_fn  # noqa: E402


# ───────────────────────── Hilfen ─────────────────────────

def _wochen_stz(index_html):
    fn = _extract_fn(index_html, "exportWochenStz",
                     r"const\s+exportWochenStz\s*=\s*\(")
    assert fn, "exportWochenStz nicht gefunden - Anker veraltet"
    return fn


def _tages_stz(index_html):
    fn = _extract_fn(index_html, "exportTagesStz",
                     r"const\s+exportTagesStz\s*=\s*\(")
    assert fn, "exportTagesStz nicht gefunden - Anker veraltet"
    return fn


def _pze_pdf(index_html):
    fn = _extract_fn(index_html, "_pzePdf")
    assert fn, "_pzePdf nicht gefunden - Anker veraltet"
    return fn


# ───────────── BEFUND 1: GE kommt aus dem falschen Eintrag ─────────────

def test_gehen_stammt_vom_letzten_eintrag_des_tages(index_html):
    """Ein Kommen ohne Gehen ist kein Nachweis. Bei EINER Buchung am Tag -
    dem Normalfall - ist arr[1] undefined und "GE:" bleibt leer."""
    fn = _wochen_stz(index_html)
    assert 'const ge=e&&e.bis?esc(e.bis):"";' not in fn, (
        "GE: wird weiterhin aus arr[ri] gelesen und erst bei ri===1 gedruckt.\n"
        "Bei einer einzigen Buchung am Tag druckt das unterschriebene Blatt\n"
        "ein Kommen OHNE Gehen; bei drei Buchungen das Ende der zweiten."
    )
    assert re.search(r"arr\[arr\.length\s*-\s*1\]", fn), (
        "Das Gehen muss vom LETZTEN Eintrag des Tages kommen - sonst steht auf\n"
        "dem Blatt nicht, wann der Monteur gegangen ist."
    )


def test_kommen_stammt_vom_ersten_eintrag_des_tages(index_html):
    """Gegenstueck: das Kommen darf nicht mitwandern, wenn GE umgestellt wird."""
    fn = _wochen_stz(index_html)
    assert re.search(r"arr\[0\]", fn), (
        "Das Kommen muss ausdruecklich aus arr[0] kommen, nicht aus der\n"
        "laufenden Schleifenvariablen."
    )


# ───────────── BEFUND 2: MP druckt immer einen leeren Wert ─────────────

def test_mittagspause_hat_einen_wert(index_html):
    """ri===0 && ... , ausgegeben bei ri===2. Das kann nie zutreffen."""
    fn = _wochen_stz(index_html)
    assert 'const mp=ri===0&&i<5?"12:00-13:00":"";' not in fn, (
        "mp wird unter ri===0 gebildet und bei ri===2 gedruckt - die beiden\n"
        "Bedingungen schliessen einander aus. Die Zeile 'MP:' steht seit jeher\n"
        "ohne Wert auf dem Blatt."
    )


@pytest.mark.xfail(strict=True, reason=(
    "OFFEN, Entscheidung Sebastian - kein Fehler im Fix, sondern eine Regelfrage. "
    "Wochenblatt: eine Pausenspalte fuer eine ganze Woche ist strukturell falsch - der vorgeschlagene Fix liest nur den Montag. Das braucht eine Pausenspalte JE TAG. Entscheidung Sebastian, Handoff 28.08. Abschnitt 3."))
def test_pausenzeiten_spalte_ist_nicht_durchgehend_leer(index_html):
    """Die Vorlage hat eine Spalte 'Pausenzeiten von - bis'. Sie wird in beiden
    Zweigen als leeres <td> gerendert - eine Spaltenueberschrift ohne Inhalt."""
    fn = _wochen_stz(index_html)
    leere_tds = fn.count('font-size:9pt;width:80px;"></td>') + \
        fn.count('font-size:9pt;"></td>')
    assert leere_tds == 0, (
        "Die Spalte 'Pausenzeiten von - bis' wird in jeder Zeile leer gedruckt\n"
        f"({leere_tds} leere Zellen). Der Pausenwert liegt im Eintrag (e.pause)\n"
        "und wird nicht verwendet."
    )


# ───────────── BEFUND 3: Wochensoll ohne Feiertag ─────────────

def test_wochensoll_beruecksichtigt_feiertage(index_html):
    fn = _wochen_stz(index_html)
    assert "const regelH=38.5;" not in fn, (
        "regelH ist hart 38,5. Am 26.10. (Nationalfeiertag, 2026 ein Montag)\n"
        "druckt das Blatt 'eventuelle Minderstunden: 8,5h' fuer einen Monteur,\n"
        "der die ganze Woche gearbeitet hat - und er unterschreibt es."
    )
    assert "_isATFeiertag" in fn or "_kvTagesnorm" in fn, (
        "Die Wochen-Stundenbestaetigung ruft weder _isATFeiertag noch\n"
        "_kvTagesnorm auf. Sie ist das einzige Lohn-Dokument ohne Feiertagslogik."
    )


def test_kvtagesnorm_ergibt_fuer_eine_normale_woche_exakt_385(node_exe, index_html):
    """Beweis, dass der Ersatz fuer regelH=38.5 verhaltensgleich ist - ausser
    am Feiertag. 8,5*4 + 4,5 = 38,5. Ohne diesen Beleg waere der Vorschlag
    eine Verhaltensaenderung an einer Geld-Zahl."""
    from conftest import run_node_snippet
    norm = _extract_fn(index_html, "_kvTagesnorm")
    assert norm, "_kvTagesnorm nicht gefunden"
    out = run_node_snippet(node_exe, norm + """
let s=0;for(let dow=1;dow<=5;dow++)s+=_kvTagesnorm(dow,false);
s+=_kvTagesnorm(6,false)+_kvTagesnorm(0,false);
let f=0;for(let dow=1;dow<=5;dow++)f+=_kvTagesnorm(dow,dow===1);
console.log(JSON.stringify({normal:s,mitFeiertagMo:f}));
""")
    import json
    r = json.loads(out)
    assert r["normal"] == 38.5, (
        f"_kvTagesnorm summiert die Woche auf {r['normal']} statt 38,5 - dann "
        "waere der Ersatz fuer regelH KEINE reine Feiertagskorrektur."
    )
    assert r["mitFeiertagMo"] == 30.0, (
        f"Feiertags-Montag: {r['mitFeiertagMo']} statt 30,0."
    )


def test_nationalfeiertag_2026_ist_ein_montag(node_exe, index_html):
    """Die Messung hinter Befund 3 - kein erfundenes Datum."""
    from conftest import run_node_snippet
    fei = _extract_fn(index_html, "_isATFeiertag")
    ost = _extract_fn(index_html, "_easterSunday")
    assert fei and ost
    out = run_node_snippet(node_exe, ost + fei + """
const d=new Date(2026,9,26);
console.log(JSON.stringify({dow:d.getDay(),feiertag:_isATFeiertag(d)}));
""")
    import json
    r = json.loads(out)
    assert r["feiertag"] is True, "Der 26.10.2026 gilt nicht als Feiertag (v3.9.875-Regression)."
    assert r["dow"] == 1, f"26.10.2026 hat dow={r['dow']}, erwartet 1 (Montag)."


# ───────────── BEFUND 4: Tagesnorm hart 8,5 ─────────────

def test_tagesnorm_folgt_dem_wochentag(index_html):
    fn = _tages_stz(index_html)
    assert 'dt>8.5?"eventuelle Mehrstunden: "' not in fn, (
        "Die Tages-Stundenbestaetigung misst gegen hart 8,5 h. Freitag-Norm ist\n"
        "4,5 h (_kvTagesnorm), Samstag/Sonntag/Feiertag 0. 8 h am Freitag sind\n"
        "3,5 h ueber der Norm - das Blatt druckt eine leere Mehrstunden-Zeile."
    )


# ───────────── BEFUND 5: zwei Pausen auf einem Blatt ─────────────

def test_summenzeile_druckt_dieselbe_pause_wie_die_pausenzeile(index_html):
    fn = _tages_stz(index_html)
    assert "const pauseStr=" in fn, "pauseStr ist weg - Anker veraltet."
    assert '>Mittagspause: 12.00 Uhr - 13.00 Uhr</td>' not in fn, (
        "Die Summenzeile schreibt die Mittagspause hart 12.00-13.00, waehrend\n"
        "die Pausenzeile darueber pauseStr aus e.pause bildet. Bei pause=0,5\n"
        "behauptet dasselbe Blatt zwei verschiedene Pausen."
    )


# ───────────── BEFUND 6: Fuss laeuft ueber die Querformat-Seite ─────────────

def _pze_fuss_mass(index_html):
    """Liest die Zuwaechse des Schlussblocks AUS DER DATEI, nicht aus dem Kopf."""
    fn = _pze_pdf(index_html)
    # v3.9.879: zwischen flush() und dem Waechter darf ein Kommentar stehen. Die
    # erste Fassung verlangte sie direkt nebeneinander und wurde rot, als der Fix
    # seine Begruendung dazwischenschrieb - derselbe Fehler wie das feste
    # Zeichenfenster in test_juprowa_selfheal_v755. Ein Riegel darf nicht an
    # Kommentartext haengen; das "flush();" davor bleibt noetig, um den Schluss-
    # Waechter vom gleichlautenden Waechter INNERHALB der Zeilenschleife zu trennen.
    m = re.search(r"flush\(\);(?:\s|/\*.*?\*/)*if\(y>(\d+(?:\.\d+)?)\)\{doc\.addPage\(\);y=20;\}", fn, re.S)
    assert m, "Waechter vor dem Schlussblock nicht gefunden - Anker veraltet."
    guard = float(m.group(1))
    rest = fn[m.end():]
    zuw = [float(x) for x in re.findall(r"y\+=(\d+(?:\.\d+)?);", rest)]
    off = [float(x) for x in re.findall(r",M,y\+(\d+(?:\.\d+)?)\)", rest)]
    fuss = re.search(r"doc\.text\(_pdfStr\('Generiert am.*?\),M,(\d+(?:\.\d+)?)\)", rest)
    assert fuss, "Seiten-Fuss-Position nicht gefunden."
    return guard, sum(zuw), (max(off) if off else 0.0), float(fuss.group(1))


def test_schlussblock_passt_auf_die_querformat_seite(index_html):
    """A4 quer = 210 mm hoch. Der Waechter laesst y=188 durch, der Block
    braucht danach 27 mm."""
    guard, zuwachs, letzter_offset, fuss_y = _pze_fuss_mass(index_html)
    bedarf = zuwachs + letzter_offset
    assert bedarf > 0, "Schlussblock verbraucht 0 mm - Messung kaputt."
    assert guard + bedarf <= 210.0, (
        f"Waechter y>{guard} + {bedarf} mm Schlussblock = {guard + bedarf} mm.\n"
        "Die Querformat-Seite ist 210 mm hoch. Die letzten Hinweiszeilen des\n"
        "Lohn-Uebergabeblatts stehen ausserhalb des Papiers."
    )


def test_schlussblock_kollidiert_nicht_mit_dem_seitenfuss(index_html):
    """Der Seiten-Fuss steht fest auf y=203. Alles darueber muss darueber
    bleiben - sonst druckt 'Summe Entfernungszulage' auf 'Generiert am'."""
    guard, zuwachs, letzter_offset, fuss_y = _pze_fuss_mass(index_html)
    bedarf = zuwachs + letzter_offset
    assert guard + bedarf <= fuss_y - 4.0, (
        f"Waechter y>{guard}, Schlussblock {bedarf} mm, Seiten-Fuss y={fuss_y}.\n"
        f"Groesstes y des Blocks = {guard + bedarf} mm.\n"
        f"Der Waechter muesste bei y>{fuss_y - bedarf - 4.0} greifen."
    )


# ───────────── BEFUND 7: Folgeseite ohne Mitarbeiter/Zeitraum ─────────────

def test_jede_seite_nennt_mitarbeiter_und_zeitraum(index_html):
    """Der gruene Kopfbalken wird einmal gezeichnet, head() wiederholt nur die
    Spaltenkoepfe. Ein loses Blatt 2 gehoert dann zu niemandem."""
    fn = _pze_pdf(index_html)
    m = re.search(r"for\(var pi=1;pi<=pc;pi\+\+\)\{(.*?)doc\.save\(", fn, re.S)
    assert m, "Seiten-Fuss-Schleife nicht gefunden - Anker veraltet."
    fuss = m.group(1)
    assert "worker.name" in fuss, (
        "Der Seiten-Fuss traegt den Mitarbeiternamen nicht. Blatt 2 des\n"
        "Personalzeit-Monatsblatts ist damit keinem Mitarbeiter zuzuordnen -\n"
        "als Lohnbeleg wertlos."
    )
    assert ("von" in fuss and "bis" in fuss), (
        "Der Seiten-Fuss nennt den Zeitraum nicht."
    )


# ───────────── BEFUND 8: halber Monat ─────────────

@pytest.mark.xfail(strict=True, reason=(
    "OFFEN, Entscheidung Sebastian - kein Fehler im Fix, sondern eine Regelfrage. "
    "PZE-Monatsblatt rechnet Sollstunden fuer den ganzen Monat, auch bei Eintritt am 15. (~60h Minus-Saldo, den es nicht gibt); ein Austrittsdatum kennt der Code gar nicht. Braucht eine Entscheidung, wie Teilmonate zu behandeln sind. Handoff 28.08."))
def test_eintritt_begrenzt_das_soll(index_html):
    """_pzePdf DRUCKT das Eintrittsdatum, _pzeBuildRows RECHNET ohne es."""
    pdf = _pze_pdf(index_html)
    assert "worker.eintritt" in pdf, "Eintritt wird nicht mehr gedruckt - Anker veraltet."
    rows = _extract_fn(index_html, "_pzeBuildRows")
    assert rows, "_pzeBuildRows nicht gefunden"
    assert "eintritt" in rows, (
        "_pzeBuildRows kennt worker.eintritt nicht und vergibt Sollstunden auch\n"
        "fuer Tage VOR dem Eintritt. Ein Monteur, der am 15. anfaengt, sieht auf\n"
        "seinem Monatsblatt ein Minus-Saldo von rund 60 h, das es nicht gibt.\n"
        "Das Eintrittsdatum steht dabei im Kopf DESSELBEN Blattes."
    )


# ───────────── Vollstaendigkeit als Beleg (e) ─────────────

def test_stundenbestaetigung_nennt_die_firma(index_html):
    """Ein Blatt mit Unterschriftsfeld, aber ohne Aussteller, taugt nicht als
    Nachweis. Die uebrigen Druckstuecke nutzen COMPANY_FOOTER/CF_HTML_LINE1."""
    for name, fn in (("Woche", _wochen_stz(index_html)),
                     ("Tag", _tages_stz(index_html))):
        assert ("COMPANY_FOOTER" in fn or "CF_HTML_LINE1" in fn
                or "Kolar" in fn), (
            f"Die {name}-Stundenbestaetigung nennt nirgends den Aussteller.\n"
            "Sie hat ein Unterschriftsfeld, aber keinen Briefkopf - anders als\n"
            "exportMonat (Z.22475/22543), das COMPANY_FOOTER + UID fuehrt."
        )


def test_stundenbestaetigung_traegt_ein_erstellungsdatum(index_html):
    for name, fn in (("Woche", _wochen_stz(index_html)),
                     ("Tag", _tages_stz(index_html))):
        assert "Erstellt" in fn or "new Date()" in fn, (
            f"Die {name}-Stundenbestaetigung nennt kein Erstellungsdatum.\n"
            "Zwei Fassungen derselben Woche sind dann nicht unterscheidbar."
        )


def test_leere_woche_wird_nicht_stumm_exportiert(index_html):
    """Grenzfall (f): eine Woche ohne Eintraege erzeugt heute ein vollstaendiges
    Blatt mit 'Wochenstunden 0,0' und 'eventuelle Minderstunden: 38,5h' - mit
    Unterschriftsfeld. exportFahrtenPdf (Z.26186) macht es richtig vor."""
    fn = _wochen_stz(index_html)
    assert re.search(r"weekTotal\s*(<=|===)\s*0|!weekTotal|Keine\s+(Eintr|Stunden)", fn), (
        "exportWochenStz hat keinen Leer-Waechter. Eine leere Woche laeuft als\n"
        "unterschriftsreifes Blatt mit -38,5 h heraus."
    )


def test_unbekannter_mitarbeiter_wird_nicht_gedruckt(index_html):
    """wName faellt auf 'Unbekannt' zurueck - und wandert so in Blatt UND
    Dateinamen eines Dokuments, das unterschrieben wird. Erwartet wird ein
    Waechter VOR der wName-Zeile, nicht das Entfernen des Fallbacks."""
    fn = _wochen_stz(index_html)
    kopf = fn.split('const wName=')[0]
    assert '||"Unbekannt"' not in fn or "return;" in kopf, (
        "Findet sich der gewaehlte Monteur nicht in monteure, druckt das Blatt\n"
        "'Monteur: Unbekannt' und speichert es als Stundenbestaetigung_Woche_\n"
        "Unbekannt_KWxx.xls. Vor der wName-Zeile fehlt jeder Waechter."
    )


# ───────────── Bestand festhalten (diese Riegel sind GRUEN) ─────────────

def test_feiertage_haben_genau_eine_quelle(index_html):
    """(c) geprueft: keine zweite Liste, kein zweiter Kalender. Wer eine
    Feiertagsliste dupliziert, faellt hier auf."""
    listen = re.findall(r"\[\s*\[1,1\]\s*,\s*\[1,6\]", index_html)
    assert len(listen) == 1, (
        f"{len(listen)} feste Feiertagslisten gefunden. Es darf genau eine\n"
        "geben (_isATFeiertag Z.4570) - sonst kennt die eine den 26.10. und\n"
        "die andere nicht, wie vor v3.9.875."
    )
    assert index_html.count("function _isATFeiertag") == 1


def test_ez_zaehlt_auch_tage_ohne_stunden(index_html):
    """(Widerlegt) Ein per Kalender vergebener Zulagen-Tag OHNE Zeitbuchung
    faellt NICHT aus der Abrechnung - _ezEffTage bildet die Vereinigung."""
    fn = _extract_fn(index_html, "_ezEffTage")
    assert fn, "_ezEffTage nicht gefunden"
    assert "Object.keys(m).forEach(take)" in fn.replace(" ", "").replace(
        "Object.keys(m).forEach(take);", "Object.keys(m).forEach(take)"), \
        "Anwesenheitstage werden nicht mehr gezaehlt."
    assert re.search(r"Object\.keys\(f\)\.forEach", fn), (
        "Die geflaggten Tage werden nicht mehr mitgezaehlt. Dann verliert ein\n"
        "per Kalender vergebener Zulagentag ohne Zeitbuchung sein Geld."
    )


def test_formularpfad_rechnet_die_stunden_aus_von_bis_neu(index_html):
    """(Teil-Widerlegung zu (a)) Ueber das Formular kann der Widerspruch
    'Stunden neben von/bis' NICHT entstehen - die Stunden folgen den Zeiten."""
    fn = _extract_fn(index_html, "addEntry", r"const\s+addEntry\s*=\s*async\s*\(")
    assert fn, "addEntry nicht gefunden"
    assert "_wrapHrs(_rVon,_rBis)-addPause" in fn, (
        "Die Neuberechnung der Stunden aus von/bis ist weg. Dann kann auch das\n"
        "Formular ein 'hours', das den gedruckten Zeiten widerspricht, speichern."
    )


@pytest.mark.xfail(strict=True, reason=(
    "OFFEN, Entscheidung Sebastian - kein Fehler im Fix, sondern eine Regelfrage. "
    'Inline-Stundenkorrektur schreibt nur hours und laesst von/bis stehen -> 6 Stunden neben 07:00 / 16:00 auf dem unterschriebenen Blatt. Ob von/bis mitgezogen oder die Abweichung aufs Blatt gedruckt werden soll, ist eine Entscheidung. Handoff 28.08.'))
def test_inline_korrektur_hinterlaesst_keinen_widerspruch(index_html):
    """(a) - der EINE Pfad, ueber den der Widerspruch entsteht. ROT bis zum
    Patch: updateEntryHours schreibt hours und reicht von/bis unveraendert
    weiter. Danach steht auf dem Blatt '6' neben '07:00 / 16:00'."""
    fn = _extract_fn(index_html, "updateEntryHours",
                     r"const\s+updateEntryHours\s*=\s*\(")
    assert fn, "updateEntryHours nicht gefunden"
    assert 'von:entry.von||"",bis:entry.bis||""' not in fn, (
        "updateEntryHours schreibt nur hours und laesst von/bis stehen.\n"
        "Die Wochen-Stundenbestaetigung druckt danach die neue Tagessumme\n"
        "neben den alten Zeiten - ein Widerspruch auf einem Blatt, das der\n"
        "Monteur unterschreibt.\n"
        "Entweder von/bis mitfuehren (bis = von + hours + pause) oder auf dem\n"
        "Blatt kennzeichnen."
    )


@pytest.mark.xfail(strict=True, reason=(
    "OFFEN, Entscheidung Sebastian - kein Fehler im Fix, sondern eine Regelfrage. "
    "Dieselbe Stelle: der >0-Zweig aktualisiert dayEntries, aber nicht entries - Stundenbestaetigung und Zulagen-PDF laufen bis zum Neuladen auseinander. Gehoert mit der Zeile darueber zusammen entschieden. Handoff 28.08."))
def test_inline_korrektur_meldet_die_neuen_stunden_zurueck(index_html):
    """Zweite Haelfte desselben Pfades: der >0-Zweig aktualisiert dayEntries,
    aber NICHT die App-weite entries-Liste. Die Wochen-Stundenbestaetigung
    (dayEntries) und das PZE-/Zulagen-PDF (entries) zeigen danach fuer
    denselben Tag verschiedene Stunden, bis die App neu laedt."""
    fn = _extract_fn(index_html, "updateEntryHours",
                     r"const\s+updateEntryHours\s*=\s*\(")
    assert fn
    m = re.search(r"if\(entry\.id&&newHours>0\)\{(.*?)\}else if", fn, re.S)
    assert m, "Der >0-Zweig ist weg - Anker veraltet."
    assert "setEntries" in m.group(1), (
        "Der >0-Zweig ruft setEntries nicht. dayEntries (Quelle der\n"
        "Stundenbestaetigung) und entries (Quelle von _pzePdf, KVZulagenReport,\n"
        "exportMonat, Bauwochenbericht) laufen auseinander."
    )


# ───────────── Umkehrprobe ─────────────

def test_umkehrprobe_die_riegel_schlagen_beim_rueckbau_an(index_html):
    """Ein Riegel, der bei zerstoertem Bestand gruen bleibt, misst nichts.
    Hier wird der Bestand absichtlich kaputtgemacht und geprueft, dass die
    Messung das merkt."""
    # 1) Feiertags-Einquelligkeit: zweite Liste einschmuggeln
    kaputt = index_html.replace("const fixed=[[1,1],[1,6]",
                                "const fixed2=[[1,1],[1,6]];const fixed=[[1,1],[1,6]", 1)
    assert kaputt != index_html, "Rueckbau griff nicht - Anker veraltet."
    assert len(re.findall(r"\[\s*\[1,1\]\s*,\s*\[1,6\]", kaputt)) == 2, (
        "Umkehrprobe: eine zweite Feiertagsliste wuerde NICHT auffallen."
    )

    # 2) Seiten-Mass: Waechter noch weiter hochsetzen -> muss durchfallen
    fn = _pze_pdf(index_html)
    m = re.search(r"flush\(\);(?:\s|/\*.*?\*/)*if\(y>(\d+(?:\.\d+)?)\)", fn, re.S)
    assert m, "Waechter-Anker veraltet."
    guard = float(m.group(1))
    _, zuwachs, letzter_offset, fuss_y = _pze_fuss_mass(index_html)
    bedarf = zuwachs + letzter_offset
    assert (guard + 20) + bedarf > 210.0, (
        "Umkehrprobe: selbst ein um 20 mm zu hoher Waechter wuerde die "
        "Seitenmessung nicht ausloesen - dann misst sie nichts."
    )
    # und die Gegenrichtung: ein korrekter Waechter waere gruen
    korrekt = fuss_y - bedarf - 4.0
    assert korrekt + bedarf <= fuss_y - 4.0, (
        "Umkehrprobe: der vorgeschlagene Waechter-Wert faellt selbst durch - "
        "dann ist der Vorschlag falsch."
    )

    # 3) GE-Riegel: den ALTEN Zustand rekonstruieren und pruefen, dass er rot wird.
    #    v3.9.879: bis der Fix drin war, hat dieser Block ihn VORWAERTS angewandt -
    #    danach war er ein No-Op und schlug fehl. Eine Umkehrprobe muss zurueckbauen,
    #    nicht vorwaertsbauen, sonst prueft sie nach dem Fix nichts mehr.
    heute = _wochen_stz(index_html)
    assert re.search(r'arr\[arr\.length\s*-\s*1\]', heute), (
        "GE wird nicht mehr aus dem LETZTEN Eintrag des Tages gelesen - dann weist "
        "das unterschriebene Blatt bei einer Buchung je Tag ein Kommen ohne Gehen aus."
    )
    zurueck = heute.replace('const _eL=arr.length?arr[arr.length-1]:null;'
                            'const ge=(_eL&&_eL.bis)?esc(_eL.bis):"";',
                            'const ge=e&&e.bis?esc(e.bis):"";', 1)
    assert zurueck != heute, "Rueckbau griff nicht - Anker veraltet."
    assert not re.search(r'arr\[arr\.length\s*-\s*1\]', zurueck), (
        "Umkehrprobe: der GE-Riegel wuerde am alten Stand nicht anschlagen."
    )
