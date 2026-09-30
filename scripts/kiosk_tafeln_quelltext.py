# -*- coding: utf-8 -*-
"""Die drei Kiosk-Tafeln am QUELLTEXT messen - Lesewege, Auffangzweige, Stand.

WAS HIER GEMESSEN WIRD
----------------------
`index.html` rendert fuer die drei Kiosk-Hashes `#planung`, `#monteure` und
`#stempel` drei eigene Bauteile:

    WochenplanTafel   <- #planung
    MonteurTafel      <- #monteure  (auch der Ruecktritt ohne Hash)
    StempelTafel      <- #stempel

Gemessen wird JE BAUTEIL:

  1. LESEWEGE      welche Abrufe stehen im Rumpf (fetch / API. / _sbGet / RPC)
  2. AUFFANGZWEIGE wie viele `catch` es gibt und wie viele davon LEER sind
  3. RLS-MARKEN    ob `_rlsLeer` / `__rlsFehler` / `__EP_RLS` ueberhaupt
                   vorkommen - in diesem Haus kommt ein abgewiesener
                   Lesezugriff als HTTP 200 mit LEEREM Array an
  4. STAND         jedes `setInterval`, das `setStand(` enthaelt, und ob im
                   selben Rumpf eine ERFOLGSPRUEFUNG steht. Ohne sie ist der
                   angezeigte "Stand" die UHR, nicht das Datenalter.
  5. SCHRIFT       alle `fontSize:<zahl>` im Rumpf, als Histogramm
  6. CSS           jede `font-size`-Regel mit `!important`, samt der Frage,
                   ob ihre @media-Bedingung bei Kioskbreite (>= 600 px)
                   ueberhaupt greift

WARUM NICHT IM ROHEN DATEITEXT GEZAEHLT WIRD
--------------------------------------------
`index.html` fuehrt lange deutsche Kommentare, die Code WOERTLICH zitieren -
darunter genau die Marken, nach denen hier gesucht wird. Wer den Rohtext
durchsucht, misst seine eigene Begruendung mit. Getrennt wird mit dem
geeichten `code_scan.ist_code`.

🔴 SELBSTPROBE - EIN KOEDER JE SCHREIBWEISE, PLUS GEGENPROBE
------------------------------------------------------------
Jeder Melder wird an einem SELBSTGEBAUTEN Text geprueft, nicht an
index.html: eine Probe, die auf den Bestand der App zeigt, geht kaputt,
sobald jemand etwas umbenennt - und dann faellt ein Werkzeug aus, das mit
der Umbenennung nichts zu tun hat.

Geprueft wird je Melder:
  * ein Koeder JE SCHREIBWEISE (einfache UND doppelte Anfuehrungszeichen,
    `React.createElement(` UND der Kuerzel `h(`, `fontSize:12` UND
    `fontSize: 12`)
  * eine GEGENPROBE: dasselbe Wort in einem Block- und in einem
    Zeilenkommentar darf NICHT mitzaehlen.

Scheitert eine Probe, bricht das Werkzeug mit Rueckgabe 2 ab und nennt
KEINE Zahl. Ein Zaehler, der eine Schreibweise nicht kennt, meldet "kommt
nicht vor" - und das ist von einem echten Befund nicht zu unterscheiden.

AUFRUF
------
    python scripts/kiosk_tafeln_quelltext.py
    python scripts/kiosk_tafeln_quelltext.py --json docs/befunde/KIOSK_QUELLTEXT.json
"""
import io
import json
import os
import re
import sys

for _strom in (sys.stdout, sys.stderr):
    try:
        _strom.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)

import code_scan as CS  # noqa: E402

TAFELN = ["WochenplanTafel", "MonteurTafel", "StempelTafel"]

# Die Marken, mit denen dieses Haus einen abgewiesenen Lesezugriff kenntlich
# macht. Ein Kiosk, der keine davon ansieht, kann "nichts da" und "ich darf
# nichts lesen" nicht unterscheiden.
RLS_MARKEN = ["_rlsLeer", "__rlsFehler", "__EP_RLS", "_merkeRlsFehler"]

# Was als ERFOLGSPRUEFUNG gilt: eine Abfrage, die den Abruf beurteilt, bevor
# der Stand gesetzt wird.
ERFOLG_MUSTER = [r"Array\.isArray", r"\.ok\b", r"!==\s*null", r"\bstatus\b"]


# ═══════════════════════════════════════════════════════════════════════════
# Zeilennummern
# ═══════════════════════════════════════════════════════════════════════════
class Zeilen(object):
    def __init__(self, text):
        self._start = [0] + [m.end() for m in re.finditer("\n", text)]

    def __call__(self, pos):
        lo, hi = 0, len(self._start) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self._start[mid] <= pos:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1


# ═══════════════════════════════════════════════════════════════════════════
# DIE MELDER - jeder arbeitet auf (text, feld) und einem Bereich
# ═══════════════════════════════════════════════════════════════════════════
def melder_marken(text, feld, a, b, marken):
    """Positionen, an denen eine der Marken im CODE steht."""
    aus = []
    for mk in marken:
        for m in re.finditer(re.escape(mk), text):
            if a <= m.start() < b and feld[m.start()]:
                aus.append((m.start(), mk))
    return sorted(aus)


def melder_lesewege(text, feld, a, b):
    """Abrufe im Rumpf. Alle Schreibweisen dieses Hauses."""
    muster = [
        ("fetch", r"\bfetch\s*\("),
        ("API", r"\bAPI\.[A-Za-z_]\w*\s*\("),
        ("_sbGet", r"\b_sbGet[A-Za-z]*\s*\("),
        ("_sbPatch", r"\b_sbPatch\s*\("),
        ("kiosk-Helfer", r"\b_kiosk[A-Za-z]\w*\s*\("),
        ("_stLoad", r"\b_stLoad[A-Za-z]\w*\s*\("),
    ]
    aus = []
    for name, pat in muster:
        for m in re.finditer(pat, text):
            if a <= m.start() < b and feld[m.start()]:
                aus.append((m.start(), name, m.group(0).strip()))
    return sorted(aus)


def melder_rpc_namen(text, feld, a, b):
    """Die RPC-Namen, die im Rumpf aufgerufen werden.

    Der Name steht in einer ZEICHENKETTE ('/rpc/name'), also NICHT im
    Codefeld - gesucht wird darum an der Position des `/rpc/`, und dafuer
    wird die umgebende Zeichenkette gelesen. Die Frage "steht das im Code?"
    beantwortet das vorangehende `fetch(`, das sehr wohl Code ist.
    """
    aus = []
    for m in re.finditer(r"/rpc/([a-z_]+)", text):
        if a <= m.start() < b:
            aus.append((m.start(), m.group(1)))
    return sorted(set(aus))


def _rumpf_von(text, pos_auf):
    """Von der oeffnenden Klammer bis hinter die passende schliessende."""
    return CS._klammer_zu(text, pos_auf, text[pos_auf],
                          {"(": ")", "{": "}"}[text[pos_auf]])


def melder_leere_auffang(text, feld, a, b):
    """`catch(...){...}` im Bereich - und ob der Rumpf LEER ist.

    Leer heisst: nach Abzug von Kommentaren bleibt nur Weissraum. Ein
    Auffangzweig, der nichts tut, schluckt den Fehler - der Nutzer sieht
    denselben Bildschirm wie bei Erfolg.
    """
    aus = []
    for m in re.finditer(r"\bcatch\s*\(", text):
        p = m.start()
        if not (a <= p < b) or not feld[p]:
            continue
        pk = text.index("(", p)
        ende_p = _rumpf_von(text, pk)
        if ende_p < 0:
            continue
        j = ende_p
        while j < len(text) and text[j] in " \t\r\n":
            j += 1
        if j >= len(text) or text[j] != "{":
            continue
        ende_b = _rumpf_von(text, j)
        if ende_b < 0:
            continue
        rumpf = text[j + 1:ende_b - 1]
        # Kommentare abziehen: was im Rumpf KEIN Code ist, faellt weg.
        roh = "".join(rumpf[i] for i in range(len(rumpf))
                      if feld[j + 1 + i])
        aus.append((p, roh.strip() == "", rumpf.strip()[:70]))
    return aus


def melder_stand(text, feld, a, b):
    """Jedes `setInterval(`, das `setStand(` enthaelt - mit/ohne Pruefung."""
    aus = []
    for m in re.finditer(r"\bsetInterval\s*\(", text):
        p = m.start()
        if not (a <= p < b) or not feld[p]:
            continue
        pk = text.index("(", p)
        ende = _rumpf_von(text, pk)
        if ende < 0:
            continue
        rumpf = text[pk:ende]
        if "setStand(" not in rumpf:
            continue
        geprueft = [pat for pat in ERFOLG_MUSTER if re.search(pat, rumpf)]
        aus.append((p, bool(geprueft), geprueft, len(rumpf)))
    return aus


_FONT_PAT = r"fontSize\s*:\s*(\d+)\b"
_CLAMP_PAT = r"fontSize\s*:\s*[\"']clamp\(\s*(\d+)px"


def melder_schrift(text, feld, a, b):
    """Alle Schriftgroessen im Rumpf: feste Zahlen und clamp-Untergrenzen."""
    fest, clamp = [], []
    for m in re.finditer(_FONT_PAT, text):
        if a <= m.start() < b and feld[m.start()]:
            fest.append((m.start(), int(m.group(1))))
    for m in re.finditer(_CLAMP_PAT, text):
        if a <= m.start() < b and feld[m.start()]:
            clamp.append((m.start(), int(m.group(1))))
    return fest, clamp


def melder_farbpaare(text, feld, a, b):
    """Stil-Objekte, die color UND background/backgroundColor SELBST setzen.

    Nur diese sind aus dem Quelltext heraus beurteilbar. Ein Objekt, das nur
    `color` setzt, erbt seinen Hintergrund - darueber sagt der Quelltext
    nichts, und eine Zahl daraus waere erfunden.
    """
    aus = []
    for m in re.finditer(r"style\s*:\s*\{", text):
        p = m.start()
        if not (a <= p < b) or not feld[p]:
            continue
        auf = text.index("{", p)
        ende = _rumpf_von(text, auf)
        if ende < 0 or ende - auf > 4000:
            continue
        blk = text[auf:ende]
        vg = re.search(r"(?<!background)[Cc]olor\s*:\s*['\"](#[0-9a-fA-F]{3,8})['\"]", blk)
        hg = re.search(r"background(?:Color)?\s*:\s*['\"](#[0-9a-fA-F]{3,8})['\"]", blk)
        if vg and hg:
            aus.append((p, vg.group(1), hg.group(1)))
    return aus


def _lum(hexf):
    hexf = hexf.lstrip("#")
    if len(hexf) == 3:
        hexf = "".join(c * 2 for c in hexf)
    hexf = hexf[:6]
    try:
        r, g, b = (int(hexf[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    except ValueError:
        return None
    def f(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def kontrast(vg, hg):
    a, b = _lum(vg), _lum(hg)
    if a is None or b is None:
        return None
    hell, dunkel = max(a, b), min(a, b)
    return round((hell + 0.05) / (dunkel + 0.05), 2)


# ═══════════════════════════════════════════════════════════════════════════
# CSS: Stilbloecke gehaertet herausschneiden
# ═══════════════════════════════════════════════════════════════════════════
def stilbloecke(text):
    """Die <style>-Bloecke - nach der Regel: VOR einem </style> gilt das
    LETZTE <style>.

    Das naheliegende Muster `<style[^>]*>(.*?)</style>` ist an dieser Datei
    falsch: sie fuehrt ein `<style>` MITTEN in einem deutschen Kommentar,
    und das naive Muster paart es mit dem naechsten echten `</style>` -
    rund 1700 Zeilen JavaScript gelten dann als CSS.
    """
    aufs = [m.end() for m in re.finditer(r"<style[^>]*>", text)]
    zus = [m.start() for m in re.finditer(r"</style>", text)]
    aus = []
    for z in zus:
        kand = [a for a in aufs if a < z]
        if not kand:
            continue
        aus.append((max(kand), z))
    return aus


def gcss_block(text):
    """Der Laufzeit-Stilblock GCSS() - ein Vorlagenliteral, kein <style>."""
    m = re.search(r"const\s+GCSS\s*=\s*\(\)\s*=>\s*`", text)
    if not m:
        return None
    a = m.end()
    i = a
    while i < len(text):
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == "`":
            return (a, i)
        i += 1
    return None


def wichtig_regeln(css, quelle):
    """Jede font-size-Regel mit !important, samt @media-Bedingung.

    Die Bedingung entscheidet, ob die Regel am Kiosk (>= 600 px breit)
    ueberhaupt greift. `@media (max-width: 600px)` greift dort NICHT -
    eine Regel darin ist fuer die Wandtafel ohne Belang.
    """
    aus = []
    tiefe_bed = []
    i = 0
    n = len(css)
    stand = 0
    while i < n:
        c = css[i]
        if c == "@" and css[i:i + 6] == "@media":
            j = css.index("{", i)
            tiefe_bed.append((css[i + 6:j].strip(), stand))
            stand += 1
            i = j + 1
            continue
        if c == "{":
            stand += 1
            i += 1
            continue
        if c == "}":
            stand -= 1
            tiefe_bed = [t for t in tiefe_bed if t[1] <= stand]
            i += 1
            continue
        i += 1
    # Zweiter Lauf: Regeln einsammeln, Bedingung ueber Klammerstand
    tiefe_bed = []
    stand = 0
    i = 0
    letzter_selektor_start = 0
    while i < n:
        c = css[i]
        if c == "@" and css[i:i + 6] == "@media":
            j = css.index("{", i)
            tiefe_bed.append((css[i + 6:j].strip(), stand))
            stand += 1
            i = j + 1
            letzter_selektor_start = i
            continue
        if c == "{":
            sel = css[letzter_selektor_start:i].strip()
            j = css.find("}", i)
            if j < 0:
                break
            koerper = css[i + 1:j]
            if re.search(r"font-size[^;}]*!important", koerper):
                bed = " AND ".join(t[0] for t in tiefe_bed)
                gr = re.search(r"font-size\s*:\s*([^;!]+)!important", koerper)
                aus.append({
                    "quelle": quelle,
                    "selektor": re.sub(r"\s+", " ", sel)[:120],
                    "wert": (gr.group(1).strip() if gr else "?"),
                    "bedingung": bed,
                    "gilt_ab_600": _gilt_ab_600(bed),
                })
            stand += 1
            i = j + 1
            stand -= 1
            letzter_selektor_start = i
            continue
        if c == "}":
            stand -= 1
            tiefe_bed = [t for t in tiefe_bed if t[1] <= stand]
            i += 1
            letzter_selektor_start = i
            continue
        i += 1
    return aus


def _gilt_ab_600(bed):
    """Greift diese @media-Bedingung bei 1280 px Kioskbreite?"""
    if not bed:
        return True
    for m in re.finditer(r"max-width\s*:\s*(\d+)px", bed):
        if int(m.group(1)) < 1280:
            return False
    if "pointer: coarse" in bed or "pointer:coarse" in bed:
        # Kann am Touch-Panel greifen, am TV nicht. Unentschieden.
        return "vielleicht"
    return True


# ═══════════════════════════════════════════════════════════════════════════
# 🔴 SELBSTPROBE
# ═══════════════════════════════════════════════════════════════════════════
PROBE_JS = (
    "function ProbeTafel(props){\n"
    "  const h=React.createElement;\n"
    "  React.createElement('div',{style:{fontSize:13,color:'#94a3b8',"
    "background:'#0f172a'}});\n"
    "  h(\"span\",{style:{fontSize: 9,color:\"#777777\","
    "backgroundColor:\"#888888\"}});\n"
    "  const a=_rlsLeer(x); const b=y.__rlsFehler;\n"
    "  fetch(SB_REST+'/rpc/probe_eins');\n"
    "  API.getDinge();\n"
    "  _sbGet('tabelle');\n"
    "  _kioskWeekArbeitsscheine();\n"
    "  try{ q(); }catch(e){}\n"
    "  try{ q(); }catch(e){ meldeEs(e); }\n"
    "  setInterval(()=>{ setStand(new Date()); },60000);\n"
    "  setInterval(()=>{ if(Array.isArray(r)) setStand(new Date()); },60000);\n"
    "  /* GEGENPROBE, Blockkommentar: hier stehen _rlsLeer( und __rlsFehler\n"
    "     und fontSize:99 und React.createElement('div' und h('span' und\n"
    "     fetch( und API.getDinge( - nichts davon darf mitzaehlen. */\n"
    "  // GEGENPROBE, Zeilenkommentar: _rlsLeer( __rlsFehler fontSize:98\n"
    "  return null;\n"
    "}\n"
)

PROBE_CSS_JA = "table { font-size: 12px !important; }"
PROBE_CSS_NEIN = "@media (max-width: 600px) { td { font-size: 11px !important; } }"


def selbstprobe():
    """Jeder Melder an einem selbstgebauten Text. Gibt (ok, zeilen) zurueck."""
    z = []
    ok = True
    t = PROBE_JS
    feld = CS._ist_code_roh(t)      # bewusst roh: der Probetext ist klein,
    a, b = 0, len(t)                # und die Eichung von `ist_code` haengt
    #                                 an index.html-Merkmalen, die hier fehlen.

    def sagt(name, ist, soll):
        nonlocal ok
        gut = (ist == soll)
        if not gut:
            ok = False
        z.append("  %-34s %-18s soll %-18s %s"
                 % (name, ist, soll, "OK" if gut else "GESCHEITERT"))

    # 1. RLS-Marken: zwei Formen im Code, vier in Kommentaren.
    sagt("RLS-Marken (Koeder je Form)",
         len(melder_marken(t, feld, a, b, RLS_MARKEN)), 2)

    # 2. Lesewege: fetch, API., _sbGet, _kioskWeekArbeitsscheine = 4
    #    (im Kommentar stehen fetch( und API.getDinge( noch einmal).
    sagt("Lesewege (4 Formen)", len(melder_lesewege(t, feld, a, b)), 4)

    # 3. RPC-Namen: genau einer, und der steht in einer ZEICHENKETTE.
    sagt("RPC-Name aus Zeichenkette",
         [n for _, n in melder_rpc_namen(t, feld, a, b)], ["probe_eins"])

    # 4. Auffangzweige: zwei, davon EINER leer.
    fang = melder_leere_auffang(t, feld, a, b)
    sagt("catch gesamt", len(fang), 2)
    sagt("catch davon leer", sum(1 for f in fang if f[1]), 1)

    # 5. Stand: zwei Takte, einer ohne Pruefung.
    st = melder_stand(t, feld, a, b)
    sagt("setInterval mit setStand", len(st), 2)
    sagt("davon OHNE Erfolgspruefung",
         sum(1 for s in st if not s[1]), 1)

    # 6. Schrift: fontSize:13 und fontSize: 9 im Code; 99/98 im Kommentar.
    fest, clamp = melder_schrift(t, feld, a, b)
    sagt("fontSize beide Schreibweisen",
         sorted(v for _, v in fest), [9, 13])

    # 7. Farbpaare: zwei Stil-Objekte setzen beides.
    paare = melder_farbpaare(t, feld, a, b)
    sagt("Farbpaare (beide Zitatformen)", len(paare), 2)
    sagt("Kontrast #777777 auf #888888 < 3",
         any(kontrast(v, g) is not None and kontrast(v, g) < 3.0
             for _, v, g in paare), True)

    # 8. CSS: eine Regel greift am Kiosk, eine nicht.
    r_ja = wichtig_regeln(PROBE_CSS_JA, "probe")
    r_nein = wichtig_regeln(PROBE_CSS_NEIN, "probe")
    sagt("CSS-Regel ohne @media gilt", [r["gilt_ab_600"] for r in r_ja], [True])
    sagt("CSS-Regel max-width:600 gilt nicht",
         [r["gilt_ab_600"] for r in r_nein], [False])

    # 9. GEGENPROBE IN DIE ANDERE RICHTUNG: ein Melder, dem man die Sicht
    #    nimmt, MUSS rot werden. Ohne diese Zeile waere "alle Proben gruen"
    #    auch dann wahr, wenn die Proben selbst nichts messen.
    blind = bytearray(len(t))        # nichts ist Code
    if melder_marken(t, blind, a, b, RLS_MARKEN):
        z.append("  Blindprobe                         GESCHEITERT "
                 "(blinder Melder findet trotzdem etwas)")
        ok = False
    else:
        z.append("  Blindprobe (blinder Melder = 0)    OK")

    return ok, z


# ═══════════════════════════════════════════════════════════════════════════
def main(json_ziel=None):
    ok, zeilen = selbstprobe()
    print("SELBSTPROBE")
    for l in zeilen:
        print(l)
    if not ok:
        print("\nABBRUCH: eine Probe ist gescheitert. Es wird KEINE Zahl "
              "genannt - ein Melder, der seinen eigenen Koeder nicht "
              "findet, meldet fuer jede Datei der Welt 'sauber'.")
        return 2
    print("  -> alle Proben bestanden\n")

    pfad = os.path.join(WURZEL, "index.html")
    with io.open(pfad, encoding="utf-8", newline="") as f:
        text = f.read()
    feld = CS.ist_code(text)
    zl = Zeilen(text)

    eich_ok, gef, erw = CS.eichen(text)
    if not eich_ok:
        print("ABBRUCH: code_scan-Eichung an index.html gescheitert "
              "(%d von %d)." % (gef, erw))
        return 2
    print("code_scan-Eichung an index.html: %d von %d\n" % (gef, erw))

    erg = {"datei": pfad, "zeichen": len(text), "tafeln": {}}

    for name in TAFELN:
        m = re.search(r"function\s+" + name + r"\s*\(props\)\s*\{", text)
        if not m:
            print("ABBRUCH: %s nicht gefunden." % name)
            return 2
        auf = text.index("{", m.end() - 1)
        ende = _rumpf_von(text, auf)
        a, b = m.start(), ende
        d = {"zeile_von": zl(a), "zeile_bis": zl(b), "bytes": b - a}

        d["lesewege"] = [{"zeile": zl(p), "art": art, "text": txt}
                         for p, art, txt in melder_lesewege(text, feld, a, b)]
        d["rpc"] = sorted(set(n for _, n in melder_rpc_namen(text, feld, a, b)))
        d["rls_marken"] = [{"zeile": zl(p), "marke": mk}
                           for p, mk in melder_marken(text, feld, a, b,
                                                      RLS_MARKEN)]
        fang = melder_leere_auffang(text, feld, a, b)
        d["catch_gesamt"] = len(fang)
        d["catch_leer"] = [{"zeile": zl(p), "rumpf": r}
                           for p, leer, r in fang if leer]
        d["stand_takte"] = [{"zeile": zl(p), "geprueft": g, "muster": mu}
                            for p, g, mu, _ in melder_stand(text, feld, a, b)]
        fest, clamp = melder_schrift(text, feld, a, b)
        hist = {}
        for _, v in fest:
            hist[v] = hist.get(v, 0) + 1
        d["schrift_fest"] = dict(sorted(hist.items()))
        d["schrift_unter_16"] = sum(n for v, n in hist.items() if v < 16)
        d["schrift_unter_24"] = sum(n for v, n in hist.items() if v < 24)
        d["schrift_gesamt"] = len(fest)
        d["clamp_minima"] = sorted(set(v for _, v in clamp))
        paare = melder_farbpaare(text, feld, a, b)
        d["farbpaare"] = []
        for p, vg, hg in paare:
            k = kontrast(vg, hg)
            d["farbpaare"].append({"zeile": zl(p), "vg": vg, "hg": hg,
                                   "kontrast": k})
        d["farbpaare_unter_4_5"] = sum(
            1 for x in d["farbpaare"]
            if x["kontrast"] is not None and x["kontrast"] < 4.5)
        erg["tafeln"][name] = d

    # ── CSS ───────────────────────────────────────────────────────────────
    regeln = []
    for (a, b) in stilbloecke(text):
        regeln += wichtig_regeln(text[a:b], "<style> Z.%d" % zl(a))
    g = gcss_block(text)
    if g:
        regeln += wichtig_regeln(text[g[0]:g[1]], "GCSS() Z.%d" % zl(g[0]))
    erg["css_important_fontsize"] = regeln
    erg["css_gilt_am_kiosk"] = [r for r in regeln if r["gilt_ab_600"] is True]

    # ── Ausgabe ───────────────────────────────────────────────────────────
    for name in TAFELN:
        d = erg["tafeln"][name]
        print("═" * 74)
        print("%s   Zeile %d-%d  (%d Byte)"
              % (name, d["zeile_von"], d["zeile_bis"], d["bytes"]))
        print("  Lesewege        : %d  (%s)"
              % (len(d["lesewege"]),
                 ", ".join(sorted(set(x["art"] for x in d["lesewege"])))
                 or "keine"))
        print("  RPC             : %s" % (", ".join(d["rpc"]) or "keine"))
        print("  RLS-Marken      : %d %s"
              % (len(d["rls_marken"]),
                 "  <-- die Tafel kann 'leer' und 'abgewiesen' NICHT "
                 "unterscheiden" if not d["rls_marken"] else ""))
        print("  catch           : %d, davon LEER %d %s"
              % (d["catch_gesamt"], len(d["catch_leer"]),
                 ("(Zeilen " + ", ".join(str(x["zeile"])
                                         for x in d["catch_leer"]) + ")")
                 if d["catch_leer"] else ""))
        for s in d["stand_takte"]:
            print("  Stand-Takt Z.%d  : %s"
                  % (s["zeile"],
                     ("nach Erfolgspruefung (%s)" % ", ".join(s["muster"]))
                     if s["geprueft"]
                     else "OHNE Erfolgspruefung  <-- das ist die UHR, "
                          "nicht das Datenalter"))
        if not d["stand_takte"]:
            print("  Stand-Takt      : keiner")
        print("  Schrift         : %d Angaben, %d unter 24 px, %d unter 16 px"
              % (d["schrift_gesamt"], d["schrift_unter_24"],
                 d["schrift_unter_16"]))
        print("                    Histogramm %s" % d["schrift_fest"])
        if d["clamp_minima"]:
            print("                    clamp-Untergrenzen %s"
                  % d["clamp_minima"])
        print("  Farbpaare       : %d im Quelltext beurteilbar, "
              "%d unter 4,5:1"
              % (len(d["farbpaare"]), d["farbpaare_unter_4_5"]))
        for x in d["farbpaare"]:
            if x["kontrast"] is not None and x["kontrast"] < 4.5:
                print("                    Z.%d  %s auf %s = %.2f:1"
                      % (x["zeile"], x["vg"], x["hg"], x["kontrast"]))

    print("═" * 74)
    print("CSS: %d font-size-Regeln mit !important, davon %d greifen bei "
          "Kioskbreite (>= 1280 px)"
          % (len(regeln), len(erg["css_gilt_am_kiosk"])))
    for r in erg["css_gilt_am_kiosk"]:
        print("   %-46s %-10s %s"
              % (r["selektor"][:46], r["wert"], r["quelle"]))

    if json_ziel:
        with io.open(json_ziel, "w", encoding="utf-8", newline="") as f:
            f.write(json.dumps(erg, ensure_ascii=False, indent=1))
        print("\ngeschrieben: %s" % json_ziel)
    return 0


if __name__ == "__main__":
    ziel = None
    if "--json" in sys.argv:
        ziel = sys.argv[sys.argv.index("--json") + 1]
    sys.exit(main(ziel))
