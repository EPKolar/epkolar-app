# -*- coding: utf-8 -*-
"""Keine CSS-Regel darf eine Schrift unter 12 px ERZWINGEN.

🔴 WARUM ES DIESEN RIEGEL GIBT - und warum er meinen eigenen einen Commit
spaeter widerlegt hat.

`test_fahrzeuge_schriftgroesse_v965` misst den QUELLTEXT: keine feste
Schriftgroesse unter 12 px in FahrzeugView. Der Riegel ist gruen. Und trotzdem
zeigte die Arbeitsscheinliste 24 Stellen unter 12 px bei 390 px, obwohl ihr
Quelltext NULL solche Werte fuehrt.

Am laufenden Element gemessen: inline `font-size: 12px`, berechnet `10px`.
Inline `13px`, berechnet `11px`. Die Ursache war
`.kpi-grid.epk-leiste > div > div:nth-child(4) { font-size: 10px !important }`.
Eine Regel mit !important uebersteuert JEDE Inline-Angabe - also auch alle 115,
die v3.9.965 gehoben hat. Ein Riegel, der nur den Quelltext liest, bleibt dabei
gruen. Das ist Anwesenheit statt Wirkung, an meinem eigenen Werk.

🔴 UND DER ZWEITE FEHLER, beim ZAEHLEN: mein erster Zaehler suchte im ROHEN
Dateitext. Er fand vier Regeln statt drei - die vierte war mein EIGENER
Aenderungstext, in dem die Regel zitiert steht. Wer rohen Dateitext durchsucht,
misst seine eigene Begruendung mit: gruen, sobald jemand sie hinschreibt, rot,
wenn jemand sie loescht. Gezaehlt wird deshalb ausschliesslich INNERHALB der
`<style>`-Bloecke, und ein Koeder belegt, dass ein Vorkommen im Kommentar NICHT
mitzaehlt.

DIE EINE AUSNAHME, namentlich: `svg text` steht auf 10 px. Diagramm-Achsen
stehen dicht nebeneinander; 10 auf 12 px kann sie zum Ueberlappen bringen. Das
ist ein eigener Schritt mit eigener Messung. Sie steht hier als NAME, nicht als
Zahl - eine Ausnahme ohne Begruendung ist eine Attrappe.
"""
import io
import os
import re

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")

# 🔴 Die Einheit ist OPTIONAL, und das ist kein Schoenheitsfehler: die Datei
# fuehrt `font-size: 0 !important` OHNE Einheit. Ein Muster, das auf `px`
# endet, uebersieht den kleinsten erzwungenen Wert, den es ueberhaupt gibt -
# und meldet dabei „keine Regel unter 12 px", was von einem echten Ergebnis
# nicht zu unterscheiden ist.
# Das Wahlmuster darf bis 200 Zeichen lang sein: das Sync-Banner-Muster liegt
# schon bei rund 105, und eine Kappung bei 120 haette es irgendwann halbiert.
REGEL = re.compile(
    r"([^{};]{1,200})\{([^{}]{0,300}?font-size:\s*(\d+(?:\.\d+)?)\s*(px|r?em|%|pt)?"
    r"\s*!important[^{}]{0,200})\}")

# Wahlmuster, die unter 12 px bleiben duerfen - jedes mit Begruendung und
# Messdatum. Eine Ausnahme ohne Begruendung ist eine Attrappe.
#
#   🔴 `svg text` IST AM 28.09.2026 WEGGEFALLEN - die Ausnahme wurde nicht
#       gehoben, sondern ENTFERNT. Sie stand innerhalb von
#       `@media (max-width: 600px)`, galt also nur am Telefon, und dort wo es
#       weh tat (8 px am Schreibtisch) gar nicht. Vor allem NAHM sie zurueck:
#       die x-Achse von SvgBar steht im Quelltext auf UI.fMeta (12) und wurde
#       auf 10 gedrueckt, die Ringsumme von 15 auf 10. Eine Ausnahme, die zwei
#       richtige Werte verschlechtert, ist keine.
#       Die sechs SVG-Schriften sind jetzt im QUELLTEXT auf 12, mit zwei
#       gerechneten Nebenbedingungen (breitere SvgPie-viewBox, Zwei-Reihen-
#       Versatz der Wertzahl) und einer Ausduennung in SvgLine.
#       Gemessen: `auswertungen` von 264 auf 2 (390 px) und von 338 auf 7
#       (1440 px). Bericht: `docs/befunde/DIAGRAMM_ACHSEN.md`.
#
#   `.header-row .mob-stack button` (0, 28.09.2026)
#       Bei hoechstens 340 px, mit dem Kommentar „Text weg, Icon bleibt".
#       Sie ist NEUTRALISIERT: drei Zeilen darunter setzt derselbe
#       Wahlausdruck 16 px, gleiche Spezifitaet, spaeter im Text - die Null
#       verliert. Die Ausnahme gilt nur, SOLANGE das Gegenstueck dasteht;
#       `test_die_null_regel_ist_UND_BLEIBT_neutralisiert` prueft genau das.
AUSNAHMEN = (".header-row .mob-stack button",)


def _lies():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def stilbloecke(text):
    """JEDE CSS-Quelle der Datei. NICHT der rohe Dateitext.

    🔴 ZWEI LUECKEN, BEIDE AM 28.09.2026 MIT EINER MUTATION BELEGT.

    (1) DIE PAARUNG WAR KAPUTT - und zwar an meiner eigenen Prosa.
        `index.html` fuehrt 21 oeffnende `<style>` und nur 20 schliessende.
        Das ueberzaehlige steht in Zeile 9502 INNERHALB eines deutschen
        JS-Kommentars: „inline schlaegt jede Regel im <style>". Das naive,
        nicht-gierige Muster paarte es mit dem `</style>` aus Zeile 11228 und
        las dadurch 244 061 von 291 511 Zeichen - 84 % - JavaScript als CSS.
        Ein Zitat in diesem Bereich erzeugt einen FALSCHEN ALARM: genau die
        Fehlerform, die dieser Riegel bei sich selbst schon einmal gefunden
        hat, nur andersherum.
        Die Regel dagegen: **vor einem `</style>` gilt das LETZTE `<style>`**,
        nicht das erste. Dazu unten eine Zaehlprobe auf die GROESSE der
        Grundgesamtheit - waechst sie ins Sechsstellige, ist die Paarung
        wieder aus dem Tritt.

    (2) `GCSS()` WAR UNSICHTBAR. Die Datei baut CSS auch zur Laufzeit: eine
        Funktion `GCSS()` liefert ein Vorlagenliteral, das an sechs Stellen
        als `createElement('style', {}, GCSS())` eingehaengt wird. Im
        Quelltext steht dort KEIN `<style>`. Eine Mutation in `GCSS()`
        (`font-size:16px` -> `9px !important`) liess diesen Riegel schweigen.
        Sein damaliger Koeder konnte das nicht fangen, weil er sein
        Pruefstueck selbst als `<html><head><style>…` baute und damit
        **genau die Luecke des Riegels teilte**.

    CSS-Kommentare werden entfernt, bevor gemessen wird - sonst zaehlt eine
    auskommentierte Regel mit.
    """
    teile = []
    # (1) Die <style>-Bloecke, rueckwaerts gepaart.
    for zu in re.finditer(r"</style\s*>", text, re.I):
        vor = text.rfind("<style", 0, zu.start())
        if vor < 0:
            continue
        auf = text.find(">", vor)
        if 0 <= auf < zu.start():
            teile.append(text[auf + 1:zu.start()])
    # (2) Die Laufzeit-Quelle: das Vorlagenliteral von `const GCSS=()=>` ... `.
    #     Es steht an sechs Stellen als createElement('style',{},GCSS()) im
    #     Baum - im Quelltext aber OHNE <style>, und genau deshalb war es
    #     unsichtbar.
    m = re.search(r"GCSS\s*=\s*\(\s*\)\s*=>\s*`", text)
    if m:
        i = m.end()                     # hinter dem oeffnenden Backtick
        j, tiefe = i, 0
        while j < len(text):
            c = text[j]
            if c == "\\":
                j += 2
                continue
            if c == "$" and j + 1 < len(text) and text[j + 1] == "{":
                tiefe += 1
                j += 2
                continue
            if c == "}" and tiefe:
                tiefe -= 1
            elif c == "`" and not tiefe:
                break
            j += 1
        teile.append(text[i:j])
    roh = "".join(teile)
    return re.sub(r"/\*.*?\*/", " ", roh, flags=re.S)


def erzwungen_klein(css):
    """(Wert, Wahlmuster) je Regel, die unter 12 px erzwingt - ohne Ausnahmen.

    Eine Regel ohne Einheit zaehlt als px: `font-size: 0 !important` ist der
    kleinste erzwungene Wert der Datei. Eine Regel mit einer ANDEREN Einheit
    (em, %, pt) wird gemeldet statt still uebersprungen - der Riegel kann sie
    nicht in px umrechnen, und schweigen waere hier eine Aussage, die er nicht
    belegen kann.
    """
    aus = []
    for m in REGEL.finditer(css):
        sel = " ".join(m.group(1).split())
        if any(a in sel for a in AUSNAHMEN):
            continue
        einheit = m.group(4)
        if einheit and einheit != "px":
            aus.append(("%s%s (nicht in px - nicht beurteilbar)"
                        % (m.group(3), einheit), sel[:120]))
            continue
        if float(m.group(3)) >= 12:
            continue
        aus.append((m.group(3), sel[:120]))
    return aus


def test_kein_css_erzwingt_schrift_unter_12px():
    css = stilbloecke(_lies())
    # Gegenprobe auf die Grundgesamtheit: der Stilblock MUSS Regeln mit
    # !important fuehren, sonst ist die Null unten geschenkt.
    alle = [m for m in REGEL.finditer(css)]
    assert len(alle) > 15, (
        "\U0001F534 Nur %d font-size-Regeln mit !important im Stilblock - die "
        "Bloecke wurden\n  nicht richtig gelesen, und eine leere "
        "Grundgesamtheit meldet immer gruen." % len(alle))
    fund = erzwungen_klein(css)
    assert not fund, (
        "\U0001F534 %d CSS-Regeln erzwingen eine Schrift unter 12 px:\n%s\n"
        "  Eine Regel mit !important uebersteuert JEDE Inline-Angabe. Solange "
        "sie steht,\n"
        "  bleibt jede gehobene Zahl im Quelltext wirkungslos - und ein "
        "Riegel, der nur\n"
        "  den Quelltext misst, bleibt dabei gruen."
        % (len(fund), "\n".join("    %spx  %s" % x for x in fund)))


def test_die_ausnahmen_sind_noch_die_benannten():
    """EINE Regel darf drunter bleiben, und nur die benannte.

    Ohne diese Probe koennte die Ausnahmeliste wachsen, bis der Riegel nichts
    mehr misst.

    🔴 Es waren zwei. `svg text` ist am 28.09.2026 WEGGEFALLEN - nicht
    gehoben, sondern entfernt: sie galt nur unter 600 px und nahm dort zwei
    bereits richtige Werte zurueck (SvgBar-x-Achse 12 -> 10, Ringsumme
    15 -> 10). Die sechs SVG-Schriften stehen jetzt im Quelltext auf 12.

    🔴 Die verbliebene ist erst am 28.09. SICHTBAR geworden, und zwar nicht
    durch eine Aenderung am Code, sondern weil das Muster endlich weit genug
    war: es verlangte frueher `px` und war damit fuer `font-size: 0
    !important` blind - den KLEINSTEN erzwungenen Wert, den diese Datei fuehrt.
    """
    css = stilbloecke(_lies())
    drunter = [(px, " ".join(sel.split()))
               for px, sel in [(m.group(3), m.group(1))
                               for m in REGEL.finditer(css)]
               if float(px) < 12]
    namen = [s for _, s in drunter]
    assert len(drunter) == 1, (
        "\U0001F534 %d Regeln unter 12 px in den CSS-Quellen, erwartet ist "
        "genau eine\n  (die neutralisierte Null der Kopfzeilen-Knoepfe). "
        "Steht `svg text` wieder da,\n  nimmt sie erneut zwei richtige Werte "
        "zurueck:\n    %s" % (len(drunter), drunter))
    assert not any("svg text" in s for s in namen), (
        "\U0001F534 Die `svg text`-Regel ist zurueck. Sie galt nur unter "
        "600 px und drueckte\n  dort die x-Achse von SvgBar von 12 auf 10 und "
        "die Ringsumme von 15 auf 10.\n  Gefunden: %r" % namen)
    assert any(".header-row .mob-stack button" in s for s in namen), (
        "\U0001F534 Die Null-Regel der Kopfzeilen-Knoepfe ist nicht mehr "
        "dabei. Gefunden: %r" % namen)
    assert len(AUSNAHMEN) == 1, (
        "\U0001F534 Die Ausnahmeliste ist gewachsen (%s). Jede Ausnahme braucht "
        "ein Messdatum\n  im Kopf dieser Datei, sonst misst der Riegel "
        "irgendwann nichts mehr." % (AUSNAHMEN,))


def test_die_null_regel_ist_UND_BLEIBT_neutralisiert():
    """🔴 Eine bedingte Ausnahme - sie gilt nur, solange ihr Gegenstueck steht.

    Bei hoechstens 340 px setzt `.header-row .mob-stack button` die Schrift auf
    `0 !important`, mit dem Kommentar „Text weg, Icon (Emoji) bleibt". Drei
    Zeilen darunter steht DERSELBE Wahlausdruck noch einmal, zusammen mit
    `::first-letter`, und setzt `font-size: 16px !important`.

    Gleiche Spezifitaet, spaeter im Text: **die Null verliert.** Die Absicht
    wirkt also nicht, und hat vermutlich nie gewirkt - bei 340 px steht der
    volle Text mit 16 px im Knopf.

    Deshalb wird die Null hier NICHT als harmlos abgehakt, sondern als
    NEUTRALISIERT gefuehrt: verschwindet die 16-px-Zeile, wird die Null
    scharf, jeder Kopfzeilen-Knopf verliert seinen Text, und dieser Riegel
    geht rot. Eine Ausnahme ohne ihr Gegenstueck ist eine Attrappe.

    Ob die urspruengliche Absicht wiederhergestellt werden soll, ist eine
    Frage an Sebastian und steht in ENTSCHEIDUNGEN-OFFEN.
    """
    css = stilbloecke(_lies())
    i = css.find("font-size: 0 !important")
    assert i > 0, (
        "\U0001F534 Die Null-Regel ist weg. Gut moeglich, dass das richtig ist -"
        " dann gehoert\n  diese Probe angepasst und die Ausnahmeliste "
        "gekuerzt.")
    danach = css[i:i + 700]
    assert re.search(r"\.header-row\s+\.mob-stack\s+button\s*\{[^{}]*"
                     r"font-size:\s*16px\s*!important", danach, re.S), (
        "\U0001F534 Die Null-Regel der Kopfzeilen-Knoepfe ist NICHT mehr "
        "neutralisiert.\n"
        "  `font-size: 0 !important` wirkt jetzt: bei hoechstens 340 px "
        "verliert jeder Knopf\n"
        "  der Kopfzeile seinen Text. Entweder die 16-px-Zeile "
        "wiederherstellen oder die\n"
        "  Null entfernen - aber nicht beides stehenlassen und hoffen.")


def test_koeder_eine_erzwungene_kleine_regel():
    """Eine 10-px-Regel MUSS gemeldet werden."""
    fund = erzwungen_klein(".irgendwas > div { font-size: 10px !important; }")
    assert fund and fund[0][0] == "10", (
        "\U0001F534 Eine erzwungene 10-px-Regel wurde nicht gemeldet.")


def test_koeder_kommentar_zaehlt_NICHT_mit():
    """\U0001F534 Der Fehler, der mir beim Zaehlen selbst passiert ist.

    Mein erster Zaehler las den ROHEN Dateitext und fand vier Regeln statt
    drei: die vierte war mein eigener Aenderungstext, in dem die Regel zitiert
    steht. Diese Probe belegt, dass der Riegel seine eigene Begruendung nicht
    mitmisst.
    """
    text = ('<html><head><style>.a{font-size:14px !important;}'
            '.b{font-size:13px !important;}.c{font-size:12px !important;}'
            '.d{color:red !important;}.e{font-size:16px !important;}'
            '.f{font-size:15px !important;}.g{font-size:18px !important;}'
            '.h{font-size:20px !important;}.i{font-size:22px !important;}'
            '.j{font-size:24px !important;}.k{font-size:26px !important;}'
            '.l{font-size:28px !important;}.m{font-size:30px !important;}'
            '.n{font-size:32px !important;}.o{font-size:34px !important;}'
            '.p{font-size:36px !important;}</style></head><body>'
            '<script>/* die Regel .z{font-size: 9px !important;} war der '
            'Traeger des Befunds */</script></body></html>')
    css = stilbloecke(text)
    assert "font-size: 9px" not in css, (
        "\U0001F534 Der Kommentar im script-Block ist in den Stilblock "
        "geraten.")
    assert not erzwungen_klein(css), (
        "\U0001F534 Der Riegel hat seine eigene Begruendung mitgezaehlt - "
        "genau der Fehler,\n  den er verhindern soll.")
    # Und die Gegenrichtung am SELBEN Text: im echten Stilblock wird gemeldet.
    assert erzwungen_klein(css + ".z{font-size: 9px !important;}"), (
        "\U0001F534 Am selben Text meldet der Riegel eine echte Regel nicht - "
        "dann schweigt er\n  immer, und die Probe oben ist wertlos.")


def test_gegenprobe_zwoelf_und_groesser_schweigen():
    for fall in (".a { font-size: 12px !important; }",
                 ".b { font-size: 14px !important; }",
                 ".c { font-size: 18px !important; }"):
        assert not erzwungen_klein(fall), (
            "\U0001F534 %s wurde gemeldet - der Riegel meldet dann alles." % fall)


def test_koeder_JE_QUELLE_nicht_nur_der_style_block():
    """🔴 Der Koeder, der bis v3.9.967 gefehlt hat.

    Der alte Koeder baute sein Pruefstueck selbst als `<html><head><style>…`
    und teilte damit **genau die Luecke des Riegels**: die Laufzeit-Quelle
    `GCSS()` kam darin nicht vor, also konnte er ihre Unsichtbarkeit nicht
    aufdecken. Eine Mutation in `GCSS()` liess den Riegel schweigen.

    Jetzt gibt es einen Koeder JE QUELLE. Faellt eine Quelle aus der Messung,
    geht genau ihr Koeder rot - und nicht der andere.
    """
    # Quelle 1: ein gewoehnlicher <style>-Block.
    q1 = "<html><head><style>.a{font-size:9px !important;}</style></head></html>"
    assert erzwungen_klein(stilbloecke(q1)), (
        "\U0001F534 Eine Regel im <style>-Block wird nicht gesehen.")

    # Quelle 2: das Laufzeit-Literal. KEIN <style> im Quelltext - genau
    # deshalb war es unsichtbar.
    q2 = ("const GCSS=()=>`.b{font-size:9px !important;}`;\n"
          "React.createElement('style',{},GCSS());")
    assert erzwungen_klein(stilbloecke(q2)), (
        "\U0001F534 Die Laufzeit-Quelle GCSS() wird nicht gesehen.\n"
        "  Sie wird an sechs Stellen als createElement('style',{},GCSS()) "
        "eingehaengt und\n"
        "  erreicht den Browser genauso wie ein <style>-Block. Eine Mutation "
        "darin liess den\n"
        "  Riegel am 28.09.2026 schweigen.")


def test_koeder_ein_style_im_KOMMENTAR_zerreisst_die_paarung_nicht():
    """🔴 Die Falle, an der die Paarung wirklich gescheitert ist.

    `index.html` fuehrt 21 oeffnende `<style>` und 20 schliessende. Das
    ueberzaehlige steht in einem deutschen JS-Kommentar: „inline schlaegt jede
    Regel im <style>". Ein nicht-gieriges `<style>(.*?)</style>` paarte es mit
    einem `</style>` tausende Zeilen spaeter und las 84 % der Datei als CSS.

    Diese Probe zeigt beide Richtungen am SELBEN Text: das Zitat im Kommentar
    holt keinen Code herein, und die echte Regel danach wird trotzdem
    gefunden.
    """
    text = (
        "<html><head><style>.echt{font-size:9px !important;}</style></head>\n"
        "<body><script>\n"
        "/* Hinweis: inline schlaegt jede Regel im <style> - deshalb ... */\n"
        "var heimlich = \"font-size:7px !important\";\n"
        "</script></body></html>")
    css = stilbloecke(text)
    assert "heimlich" not in css and "var " not in css, (
        "\U0001F534 Das `<style>` im Kommentar hat JavaScript in die "
        "CSS-Grundgesamtheit gezogen.\n"
        "  Gemessen: %d Zeichen." % len(css))
    assert len(css) < 200, (
        "\U0001F534 Die Grundgesamtheit ist %d Zeichen gross - bei diesem "
        "Pruefstueck sind\n  hoechstens ein paar Dutzend richtig. Die Paarung "
        "ist aus dem Tritt." % len(css))
    assert erzwungen_klein(css), (
        "\U0001F534 Am selben Text wird die ECHTE Regel nicht gefunden - dann "
        "schweigt der\n  Riegel immer, und die Probe oben ist wertlos.")


def test_die_grundgesamtheit_hat_die_richtige_groessenordnung():
    """Eine Zaehlprobe auf die GROESSE, nicht auf den Inhalt.

    Die CSS-Quellen dieser Datei sind rund 40 000 Zeichen gross. Liest der
    Auszieher ploetzlich sechsstellig, hat er wieder JavaScript erwischt -
    dann ist jede Null darunter geschenkt und jeder Alarm verdaechtig.
    Liest er dreistellig, ist eine Quelle weggefallen.
    """
    n = len(stilbloecke(_lies()))
    assert 20_000 < n < 120_000, (
        "\U0001F534 Die CSS-Grundgesamtheit ist %d Zeichen gross. Erwartet "
        "sind rund 40 000.\n"
        "  Sechsstellig heisst: die <style>-Paarung hat wieder JavaScript "
        "hereingezogen\n"
        "  (das ueberzaehlige `<style>` steckt in einem deutschen Kommentar). "
        "Dreistellig\n  heisst: eine Quelle ist weggefallen." % n)


def test_der_riegel_sagt_selbst_was_er_NICHT_prueft():
    """🔴 Anwesenheit statt Wirkung - und diesmal steht es im Riegel selbst.

    Dieser Riegel liest den QUELLTEXT. Er kann nicht sehen, was der Browser
    ausrechnet, und drei der neun in v3.9.966 gehobenen Regeln treffen
    ueberhaupt kein Bauteil (`.ber-table` kommt als Klasse nirgends vor,
    `.badge` nur in Druck-HTML mit eigenem Stilblock, und beide Arme des
    Sync-Banner-Musters gehen ins Leere). An denen ist der Riegel gruen - und
    war es auch, als sie noch 11 px trugen.

    Umgekehrt kann der Schirm unter 12 px landen ganz ohne `!important`.

    Die Wirkungsmessung ist deshalb ein eigenes Werkzeug, und diese Probe
    haelt fest, dass es existiert. Ein Riegel, der stillschweigend gruen
    meldet, was er gar nicht prueft, ist die gefaehrlichste Form von allen.
    """
    wurzel = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    werkzeug = os.path.join(wurzel, "scripts", "schriftgroesse_wirkung.py")
    assert os.path.exists(werkzeug), (
        "\U0001F534 Die Wirkungsmessung `scripts/schriftgroesse_wirkung.py` "
        "fehlt.\n"
        "  Ohne sie behauptet dieser Riegel eine Wirkung, die er nicht misst.")
    kopf = io.open(werkzeug, encoding="utf-8", newline="").read(2000)
    assert "getComputedStyle" in kopf, (
        "\U0001F534 Die Wirkungsmessung fragt nicht mehr nach der BERECHNETEN "
        "Groesse.\n  Dann misst sie dasselbe wie dieser Riegel, und es gibt "
        "sie umsonst.")
