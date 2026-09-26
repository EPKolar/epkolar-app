# -*- coding: utf-8 -*-
"""v3.9.932 Stufe 1 - das Mobil-Fundament. Kein Aussehen, nur Fundament.

WAS HIER GESICHERT WIRD
───────────────────────
1. Viewport: Zoom frei, Safe-Area an.
2. Der Kopf verlinkt das STATISCHE Manifest; der Laufzeit-Blob-Builder ist weg.
3. BP_MOB ist EINE Schwelle - und sie ist im selben <script>-Block erreichbar
   wie ihre Verwendungen.
4. Die Endreserve haengt an der Leistenhoehe statt an einer getippten Zahl.

Die Manifest- und sw.js-Riegel selbst stehen in test_pwa_manifest_v931.py;
hier geht es um die Stellen in index.html, die dort bewusst ausgespart waren.

WARUM PUNKT 3 DER WICHTIGSTE IST
────────────────────────────────
`node_check.py` PARST die <script>-Bloecke, es FUEHRT sie nicht aus. Eine
Konstante, die im falschen Block deklariert wird, ist syntaktisch tadellos
und zur Laufzeit ein ReferenceError - an 27 Stellen gleichzeitig, bei
gruenem Tor. Genau diese Fehlerform steht in CLAUDE.md mehrfach
("node_check parst nur"). Deshalb wird hier die BLOCKZUGEHOERIGKEIT gemessen,
nicht die blosse Anwesenheit der Deklaration.
"""
import io
import re

import pytest

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
IDX = WURZEL / "index.html"


@pytest.fixture(scope="module")
def roh():
    return io.open(str(IDX), encoding="utf-8", newline="").read()


def _bloecke(s):
    """(anfang, ende) je <script>-Block."""
    aus = []
    for m in re.finditer(r"<script\b[^>]*>", s, re.I):
        e = s.find("</script>", m.end())
        aus.append((m.end(), e if e > 0 else len(s)))
    return aus


def _block_von(bloecke, pos):
    for nr, (a, b) in enumerate(bloecke):
        if a <= pos < b:
            return nr
    return None


def _komm_spannen(s):
    return [(m.start(), m.end()) for m in re.finditer(r"/\*[\s\S]*?\*/", s)]


def _im_kommentar(spannen, i):
    for a, b in spannen:
        if a <= i < b:
            return True
        if a > i:
            break
    return False


# ── 1. Viewport ────────────────────────────────────────────────────────────

def test_viewport_traegt_safe_area_und_sperrt_den_zoom_nicht(roh):
    """Beides in einem Riegel, weil es EINE Zeile ist.

    `viewport-fit=cover` fehlte, obwohl der Code an elf Stellen
    env(safe-area-inset-*) verwendet - ohne cover liefert der Browser dort
    immer 0. Elf Berechnungen sahen richtig aus und rechneten mit einer Null.
    """
    m = re.search(r'<meta[^>]*name=["\']viewport["\'][^>]*>', roh)
    assert m, "Es gibt kein Viewport-Meta."
    tag = m.group(0)
    assert "viewport-fit=cover" in tag, (
        "viewport-fit=cover fehlt - dann liefert env(safe-area-inset-*) "
        "ueberall 0, und die fixe Fussleiste sitzt unter dem Home-Indikator. "
        "Gefunden: %s" % tag)
    assert "maximum-scale" not in tag, (
        "maximum-scale sperrt das Zoomen. Auf einer Baustellen-App ist Zoomen "
        "Bedienbarkeit, nicht Kosmetik. Gefunden: %s" % tag)
    assert "user-scalable" not in tag, (
        "user-scalable=no sperrt das Zoomen. Gefunden: %s" % tag)


def test_safe_area_wird_ueberhaupt_verwendet(roh):
    """KOEDER zum Viewport-Riegel.

    `viewport-fit=cover` waere sinnlos, wenn niemand die Insets liest. Faellt
    diese Zahl auf 0, misst der Riegel darueber nichts mehr Sinnvolles.
    """
    assert roh.count("safe-area-inset") >= 8, (
        "Nur %d safe-area-inset-Stellen - vorher waren es 11. Wurden sie "
        "entfernt, ist viewport-fit=cover ohne Wirkung."
        % roh.count("safe-area-inset"))


# ── 2. Statisches Manifest im Kopf, Blob-Builder raus ─────────────────────

def test_der_kopf_verlinkt_das_statische_manifest(roh):
    kopf = roh[:roh.lower().find("</head>")]
    assert 'rel="manifest" href="./manifest.json"' in kopf, (
        "Der <head> verlinkt manifest.json nicht.")
    assert 'rel="apple-touch-icon" href="./icon-192.png"' in kopf, (
        "apple-touch-icon zeigt nicht auf die echte Datei.")


def test_der_laufzeit_blob_manifest_builder_ist_weg(roh):
    """Zwei Manifeste waeren schlimmer als eines.

    Der Blob-Builder haengte sein eigenes <link rel="manifest"> an und haette
    das statische ueberstimmt - die neuen Icon-Dateien waeren dann zwar da,
    aber nie geladen worden.
    """
    assert "PWA MANIFEST (inline" not in roh, "Der Blob-Builder steht noch da."
    assert "application/manifest+json" not in roh, (
        "Es wird noch ein Manifest zur Laufzeit gebaut.")
    links = re.findall(r'rel=["\']manifest["\']', roh)
    assert len(links) == 1, (
        "Es gibt %d Manifest-Verweise - genau einer darf es sein, sonst "
        "gewinnt der zuletzt angehaengte." % len(links))


# ── 3. BP_MOB - und zwar im richtigen Block ───────────────────────────────

def test_bp_mob_ist_genau_einmal_deklariert(roh):
    assert roh.count("const BP_MOB=600;") == 1, (
        "BP_MOB ist %dx deklariert." % roh.count("const BP_MOB=600;"))


def test_bp_mob_ist_von_jeder_verwendung_aus_erreichbar(roh):
    """DER Riegel dieser Stufe.

    Gemessen wird die Blockzugehoerigkeit, nicht die Anwesenheit. Eine
    Konstante im falschen <script>-Block parst fehlerfrei und ist zur
    Laufzeit ein ReferenceError an jeder Verwendungsstelle.
    """
    bloecke = _bloecke(roh)
    dekl = roh.find("const BP_MOB=600;")
    assert dekl > 0
    heim = _block_von(bloecke, dekl)
    assert heim is not None, "Die Deklaration liegt in keinem <script>-Block."

    stellen = [m.start() for m in re.finditer(r"ww<BP_MOB", roh)]
    assert stellen, (
        "Keine einzige Verwendung von BP_MOB gefunden. Das ist kein gruenes "
        "Ergebnis, sondern eine ausgefallene Messung.")
    fremd = [p for p in stellen if _block_von(bloecke, p) != heim]
    assert not fremd, (
        "%d Verwendungen liegen in einem ANDEREN <script>-Block als die "
        "Deklaration. Sie waeren zur Laufzeit ein ReferenceError, und "
        "node_check bliebe gruen." % len(fremd))
    frueher = [p for p in stellen if p < dekl]
    assert not frueher, (
        "%d Verwendungen stehen VOR der Deklaration." % len(frueher))


def test_im_code_steht_keine_nackte_600er_schwelle_mehr(roh):
    """Die vier verbliebenen ww<600 duerfen nur in Kommentaren stehen.

    Dort sind sie Geschichte: sie dokumentieren, warum eine Schwelle einmal
    von 700 auf 600 ging. Wer sie mitersetzt, faelscht diese Geschichte.
    """
    spannen = _komm_spannen(roh)
    im_code = [m.start() for m in re.finditer(r"ww\s*<\s*600", roh)
               if not _im_kommentar(spannen, m.start())]
    assert not im_code, (
        "%d nackte ww<600 stehen noch im Code." % len(im_code))
    # v3.9.936: 27 -> 28. Eine Stelle (WerkzeugView) blieb in v3.9.932 auf
    # der nackten 600 stehen, und ich habe sie ZWEIMAL als "steht im
    # Kommentar" gemeldet. Ursache war mein Zaehler: er suchte Blockkommentare
    # per Regex und hielt dabei das Sternchen in
    # accept:"application/pdf,image/*" fuer einen Kommentaranfang. Der wird
    # nie geschlossen - also galt alles dahinter als Kommentar, die letzten
    # 80 kB der Datei mitsamt dieser Funktion. Ein Zaehler, der zu WENIG
    # findet, meldet ein gruenes Ergebnis.
    # Gefunden hat es Sebastian, indem er die Zeile hereinkopiert hat.
    # Gezaehlt wird seither mit scripts/code_scan.py, das eine EICHPROBE
    # bestehen muss (jede `const isMob=ww<...`-Deklaration ist Code) und die
    # Auskunft verweigert, wenn es sie nicht besteht.
    # v3.9.955: 28 -> 29. VBautag ist von ww<768 auf ww<BP_MOB umgestellt
    # worden - die Entscheidung, die der Riegel darunter bis dahin als offen
    # festgehalten hat. Die Zahl STEIGT, weil eine Stelle dazukam; das ist die
    # Gegenrichtung zu "eine Pruefung anpassen, damit sie gruen wird". Waere
    # sie gesunken, waere eine Umstellung verlorengegangen.
    assert roh.count("ww<BP_MOB") == 29, (
        "Erwartet 29 umgestellte Stellen, gefunden %d." % roh.count("ww<BP_MOB"))


# Die umschliessende Ansicht je erlaubter Tablet-Schwelle, in Dateireihenfolge.
# Namentlich statt als Zahl - Begruendung im Riegel darunter.
_TABLET_ERLAUBT = ["ProjectShell", "VDash", "VPlan", "VFotos",
                   "WerkzeugView", "WerkzeugView"]


def test_die_tablet_schwellen_sind_unangetastet(roh):
    """Die sechs bewussten isTab-Stellen, jede mit ihrer Ansicht benannt.

    Kommentarblind gezaehlt, aus gemessenem Anlass: die Deklaration von
    BP_MOB traegt einen Kommentar, der erklaert, WARUM die 768er Stellen
    stehen bleiben - und nennt `ww<768` dabei zweimal. Ein roher Zaehler
    stand deshalb auf 9 statt 7 und haette einen Fehler gemeldet, den es
    nicht gibt. Gemessen wird der Code, nicht der Text ueber dem Code.

    v3.9.955 - WARUM AUS SIEBEN SECHS WURDEN
    ────────────────────────────────────────
    Dieser Riegel hielt fest, die siebte Stelle (VBautag) sei "eine offene
    Entscheidung fuer Sebastian". Sie ist getroffen: dort hing `isMob` an der
    TABLETBREITE, womit ein Tablet im Hochformat im Bautagebuch die
    Handy-Fassung zeigte und im Rest derselben App die Desktop-Fassung. Seit
    v3.9.955 steht dort BP_MOB.

    Eine Zahl von 7 auf 6 zu senken, damit ein Riegel gruen wird, waere genau
    der schwerste Fehler. Deshalb wird hier nicht die Zahl gesenkt, sondern
    die Pruefung VERSCHAERFT: sie nennt die sechs Ansichten einzeln. Eine
    Zahl allein hat nie unterschieden, ob eine erlaubte Stelle verschwand und
    dafuer eine neue, unerlaubte dazukam - beides ergibt wieder sechs.

    Die Verhaltensaenderung selbst, ihre Messung und der Koeder liegen in
    tests/test_eine_mobilschwelle_v955.py.
    """
    spannen = _komm_spannen(roh)
    im_code = [m.start() for m in re.finditer(r"ww\s*<\s*768", roh)
               if not _im_kommentar(spannen, m.start())]
    assert im_code, (
        "Keine einzige ww<768-Stelle im Code gefunden. Das ist kein gruenes "
        "Ergebnis: die sechs bewussten Tabletschwellen MUESSEN da sein. "
        "Entweder sind sie verlorengegangen, oder der Kommentarzaehler irrt "
        "wieder wie in v3.9.936 und haelt die halbe Datei fuer Kommentar.")
    ansichten = []
    for p in im_code:
        treffer = list(re.finditer(r"function\s+([A-Za-z_]\w*)\s*\(", roh[:p]))
        ansichten.append(treffer[-1].group(1) if treffer else "?")
    assert ansichten == _TABLET_ERLAUBT, (
        "Die Tablet-Schwellen `ww<768` stehen nicht mehr dort, wo sie erlaubt "
        "sind.\n  erwartet: %s\n  gemessen: %s\n"
        "Ist eine DAZUGEKOMMEN: sie meint vermutlich die Mobilschwelle, dann "
        "gehoert dort BP_MOB hin. Ist eine WEGGEFALLEN: pruefen, ob die "
        "Tablet-Fassung dieser Ansicht verlorenging, und diese Liste erst "
        "danach nachziehen." % (_TABLET_ERLAUBT, ansichten))


# ── 4. Die Endreserve haengt an der Leistenhoehe ──────────────────────────

def test_die_endreserve_haengt_an_der_leistenhoehe(roh):
    """Nicht: "es steht eine Zahl da". Sondern: die Zahl steht NUR EINMAL.

    Der Sinn der Uebung ist, dass Leiste und Reserve nicht auseinanderlaufen.
    Eine zweite getippte Zahl im Reserve-Ausdruck wuerde genau das wieder
    zulassen.
    """
    assert "--epk-bar-h:58px" in roh, "Die Leistenhoehe ist nicht als Groesse hinterlegt."
    assert "--epk-bar-warn:24px" in roh, (
        "Der Sync-Streifen ueber der Leiste ist nicht beruecksichtigt.")
    m = re.search(r'padding:ww<BP_MOB\?"0 0 ([^"]+)"', roh)
    assert m, "Die Endreserve am rollenden Kasten wurde nicht gefunden."
    ausdruck = m.group(1)
    assert "var(--epk-bar-h" in ausdruck and "var(--epk-bar-warn" in ausdruck, (
        "Die Reserve nimmt die Leistenhoehe nicht ueber die Groesse: %s"
        % ausdruck)
    assert "env(safe-area-inset-bottom" in ausdruck, (
        "Die Reserve beruecksichtigt die Safe-Area nicht: %s" % ausdruck)
    # Eine getippte Pixelzahl ausser dem Abstand von 12px waere ein Rueckfall.
    zahlen = re.findall(r"(\d+)px", ausdruck.replace("var(--epk-bar-h,58px)", "")
                        .replace("var(--epk-bar-warn,24px)", "")
                        .replace("env(safe-area-inset-bottom,0px)", ""))
    assert zahlen == ["12"], (
        "Im Reserve-Ausdruck stehen getippte Pixelzahlen %s - dann laufen "
        "Leiste und Reserve wieder auseinander: %s" % (zahlen, ausdruck))
