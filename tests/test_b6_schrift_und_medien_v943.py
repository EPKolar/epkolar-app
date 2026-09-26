# -*- coding: utf-8 -*-
"""v3.9.943 - Schriftgroessen unter 10 px, die Wetterkarte, die Medienmulden.

WAS AM SCHIRM GEMESSEN WURDE (und was diese Datei davon halten kann)
────────────────────────────────────────────────────────────────────
Die Befunde kommen von scripts/b3_vier_ansichten_messen.py bei 375, 390 und
1440 px (zwoelf Laeufe, alle acht Koeder angeschlagen),
scripts/b3_home390_beschnitt.py und scripts/bottom_reserve_messen.py. Diese
Datei liest Quelltext und kann das nicht nachstellen - sie haelt die URSACHEN
fest, damit ein spaeteres "Aufraeumen" auffaellt.

    Schrift unter 12 px, Home:       390 px 78 -> 69   |  1440 px 120 -> 111
    Schrift unter 12 px, Werkzeuge:  390 px 60 -> 55   |  1440 px  32 ->  25
    Beschnitt auf Home bei 390 px:   5 -> 11 -> 5
        Der Zwischenwert ist wichtig: nachdem die 7-px-Schrift gehoben war,
        passte die Wetterzeile nicht mehr (sieben Zellen auf 374 px lassen je
        46 px, "Bedeckt" braucht bei 12 px rund 48). Erst die Kuerzung auf vier
        Tage am Telefon brachte es zurueck auf die fuenf vorbestehenden
        Stellen. Der Weg "Schrift wieder kleiner machen" war ausdruecklich
        nicht gewollt.
    Fussleiste nach dem Schriftwechsel: 58 px, unveraendert, 0 verdeckte
        Bedienelemente von 128 in sechs Ansichten. --epk-bar-h muss also NICHT
        nachwandern - das war zu messen, nicht zu glauben.
    Planflaeche im Hellmodus (voller Durchgang, 31 Ansichten):
        390 px 57,5 % -> 7,6 % des Schirms | 1440 px 72,7 % -> 5,1 %
        Dunkelmodus ziffergleich 85,1 % / 100,0 % - die Gegenprobe zu
        "bleibt bytegleich".
"""
import io
import re

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]


def _roh():
    return io.open(str(WURZEL / "index.html"), encoding="utf-8",
                   newline="").read()


def _code_feld(roh):
    import sys
    sys.path.insert(0, str(WURZEL / "scripts"))
    from code_scan import ist_code, eichen
    ok, gefunden, erwartet = eichen(roh)
    assert ok, ("Die Eichung von code_scan ist gescheitert (%d von %d) - ohne "
                "sie sagt keine Zaehlung hier etwas." % (gefunden, erwartet))
    return ist_code(roh)


# ── Alles unter 10 px ─────────────────────────────────────────────────────

def test_keine_schriftgroesse_unter_zehn_px_im_code():
    """36 Codestellen standen auf 7 oder 8 px - Groessen, die man nicht mehr
    liest, nicht bloss schwer. Der kleinste Wert der ganzen App war 7 px.

    Der KOEDER sind die 9er und die 11er: die gibt es weiter (absichtlich, sie
    sind ein eigener Schritt). Findet der Zaehler die nicht, ist seine Null bei
    7 und 8 kein Befund, sondern sein eigener Ausfall.
    """
    roh = _roh()
    feld = _code_feld(roh)

    def zaehl(rx):
        return [m.start() for m in re.finditer(rx, roh) if feld[m.start()]]

    koeder = {"9": len(zaehl(r"fontSize:9(?![\d.])")),
              "11": len(zaehl(r"fontSize:11(?![\d.])"))}
    assert all(v > 0 for v in koeder.values()), (
        "KOEDER STUMM: %r. Der Zaehler findet die 9er und 11er nicht mehr - "
        "dann ist seine Null bei 7 und 8 keine Aussage. (Sind sie absichtlich "
        "alle gehoben worden, muss der Koeder hier nachgezogen werden.)"
        % koeder)

    klein = zaehl(r"fontSize:(?:isMob\?7:[89]|[78])(?![\d.])")
    assert not klein, (
        "%d Codestellen stehen wieder auf 7 oder 8 px (Positionen %s). "
        "UI.fMeta (12) ist der Boden der App." % (len(klein), klein[:6]))


def test_die_dezimalgroessen_sind_unberuehrt():
    """Mein erster Griff nahm `fontSize:[789]` und hat dabei `fontSize:9.5`
    zerschnitten - node_check meldete 'Unexpected number', der Griff wurde
    zurueckgenommen. Das Muster braucht (?![\\d.]) hinter der Zahl.

    Dieser Riegel haelt fest, dass die Dezimalwerte noch da sind - sie sind
    der Beleg, dass das Muster eng genug ist.
    """
    roh = _roh()
    feld = _code_feld(roh)
    dez = [m.group(0) for m in re.finditer(r"fontSize:\d+\.\d+", roh)
           if feld[m.start()]]
    assert dez, (
        "Keine Dezimal-Schriftgroesse mehr im Code. Entweder sind sie "
        "absichtlich verschwunden - dann gehoert dieser Riegel angepasst - "
        "oder ein zu weites Muster hat sie zerschnitten.")
    assert "fontSize:9.5" in dez, (
        "fontSize:9.5 ist verschwunden. Genau diesen Wert hat mein erstes, zu "
        "weites Muster zerstoert. Gefunden: %s" % sorted(set(dez)))


# ── Die Wetterkarte ───────────────────────────────────────────────────────

def test_die_wetterkarte_zeigt_am_telefon_weniger_tage():
    """Sieben Zellen auf 374 px lassen je 46 px Inhalt; "Bedeckt" braucht bei
    12 px rund 48 - gemessen als 2 px Beschnitt in einer 44-px-Zelle. Vier
    Zellen geben je etwa 91 px."""
    roh = _roh()
    assert roh.count("slice(0,isMob?4:7)") == 2, (
        "Erwartet zwei Kuerzungen (Live-Block und Ersatzvorrat), gefunden %d. "
        "Kuerzt nur einer, zeigt derselbe Bildschirm sieben gequetschte Zellen, "
        "sobald die Wetterabfrage nicht antwortet - ein Bildschirm mit zwei "
        "Wahrheiten." % roh.count("slice(0,isMob?4:7)"))
    assert ".slice(0,7).map((d,i)=>" not in roh, (
        "Der Live-Block zeigt wieder sieben Tage am Telefon.")


def test_in_der_wetterkarte_steht_nichts_unter_zwoelf():
    """Acht sichtbare Stellen bei 7 px waren der kleinste Wert der Messreihe."""
    roh = _roh()
    i = roh.find('WMO_D[wcode]||""')
    assert i > 0, "KOEDER STUMM: der Live-Wetterblock wurde nicht gefunden."
    block = roh[max(0, i - 1500):i + 400]
    klein = re.findall(r"fontSize:(?:isMob\?)?(\d+)(?::(\d+))?", block)
    zahlen = [int(x) for paar in klein for x in paar if x]
    assert zahlen, "KOEDER STUMM: keine Schriftgroesse im Wetterblock gefunden."
    assert min(zahlen) >= 12, (
        "In der Wetterkarte steht wieder %d px. Gefunden: %s"
        % (min(zahlen), sorted(zahlen)))


# ── Die Fussleiste ────────────────────────────────────────────────────────

def test_die_fussleiste_ist_nicht_mehr_zehn_px():
    """Die Leiste ist die einzige Flaeche, die in JEDER Ansicht und bei JEDER
    Breite im Bild ist. Gemessen nach dem Wechsel: Hoehe weiter 58 px, 0
    verdeckte Bedienelemente - --epk-bar-h muss nicht nachwandern."""
    roh = _roh()
    assert ("React.createElement('span', { style: {fontSize:10,"
            "fontWeight:isActive?700:400}}") not in roh, (
        "Die Beschriftungen der Fussleiste stehen wieder auf 10 px.")
    assert ("React.createElement('span', { style: {fontSize:UI.fMeta,"
            "fontWeight:isActive?700:400}}") in roh, (
        "Die Beschriftung der Fussleiste haengt nicht an UI.fMeta.")


def test_die_leistenhoehe_ist_weiter_an_ein_token_gebunden():
    """Waechst die Leiste ohne --epk-bar-h, verschwindet das letzte
    Bedienelement darunter (die Endreserve haengt seit v3.9.932 daran)."""
    roh = _roh()
    assert "--epk-bar-h:58px" in roh, "--epk-bar-h ist weg oder anders."
    assert "min-height:var(--epk-bar-h,58px)" in roh, (
        "Die Leiste bezieht ihre Hoehe nicht mehr aus dem Token.")


# ── Die Medienmulden ──────────────────────────────────────────────────────

def test_die_drei_lebenden_medienmulden_folgen_dem_thema():
    """Derselbe Bauteil wie der grosse Plan-Betrachter aus v3.9.942: eine
    Mulde mit genau einem Bild darin. Gemessen war die Planvorschau im
    Hellmodus bei 390 px zu 14,2 Prozent des Schirms dunkel (Letterbox-Balken
    neben dem Planblatt) - unter der Urteilsschwelle von 25 Prozent, aber
    sichtbar. Es waere eine Regel zu viel, wenn der Betrachter dem Thema folgt
    und die Vorschaukachel DESSELBEN Plans schwarz bleibt."""
    roh = _roh()
    assert roh.count('_dark?"#0a0c14":V.bd') == 3, (
        "Erwartet drei themenabhaengige Medienmulden (Planvorschau, "
        "Fotokachelwand, Fotoliste), gefunden %d."
        % roh.count('_dark?"#0a0c14":V.bd'))


def test_der_tote_zweig_bleibt_und_ist_benannt():
    """PlanViewer wird NIE gerendert - `createElement(PlanViewer,` kommt 0 mal
    vor, gezeichnet wird PlanViewerCanvas. Gemessen: die Farbe erscheint im
    Hellmodus in keinem Element. Toter Code wird hier nicht kosmetisch
    gepflegt, sondern benannt.

    Wird PlanViewer eines Tages doch gerendert, ist die feste Farbe wieder ein
    Befund - dieser Riegel schlaegt dann an.
    """
    roh = _roh()
    gerendert = roh.count("createElement(PlanViewer,")
    if gerendert == 0:
        assert 'background:"#0a0c14"' in roh, (
            "Die feste Farbe im toten PlanViewer-Zweig ist verschwunden. Wenn "
            "der Zweig entfernt wurde, ist das in Ordnung - dann gehoert "
            "dieser Riegel weg. Wurde nur die Farbe geaendert, fehlt die "
            "Begruendung.")
        assert "ABSICHTLICH NICHT AUF DAS THEMA UMGESTELLT" in roh, (
            "Die Begruendung am toten Zweig ist weg. Ohne sie sieht die feste "
            "Farbe wie ein vergessener Fall aus.")
    else:
        assert 'background:_dark?"#0a0c14"' in roh or \
               'background:"#0a0c14"' not in roh, (
            "PlanViewer wird jetzt %d mal gerendert - dann ist seine feste "
            "Farbe #0a0c14 ein echter Befund und muss dem Thema folgen, wie "
            "die drei Schwestern." % gerendert)
