# -*- coding: utf-8 -*-
"""Abtaster fuer BEDIENELEMENTE in index.html - Klassen (a), (b), (c).

Er misst die Menge, die v3.9.957 (Symbolzeichen) und v3.9.958 (Emoji-Literal)
ausdruecklich AUSGELASSEN haben: Knoepfe mit Text-, Variablen- oder
gemischtem Inhalt, und alles, was gar kein `button` ist.

WAS ER ANDERS MACHT ALS DIE BEIDEN VORGAENGER
─────────────────────────────────────────────
1. Er kennt BEIDE Schreibweisen. `React.createElement('button'` UND den
   lokalen Kuerzel `h('button'` (`const h=React.createElement` steht 13 mal
   in Komponentenruempfen). Die Abtaster von v957/v958 suchten nur
   `createElement('button'` - 97 Knoepfe haben sie NIE gesehen.
2. Er kennt BEIDE Anfuehrungszeichen. v958 las den Inhalt mit
   `re.match(r'"..."')` - EINFACH gesetzte Inhalte (`,'✕')`) fielen durch.
3. Er liest ALLE Kinder, nicht nur das erste - und bei einem verschachtelten
   Element auch dessen Kinder. Ein Knopf `,'🏖️',h('div',{},'Urlaub')` hat
   einen Namen; ein Knopf `,"🗑️ ",isMob?"Löschen":""` hat ihn NUR auf dem
   Telefon. Wer nur das erste Kind ansieht, urteilt in beide Richtungen
   falsch.
4. Er klammert das Eigenschaftenobjekt mit einer KLAMMERZAEHLUNG aus, die
   ueber die Code-Maske von code_scan laeuft - Zeichenketten und Kommentare
   koennen die Zaehlung damit nicht aus dem Tritt bringen. Genau daran ist
   die erste Fassung der v958-Messung dreimal gescheitert (Z10166, Z20541,
   Z20867).

AUFRUF
──────
    python scripts/bedienelemente_scan.py            # Uebersicht
    python scripts/bedienelemente_scan.py json       # alles maschinenlesbar
    python scripts/bedienelemente_scan.py koeder     # Selbstprobe
"""
import bisect
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from code_scan import ist_code, eichen  # noqa: E402

# 🔴 Der Pfad ist ueberschreibbar (BEDIENELEMENTE_PFAD). WARUM:
# Waehrend dieser Messung hat ein anderer Schreiber `index.html` geaendert -
# 3.671.906 -> 3.708.615 Bytes, v3.9.959 -> v3.9.960, mitten im Lauf. Zwei
# Laeufe gaben dadurch zwei verschiedene Zahlen (295/443/47 und 297/442/46),
# und ZEILENNUMMERN aus dem ersten Lauf zeigen in der neuen Datei woandershin.
# Eine Messung an einem Baum, an dem gearbeitet wird, ist keine Messung.
# Deshalb: auf eine EINGEFRORENE Abschrift zeigen und den Stand nennen.
PFAD = os.environ.get("BEDIENELEMENTE_PFAD") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "index.html")

# Die zwei Schreibweisen. Vor `h(` gehoert die Rueckschau, sonst treffen
# `search(`, `.h(` und `push(` mit.
AUFRUF = re.compile(
    r"(?:(?<![A-Za-z0-9_$.])React\.createElement"
    r"|(?<![A-Za-z0-9_$.])createElement"
    r"|(?<![A-Za-z0-9_$.])h)\s*\(\s*")

ECHTE_BEDIENELEMENTE = {"button", "a", "input", "select", "textarea", "option"}

# Zeichen, die fuer eine Vorlesehilfe KEIN Wort sind: Symbolzeichen, Emoji,
# Varianten-Waehler, Leerraum, Trennstriche. Bewusst eine Aufzaehlung und
# keine Unicode-Kategorie - eine Kategorie traefe auch Buchstaben mit
# Akzent, und dann waere "Löschen" kein Text mehr.
STUMME_ZEICHEN = (
    "\\U0001F000-\\U0001FAFF"          # Emoji-Ebenen
    "\u2190-\u21ff"                    # Pfeile
    "\u2300-\u23ff"                    # Technische Zeichen (⏰ ⏳ ⌀)
    "\u2400-\u27bf"                    # Dingbats (✕ ✓ ❌ ➕)
    "\u2b00-\u2bff"                    # weitere Pfeile/Formen
    "\u25a0-\u25ff"                    # Geometrie (◀ ▶ ▲ ▼)
    "\u2600-\u26ff"                    # Sonstige Symbole
    "\u3030\u303d\u00a9\u00ae\u2122"
    "\u2610-\u2637\u22ee\u22ef\u00d7\u00b7"
    "\ufe0f\u200d\u2028\u2029"
    "\\s\u00a0\u2013\u2014\u2026\uff0b"
)
NUR_STUMM = re.compile("^[" + STUMME_ZEICHEN + "]*$")
HAT_EMOJI = re.compile("[" + STUMME_ZEICHEN.replace("\\s\u00a0", "")
                       .replace("\u2013\u2014\u2026", "") + "]")


def lies():
    roh = io.open(PFAD, encoding="utf-8", newline="").read()
    if len(roh) < 3_000_000:
        raise AssertionError(
            "index.html hat nur %d Bytes - Datenverlust, keine Namensfrage. "
            "Eine leere Datei hat null namenlose Knoepfe." % len(roh))
    return roh


def maske(text):
    """Code-Maske, EICHPROBE zwingend. Ohne Eichung keine Auskunft."""
    eichen(text)
    return ist_code(text)


# ───────────────────── Zerlegung eines Aufrufs ─────────────────────
def _vor(text, mk, i):
    """Naechste bedeutsame Position ab i. Kommentare uebersprungen."""
    n = len(text)
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
            continue
        if not mk[i]:
            if c in "\"'`":
                return i          # eine Zeichenkette IST ein Argument
            i += 1                # Kommentar
            continue
        return i
    return n


def _klammer_ende(text, mk, i, offen, zu):
    """Position HINTER der passenden schliessenden Klammer.

    Gezaehlt wird nur an Code-Positionen - ein `{` in einem Knopftext oder
    in einem Kommentar kann die Zaehlung nicht verschieben.
    """
    n, tiefe = len(text), 0
    while i < n:
        if mk[i]:
            c = text[i]
            if c == offen:
                tiefe += 1
            elif c == zu:
                tiefe -= 1
                if tiefe == 0:
                    return i + 1
        i += 1
    return None


def _arg_ende(text, mk, i):
    """(Ende, war_komma, abgeschlossen) fuer das Argument ab i."""
    n, tiefe = len(text), 0
    while i < n:
        if mk[i]:
            c = text[i]
            if c in "([{":
                tiefe += 1
            elif c in ")]}":
                if tiefe == 0:
                    return i, False, True
                tiefe -= 1
            elif c == "," and tiefe == 0:
                return i, True, True
        i += 1
    return n, False, False


def _string_ende(text, i):
    """Position hinter dem Schlusszeichen der Zeichenkette an i."""
    q, n, j = text[i], len(text), i + 1
    while j < n:
        if text[j] == "\\":
            j += 2
            continue
        if text[j] == q:
            return j + 1
        j += 1
    return None


_FN_CACHE = {}


def _fn_tabelle(text):
    """Alle `function NAME(`-Stellen EINMAL.

    Die erste Fassung rief pro Stelle ein `re.finditer` ueber `text[:p]` -
    7543 Durchlaeufe ueber bis zu 3,6 MB, und der Lauf lief in die
    Zeitgrenze. Eine Messung, die nicht zu Ende laeuft, liefert keine Zahl.
    """
    key = (len(text), text[:64])
    if key not in _FN_CACHE:
        _FN_CACHE[key] = [(m.start(), m.group(1)) for m in
                          re.finditer(r"function\s+([A-Za-z_]\w*)\s*\(", text)]
    return _FN_CACHE[key]


def _ansicht(text, p):
    tab = _fn_tabelle(text)
    i = bisect.bisect_left(tab, (p,)) - 1
    return tab[i][1] if i >= 0 else "?"


def _zerlege(text, mk, m_end):
    """Zerlegt einen Aufruf ab dem ersten Argument.

    Gibt (tag, props, kinder, ende) oder None. `kinder` ist eine Liste von
    (anfang, ende) im Text.
    """
    i = m_end
    if i >= len(text) or text[i] not in "\"'`":
        return None                        # Komponente, kein HTML-Tag
    se = _string_ende(text, i)
    if se is None:
        return None
    tag = text[i + 1:se - 1]
    if not re.match(r"^[a-z][a-z0-9]*$", tag):
        return None
    j = _vor(text, mk, se)
    if j >= len(text) or text[j] != ",":
        return (tag, "", [], j)            # nur das Tag
    j = _vor(text, mk, j + 1)
    if j < len(text) and mk[j] and text[j] == "{":
        pe = _klammer_ende(text, mk, j, "{", "}")
        if pe is None:
            return None
        props, nach = text[j:pe], pe
    else:
        ae, _, ok = _arg_ende(text, mk, j)
        if not ok:
            return None
        props, nach = text[j:ae], ae
    kinder = []
    k = _vor(text, mk, nach)
    while k < len(text) and text[k] == ",":
        k = _vor(text, mk, k + 1)
        ke, komma, ok = _arg_ende(text, mk, k)
        if not ok:
            break
        if text[k:ke].strip():
            kinder.append((k, ke))
        if not komma:
            k = ke
            break
        k = ke
    return (tag, props, kinder, k)


def stellen(text, mk):
    """Jede Elementerzeugung mit LITERALEM Tag-Namen."""
    aus = []
    for m in AUFRUF.finditer(text):
        a = m.start()
        if not mk[a]:
            continue
        z = _zerlege(text, mk, m.end())
        if z is None:
            continue
        tag, props, kinder, ende = z
        aus.append(dict(tag=tag, pos=a, zeile=text.count("\n", 0, a) + 1,
                        ansicht=_ansicht(text, a), props=props,
                        kinder=[text[x:y].strip() for x, y in kinder],
                        _kspans=kinder, ende=ende))
    return aus


# ───────────────────── Beurteilung des Namens ─────────────────────
def _literal_text(text, mk, a, b):
    """Ist das Argument [a,b) eine einzige Zeichenkette? Dann ihr Inhalt."""
    if a >= len(text) or text[a] not in "\"'":
        return None
    se = _string_ende(text, a)
    if se is None or text[se:b].strip():
        return None
    return text[a + 1:se - 1]


def namensbeitrag(text, mk, a, b, tiefe=0):
    """Was dieses Kind zum Namen beitraegt.

    "immer"    steuert immer sichtbaren Text bei
    "manchmal" kann Text beitragen, kann aber leer/stumm sein
    "nie"      ist nur Symbol/Emoji oder leer
    """
    if tiefe > 4:
        return "manchmal"
    roh = text[a:b].strip()
    if not roh:
        return "nie"
    lit = _literal_text(text, mk, a, b)
    if lit is not None:
        return "nie" if NUR_STUMM.match(lit) else "immer"
    # Verschachteltes Element: seine eigenen Kinder ansehen.
    m = AUFRUF.match(text, a)
    if m:
        z = _zerlege(text, mk, m.end())
        if z is not None:
            tag, props, kinder, _ = z
            if re.search(r"\baria-label\b|\btitle\s*:", props):
                return "immer"
            beitraege = [namensbeitrag(text, mk, x, y, tiefe + 1)
                         for x, y in kinder]
            if "immer" in beitraege:
                return "immer"
            return "manchmal" if "manchmal" in beitraege else "nie"
        return "manchmal"
    # Ternaer auf Tiefe 0: BEIDE Zweige muessen Text geben.
    zw = _ternaer_zweige(text, mk, a, b)
    if zw is not None:
        beitraege = [namensbeitrag(text, mk, x, y, tiefe + 1) for x, y in zw]
        if all(v == "immer" for v in beitraege):
            return "immer"
        if all(v == "nie" for v in beitraege):
            return "nie"
        return "manchmal"
    # Verkettung mit einem festen Textstueck?
    if re.search(r"[\"'][^\"']*[A-Za-zÄÖÜäöüß][^\"']*[\"']", roh):
        return "immer"
    return "manchmal"


def _ternaer_zweige(text, mk, a, b):
    """(dann, sonst) als Spannen, wenn [a,b) ein Ternaer auf Tiefe 0 ist."""
    tiefe, q, kolon = 0, -1, -1
    i = a
    while i < b:
        if mk[i]:
            c = text[i]
            if c in "([{":
                tiefe += 1
            elif c in ")]}":
                tiefe -= 1
            elif c == "?" and tiefe == 0 and text[i:i + 2] not in ("?.", "??"):
                if q < 0:
                    q = i
            elif c == ":" and tiefe == 0 and q >= 0 and kolon < 0:
                kolon = i
        i += 1
    if q < 0 or kolon < 0:
        return None
    return [(q + 1, kolon), (kolon + 1, b)]


def hat_namen(props):
    return bool(re.search(r"\btitle\s*:", props)) or "aria-label" in props


def beurteile(text, mk, s):
    """Namensbefund fuer ein Bedienelement."""
    if hat_namen(s["props"]):
        return "benannt-prop"
    if "aria-labelledby" in s["props"]:
        return "benannt-prop"
    beitraege = [namensbeitrag(text, mk, x, y) for x, y in s["_kspans"]]
    if "immer" in beitraege:
        return "benannt-text"
    if "manchmal" in beitraege:
        return "manchmal-stumm"
    return "immer-stumm"


def schreibweise(text, s):
    """createElement-Form oder h(-Kuerzel.

    🔴 Die erste Fassung nahm `text[pos:pos+18]` - das ergibt
    "React.createElemen" OHNE das letzte t, also traf `"createElement" in`
    nie, und der Zaehler meldete 793 h( und 5 createElement. Eine Zahl, die
    der Augenschein widerlegt (die Datei fuehrt 708 `createElement('button'`),
    ist ein Zaehlerfehler, kein Befund.
    """
    return ("createElement" if text[s["pos"]:s["pos"] + 40]
            .startswith(("React.createElement", "createElement")) else "h(")


# ───────────────────────── Klassen ─────────────────────────
def klasse_a(text, mk, st):
    """Knopf, dessen Name von einer VARIABLE haengt (kann leer werden)."""
    aus = []
    for s in st:
        if s["tag"] not in ("button", "a"):
            continue
        if beurteile(text, mk, s) != "manchmal-stumm":
            continue
        aus.append(s)
    return aus


def klasse_a_immer(text, mk, st):
    """Knopf, der NIE Text zeigt und keinen Namen in den Props hat."""
    return [s for s in st if s["tag"] in ("button", "a")
            and beurteile(text, mk, s) == "immer-stumm"]


def klasse_b(text, mk, st):
    """Knopf, dessen sichtbarer Inhalt Emoji PLUS Text ist."""
    aus = []
    for s in st:
        if s["tag"] != "button":
            continue
        lits = []
        for x, y in s["_kspans"]:
            lit = _literal_text(text, mk, x, y)
            if lit:
                lits.append(lit)
        ganz = "".join(lits)
        if not ganz or not HAT_EMOJI.search(ganz):
            continue
        if NUR_STUMM.match(ganz):
            continue                       # reines Emoji -> v957/v958
        aus.append(dict(s, sichtbar=ganz.strip()))
    return aus


def klasse_c_onclick(st):
    """onClick auf einem Element, das kein button/a/input/select ist."""
    aus = []
    for s in st:
        if s["tag"] in ECHTE_BEDIENELEMENTE:
            continue
        mo = re.search(r"\bonClick\s*:\s*", s["props"])
        if not mo:
            continue
        rumpf = s["props"][mo.end():mo.end() + 90]
        # 🔴 Ein `onClick: e=>e.stopPropagation()` ist KEIN Bedienelement,
        # sondern ein Klick-Schlucker: er verhindert, dass der Klick beim
        # Elternelement ankommt. Ein role/tabIndex dort waere falsch - er
        # baute einen Halt in der Tastaturreihenfolge, der nichts tut.
        # Dieselbe Sorte Ausnahme wie die Statusanzeige in v957.
        schlucker = bool(re.match(
            r"(?:e|ev|evt|event)\s*=>\s*(?:e|ev|evt|event)\s*\.\s*"
            r"stopPropagation\s*\(\s*\)\s*(?:,|\}|$)", rumpf))
        aus.append(dict(s,
                        role=bool(re.search(r"\brole\s*:", s["props"])),
                        tabIndex=bool(re.search(r"\btabIndex\s*:",
                                                s["props"])),
                        onKey=bool(re.search(r"\bonKey(Down|Press|Up)\s*:",
                                             s["props"])),
                        schlucker=schlucker))
    return aus


def label_bereiche(text, mk, st):
    return [(s["pos"], s["ende"]) for s in st if s["tag"] == "label"]


def _naechste_label_schrift(text, mk, st_sorted, pos):
    """Text des NAECHSTEN `label`-Elements VOR pos - als Namensvorschlag.

    🔴 Das ist ein ABGELESENER Vorschlag, KEIN Befund: ein `label`-Element
    ohne `htmlFor` und ein `input` ohne `id` stehen fuer eine Vorlesehilfe
    in keiner Beziehung, auch wenn sie im Bild uebereinander liegen. Die
    Schrift daneben sagt, wie das Feld HEISST - dass sie es nicht BENENNT,
    ist genau der Befund.
    """
    best = None
    for s in st_sorted:
        if s["pos"] >= pos:
            break
        if s["tag"] != "label":
            continue
        if pos - s["pos"] > 1400:
            continue
        for x, y in s["_kspans"]:
            lit = _literal_text(text, mk, x, y)
            if lit and not NUR_STUMM.match(lit):
                best = lit.strip()
    return best


def klasse_c_eingaben(text, mk, st):
    """input/select/textarea und ihr Name."""
    lb = label_bereiche(text, mk, st)
    st_sorted = sorted(st, key=lambda s: s["pos"])
    aus = []
    for s in st:
        if s["tag"] not in ("input", "select", "textarea"):
            continue
        p = s["props"]
        mt = re.search(r"type\s*:\s*[\"']([a-z]+)[\"']", p)
        typ = mt.group(1) if mt else ""
        in_label = any(a < s["pos"] < b for a, b in lb)
        mph = re.search(r"placeholder\s*:\s*[\"']([^\"']*)[\"']", p)
        # `htmlFor` + `id` waere die programmatische Verbindung.
        mfor = re.search(r"\bid\s*:\s*[\"']([^\"']*)[\"']", p)
        verbunden = bool(mfor and re.search(
            r"htmlFor\s*:\s*[\"']" + re.escape(mfor.group(1)) + r"[\"']",
            text))
        aus.append(dict(
            s, typ=typ, in_label=in_label,
            placeholder=(mph.group(1) if mph else ""),
            verbunden=verbunden,
            labelschrift=_naechste_label_schrift(text, mk, st_sorted,
                                                 s["pos"]),
            ok=(hat_namen(p) or in_label or "aria-labelledby" in p
                or verbunden)))
    return aus


# ─────────────────────────── KOEDER ───────────────────────────
def _anker(roh):
    for kand in ("React.createElement('div', { style: { minHeight",
                 "React.createElement('button'", "h('button'"):
        if kand in roh:
            return kand
    raise AssertionError("Kein Anker fuer den Koeder gefunden.")


KOEDER = [
    ("a  Knopf, dessen Inhalt eine leere Variable sein kann",
     "h('button',{onClick:()=>0}, koederVariable), ",
     lambda t, mk, st: any("koederVariable" in " ".join(s["kinder"])
                           for s in klasse_a(t, mk, st))),
    ("a  Knopf, der NIE Text zeigt (reines Symbol, ohne Namen)",
     "h('button',{onClick:()=>0}, '\u2715'), ",
     lambda t, mk, st: any("'\u2715'" in " ".join(s["kinder"])
                           for s in klasse_a_immer(t, mk, st))),
    ("a  Knopf mit Text UND leerem Zweig (\"nur mobil benannt\")",
     "h('button',{onClick:()=>0}, \"\U0001F5D1\ufe0f \", koederMob?\"L\u00f6schen\":\"\"), ",
     lambda t, mk, st: any("koederMob" in " ".join(s["kinder"])
                           for s in klasse_a(t, mk, st))),
    ("b  Knopf mit Emoji PLUS Text",
     "h('button',{onClick:()=>0}, \"\U0001F5A8\ufe0f Koederdruck\"), ",
     lambda t, mk, st: any("Koederdruck" in s["sichtbar"]
                           for s in klasse_b(t, mk, st))),
    ("c  div mit onClick, ohne role und tabIndex",
     "h('div',{onClick:()=>0}, \"Koederflaeche\"), ",
     lambda t, mk, st: any(s["tag"] == "div" and not s["role"]
                           and "Koederflaeche" in " ".join(s["kinder"])
                           for s in klasse_c_onclick(st))),
    ("c  input ohne jeden Namen",
     "h('input',{type:'text',value:koeder}), ",
     lambda t, mk, st: any(not e["ok"] and "koeder" in e["props"]
                           for e in klasse_c_eingaben(t, mk, st))),
    ("GEGENPROBE die h(-Schreibweise wird ueberhaupt gesehen",
     "h('button',{onClick:()=>0}, koederKuerzel), ",
     lambda t, mk, st: any("koederKuerzel" in " ".join(s["kinder"])
                           for s in klasse_a(t, mk, st))),
    ("GEGENPROBE ein EINFACH gesetzter Inhalt wird gesehen",
     "React.createElement('button',{onClick:()=>0}, '\u25c0'), ",
     lambda t, mk, st: any("'\u25c0'" in " ".join(s["kinder"])
                           for s in klasse_a_immer(t, mk, st))),
    ("GEGENPROBE ein BENANNTER Knopf wird NICHT gemeldet (Falschmeldung)",
     "h('button',{onClick:()=>0,title:\"Koeder benannt\"}, koederEgal), ",
     lambda t, mk, st: not any("koederEgal" in " ".join(s["kinder"])
                               for s in klasse_a(t, mk, st))),
    ("GEGENPROBE ein Knopf mit Text in einem KIND wird NICHT gemeldet",
     "h('button',{onClick:()=>0}, '\u2715', h('div',{},'Koederwort')), ",
     lambda t, mk, st: not any("Koederwort" in " ".join(s["kinder"])
                               for s in klasse_a(t, mk, st)
                               + klasse_a_immer(t, mk, st))),
]


def koederprobe(roh):
    """Jede zaehlende Messung braucht einen Koeder.

    Ohne ihn ist eine 0 wertlos: "nicht gefunden" sieht genauso aus wie "ist
    sauber". Die drei GEGENPROBEN messen die andere Richtung - ein Zaehler,
    der ALLES meldet, schlaegt bei jedem Koeder an und ist trotzdem kaputt.
    """
    anker, erg = _anker(roh), []
    for name, code, pruef in KOEDER:
        kaputt = roh.replace(anker, code + anker, 1)
        mk = ist_code(kaputt)
        erg.append((name, bool(pruef(kaputt, mk, stellen(kaputt, mk)))))
    return erg


def main():
    roh = lies()
    mk = maske(roh)
    st = stellen(roh, mk)
    was = sys.argv[1] if len(sys.argv) > 1 else ""
    if was == "koeder":
        for name, ok in koederprobe(roh):
            print(("ANGESCHLAGEN  " if ok else "BLIND         ") + name)
        return
    a = klasse_a(roh, mk, st)
    ai = klasse_a_immer(roh, mk, st)
    b = klasse_b(roh, mk, st)
    co = klasse_c_onclick(st)
    ce = klasse_c_eingaben(roh, mk, st)
    if was == "json":
        def d(s, extra=()):
            o = dict(ansicht=s["ansicht"], zeile=s["zeile"], tag=s["tag"],
                     schreib=schreibweise(roh, s),
                     kinder=s["kinder"][:6], props=s["props"][:700])
            for k in extra:
                o[k] = s[k]
            return o
        print(json.dumps(dict(
            gesamt=len(st),
            a_manchmal=[d(s) for s in a],
            a_immer=[d(s) for s in ai],
            b=[d(s, ("sichtbar",)) for s in b],
            c_onclick=[d(s, ("role", "tabIndex", "onKey", "schlucker"))
                       for s in co],
            c_eingaben=[d(s, ("typ", "ok", "in_label", "placeholder"))
                        for s in ce],
        ), ensure_ascii=False, indent=0))
        return
    from collections import Counter
    kn = [s for s in st if s["tag"] == "button"]
    print("Elementstellen mit literalem Tag : %d" % len(st))
    print("davon button                     : %d  (%s)"
          % (len(kn), dict(Counter(schreibweise(roh, s) for s in kn))))
    print("Namensbefund aller Knoepfe       : %s"
          % dict(Counter(beurteile(roh, mk, s) for s in kn)))
    print()
    print("(a) Name haengt an einer Variable / einem Zweig, der leer sein "
          "kann : %d" % len(a))
    print("(a+) Knopf zeigt NIE Text und hat keinen Namen in den Props  "
          "     : %d" % len(ai))
    print("(b) Emoji PLUS Text (schwaechere Klasse, kein Urteil)        "
          "     : %d" % len(b))
    print("(c) onClick auf Nicht-Bedienelement                          "
          "     : %d" % len(co))
    print("     davon Klick-Schlucker (stopPropagation, kein Bedienelement)"
          ": %d" % sum(1 for s in co if s["schlucker"]))
    print("     echte Bedienflaechen (ohne Schlucker)                    "
          "     : %d" % sum(1 for s in co if not s["schlucker"]))
    print("     davon mit role UND tabIndex                              "
          "    : %d" % sum(1 for s in co
                           if s["role"] and s["tabIndex"] and not s["schlucker"]))
    print("     davon mit onKeyDown/Press/Up                             "
          "    : %d" % sum(1 for s in co if s["onKey"] and not s["schlucker"]))
    print("     Tags: %s" % dict(Counter(s["tag"] for s in co)))
    print("(c) input/select/textarea gesamt                             "
          "     : %d" % len(ce))
    print("     davon OHNE label/aria-label/title                       "
          "     : %d" % sum(1 for s in ce if not s["ok"]))
    print("     davon nur mit placeholder                               "
          "     : %d" % sum(1 for s in ce if not s["ok"] and s["placeholder"]))
    print("     Tags ohne Namen: %s"
          % dict(Counter(s["tag"] for s in ce if not s["ok"])))


if __name__ == "__main__":
    main()


# ─────────── Gegenprobe: ist der Name eine EIGENSCHAFT ERSTER EBENE? ───────
def _top_level_keys(props):
    """Schluessel auf Tiefe 1 des Eigenschaftenobjekts.

    🔴 WARUM DAS NOETIG IST
    `hat_namen()` sucht `title:` flach im Props-Text. Ein `title:` kann aber
    TIEFER stehen - in einem Datenobjekt innerhalb eines `onClick`, z.B.
    Z18476: `onClick: ()=>setTplEdit(p=>[...p,{label:"Neue Vorlage",
    type:"mangel",title:"",...}])`. Das ist KEIN Name des Knopfes. Ein
    flacher Treffer meldet den Knopf trotzdem als benannt - genau die
    Fehlerform, an der die erste v958-Messung dreimal gescheitert ist, nur
    eine Ebene hoeher.
    """
    keys, tiefe, i, n = set(), 0, 0, len(props)
    while i < n:
        c = props[i]
        if c in "\"'`":
            q, i = c, i + 1
            start = i
            while i < n and props[i] != q:
                i += 2 if props[i] == "\\" else 1
            # Ein Zeichenketten-Schluessel: 'aria-label': "..."
            if tiefe == 1:
                j = i + 1
                while j < n and props[j] in " \t\r\n":
                    j += 1
                if j < n and props[j] == ":":
                    keys.add(props[start:i])
            i += 1
            continue
        if c in "{[(":
            tiefe += 1
        elif c in "}])":
            tiefe -= 1
        elif tiefe == 1 and (c.isalpha() or c in "_$"):
            m = re.match(r"[A-Za-z_$][\w$]*", props[i:])
            wort = m.group(0)
            j = i + len(wort)
            while j < n and props[j] in " \t\r\n":
                j += 1
            if j < n and props[j] == ":":
                keys.add(wort)
            i += len(wort)
            continue
        i += 1
    return keys


def hat_namen_streng(props):
    k = _top_level_keys(props)
    return bool({"title", "aria-label", "aria-labelledby"} & k)
