# -*- coding: utf-8 -*-
"""Schreibwege in index.html: wer schreibt, wer merkt die Abweisung, wer fragt
die Rolle?

WARUM ES DIESES SKRIPT GIBT
───────────────────────────
"HTTP 200 mit leerem Array" ist bei PostgREST die Antwort auf einen vom
Zeilenschutz (RLS) ABGEWIESENEN Schreibvorgang. Ohne Pruefung gilt das als
Erfolg: der Auftrag wird aus der Warteschlange geloescht, und die Eingabe des
Monteurs ist weg. `_RLS_SILENT_DENIAL_LABELS` (index.html) ist der Waechter
dagegen - aber er sitzt NUR im allgemeinen PATCH-Zweig von
`_translateAndExec`. Dieses Skript misst, welche Schreibwege ihn erreichen und
welche an ihm vorbeilaufen.

Dazu: an welchen Schreibstellen ueberhaupt eine Rolle abgefragt wird.

DREI FALLEN, GEGEN DIE GEEICHT WIRD
───────────────────────────────────
  1. Kommentare. `index.html` hat zwei Kommentare von 284 000 bzw. 88 500
     Zeichen, in denen `SQ.push` und Tabellennamen zitiert werden.
  2. Zwei Schreibweisen: `method:"PUT"` UND `method:'PUT'`.
  3. Klammerabgleich. Eine `}` in einer Zeichenkette oder ein `)` in einem
     Regex-Literal im Rumpf reisst einen naiven Abgleich aus dem Tritt. Hier
     zaehlen NUR Code-Zeichen (code_scan.ist_code).

UMFANG
──────
Nur der Quelltext von `index.html`. Ueber den tatsaechlichen Zeilenschutz der
laufenden Datenbank sagt dieses Skript NICHTS - dafuer gibt es hier keinen
Zugang.

AUFRUF
──────
    python scripts/rechte_schreibwege_messen.py
Rueckgabewert: 0 = gemessen, 2 = Selbstprobe gescheitert (keine Zahl gueltig).
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from code_scan import ist_code  # noqa: E402

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUELLE = os.path.join(WURZEL, "index.html")

# Marken, die eine Rollenabfrage ausmachen. Gleiche Liste wie in
# rechte_rollen_messen.py, beide Anfuehrungszeichen-Schreibweisen inbegriffen.
ROLLENMARKEN = [
    r"""\bcanDo\s*\(""",
    r"""\bhasPerm\s*\(""",
    r"""(?:[\w$]+\.)?_?[Rr]oll?e\s*(?:===|!==|==|!=)\s*['"][A-Za-z_]+['"]""",
    r"""\.rolle\b""",
    r"""\bROLES\s*\[""",
    r"""\bperms(?:Override|_override)\b""",
    r"""\bis(?:Full)?Admin\b""",
    r"""\b_isAdmin\b""",
    r"""\bisAdminPL\b""",
]
ROLLENMARKE = re.compile("|".join(ROLLENMARKEN))


# ───────────────────────── Werkzeug ─────────────────────────

def lies(pfad):
    with io.open(pfad, "r", encoding="utf-8", errors="replace", newline="") as f:
        return f.read()


def zeilenfeld(text):
    aus, z = [], 1
    for ch in text:
        aus.append(z)
        if ch == "\n":
            z += 1
    return aus


def code_treffer(text, feld, muster, flags=0):
    return [m for m in re.finditer(muster, text, flags) if feld[m.start()]]


def klammer_zu(text, feld, i, auf, zu):
    """Passende schliessende Klammer - NUR Code-Zeichen zaehlen."""
    tiefe, n, j = 0, len(text), i
    while j < n:
        if feld[j]:
            if text[j] == auf:
                tiefe += 1
            elif text[j] == zu:
                tiefe -= 1
                if tiefe == 0:
                    return j
        j += 1
    return -1


def ist_kein_kommentar(text):
    """Bytefeld: True, wo das Zeichen KEIN Kommentar ist (Code UND Zeichenkette).

    WARUM NICHT code_scan.ist_code: das blendet Zeichenketten MIT aus. Genau
    darin steht hier aber der Inhalt - `method:"PUT"`, `url:"/api/..."`. Ein
    Zaehler auf ist_code meldet fuer JEDEN dieser Schluessel "kommt nicht vor".
    Die Zustaende sind dieselben wie in code_scan; nur BLOCK und ZEILE werden
    ausgeblendet. Die Selbstprobe prueft zusaetzlich die Einbettung:
    ist_code(x) => ist_kein_kommentar(x) muss an JEDER Stelle gelten.
    """
    n = len(text)
    aus = bytearray(n)
    CODE, EINF, DOPP, VORL, ZEILE, BLOCK = range(6)
    zustand = CODE
    i = 0
    while i < n:
        c = text[i]
        if zustand == CODE:
            if c == "/" and i + 1 < n and text[i + 1] not in "*/":
                k = i - 1
                while k >= 0 and text[k] in " \t\r\n":
                    k -= 1
                davor = text[k] if k >= 0 else "("
                wort = text[max(0, k - 9):k + 1]
                if davor in "(,=:[!&|?{};+-~^%<>" or wort.endswith(
                        ("return", "typeof", "case", "in", "of", "new",
                         "delete", "void", "instanceof")):
                    j = i + 1
                    in_klasse = False
                    ende = -1
                    while j < n:
                        d = text[j]
                        if d == "\\":
                            j += 2
                            continue
                        if d == "\n":
                            break
                        if d == "[":
                            in_klasse = True
                        elif d == "]":
                            in_klasse = False
                        elif d == "/" and not in_klasse:
                            ende = j
                            break
                        j += 1
                    if ende >= 0:
                        for x in range(i, ende + 1):
                            aus[x] = 1
                        i = ende + 1
                        continue
                    aus[i] = 1
                    i += 1
                    continue
            if c == "/" and i + 1 < n and text[i + 1] == "*":
                zustand = BLOCK
                i += 2
                continue
            if c == "/" and i + 1 < n and text[i + 1] == "/":
                zustand = ZEILE
                i += 2
                continue
            aus[i] = 1
            if c == "'":
                zustand = EINF
            elif c == '"':
                zustand = DOPP
            elif c == "`":
                zustand = VORL
            i += 1
            continue
        if zustand == BLOCK:
            if c == "*" and i + 1 < n and text[i + 1] == "/":
                zustand = CODE
                i += 2
                continue
            i += 1
            continue
        if zustand == ZEILE:
            if c == "\n":
                zustand = CODE
                aus[i] = 1
            i += 1
            continue
        # in einer Zeichenkette: Inhalt ZAEHLT
        aus[i] = 1
        if c == "\\":
            if i + 1 < n:
                aus[i + 1] = 1
            i += 2
            continue
        if (zustand == EINF and c == "'") or (zustand == DOPP and c == '"') \
                or (zustand == VORL and c == "`"):
            zustand = CODE
        i += 1
    return aus


def nur_code(text, feld, a, b):
    """Der Ausschnitt [a,b), Nicht-Code durch Leerzeichen ersetzt."""
    return "".join(text[i] if (feld[i] or text[i] == "\n") else " "
                   for i in range(a, min(b, len(text))))


def ohne_kommentar(text, kfeld, a, b):
    """Der Ausschnitt [a,b), KOMMENTARE durch Leerzeichen ersetzt."""
    return "".join(text[i] if (kfeld[i] or text[i] == "\n") else " "
                   for i in range(a, min(b, len(text))))


def umgebung_start(text, feld, pos, ebenen=2, grenze=8000):
    """Anfang des umschliessenden Blocks, bis zu `ebenen` Ebenen nach aussen.

    Rueckwaerts ueber CODE-Zeichen: `}` geht eine Ebene hinein, `{` bei Tiefe 0
    geht eine Ebene heraus.

    🔴 DAS IST EINE NAEHERUNG, UND SIE IRRT IN BEIDE RICHTUNGEN. Gemessen an
    index.html v3.9.997, je ein Gegenbeispiel:
      * `updSt` (Schreibstelle 17037) wird als "mit Riegel" gefuehrt - das
        gefundene `isAdmin` gehoert zu einer ANDEREN Funktion.
      * `_bulkApply` (Schreibstelle 17041) wird als "ohne Riegel" gefuehrt -
        der Push steht in einem forEach-Rueckruf, und das `if(!isAdmin)return;`
        am Anfang der Funktion liegt eine Ebene weiter draussen.
    Die Zahlen taugen deshalb als SUCHHILFE, nicht als Befund. Jeder Befund
    muss an der Stelle selbst nachgelesen werden.
    """
    tiefe, raus, gez = 0, 0, 0
    i = pos - 1
    while i >= 0 and gez < grenze:
        if feld[i]:
            gez += 1
            c = text[i]
            if c == "}":
                tiefe += 1
            elif c == "{":
                if tiefe == 0:
                    raus += 1
                    if raus >= ebenen:
                        return i + 1
                else:
                    tiefe -= 1
        i -= 1
    return max(0, i + 1)


# ───────────────────────── Die Zaehler ─────────────────────────

def z_sq_push(text, feld, kfeld, zl):
    """Jeder SQ.push-Aufruf im CODE mit Methode und Route.

    Die Klammer wird ueber CODE-Zeichen abgeglichen (eine `}` in einer
    Zeichenkette zaehlt also nicht), der INHALT dagegen ohne Kommentare
    gelesen - `method:"PUT"` steht in einer Zeichenkette.
    """
    aus = []
    for m in code_treffer(text, feld, r"""\bSQ\.push\s*\("""):
        auf = text.index("(", m.start() + 7)
        zu = klammer_zu(text, feld, auf, "(", ")")
        if zu < 0:
            aus.append({"zeile": zl[m.start()], "pos": m.start(),
                        "methode": "?", "route": "?",
                        "fehler": "keine schliessende Klammer"})
            continue
        arg = ohne_kommentar(text, kfeld, auf, zu + 1)
        # Methode: beide Anfuehrungszeichen-Schreibweisen
        mm = re.search(r"""method\s*:\s*(['"])([A-Z]+)\1""", arg)
        # Route: aus /api/<name>; auch aus einem Vorlagenliteral
        rm = re.search(r"""/api/([a-z0-9_-]+)""", arg, re.I)
        aus.append({"zeile": zl[m.start()], "pos": m.start(),
                    "methode": mm.group(2) if mm else "?",
                    "route": rm.group(1) if rm else "?"})
    return aus


def z_route_map(text, feld, kfeld):
    tr = code_treffer(text, feld, r"""\bconst\s+ROUTE_MAP\s*=\s*\{""")
    if len(tr) != 1:
        return None
    auf = text.index("{", tr[0].start())
    zu = klammer_zu(text, feld, auf, "{", "}")
    inner = ohne_kommentar(text, kfeld, auf, zu + 1)
    aus = {}
    for m in re.finditer(
            r"""(['"])([a-z0-9_-]+)\1\s*:\s*\[\s*(['"])[a-z0-9_-]+\3\s*,\s*(['"])([a-z0-9_]+)\4""",
            inner, re.I):
        aus[m.group(2)] = m.group(5)
    return aus


def z_labels(text, feld, kfeld):
    tr = code_treffer(text, feld,
                      r"""\bconst\s+_RLS_SILENT_DENIAL_LABELS\s*=\s*Object\.freeze\s*\(\s*\{""")
    if len(tr) != 1:
        return None
    auf = text.index("{", tr[0].start())
    zu = klammer_zu(text, feld, auf, "{", "}")
    inner = ohne_kommentar(text, kfeld, auf, zu + 1)
    return re.findall(r"""[{,]\s*([a-z_]+)\s*:\s*["']""", inner)


def z_helfer_blind(text, feld):
    """Welche Schreibhelfer koennen 0 getroffene Zeilen ueberhaupt SEHEN?

    Nur wer `Prefer: return=representation` schickt (`_sbWH`), bekommt die
    getroffenen Zeilen zurueck. Wer `_sbH()` nimmt, bekommt 204/leer und kann
    eine Abweisung STRUKTURELL nicht von einem Erfolg unterscheiden.
    """
    aus = {}
    for name in ["_sbPatch", "_sbPost", "_sbUpsert", "_sbDelete", "_sbDeleteWhere"]:
        tr = code_treffer(text, feld,
                          r"""\basync\s+function\s+%s\s*\(""" % re.escape(name))
        if not tr:
            aus[name] = None
            continue
        auf = text.index("{", tr[0].start())
        zu = klammer_zu(text, feld, auf, "{", "}")
        rumpf = nur_code(text, feld, auf, zu + 1)
        aus[name] = {
            "sieht_zeilen": "_sbWH(" in rumpf,
            "header": "_sbWH" if "_sbWH(" in rumpf else "_sbH",
            "gibt_zurueck": "r.json()" in rumpf,
        }
    return aus


def z_umleitungen(text, feld, zl):
    """Schreibvorgaenge IN `_translateAndExec`, die den Waechter nicht erreichen.

    Der Waechter steht im allgemeinen PATCH-Zweig. Jeder direkte Aufruf eines
    Schreibhelfers, der VOR dem allgemeinen CRUD-Block steht, laeuft an ihm
    vorbei - auch dann, wenn die Tabelle in der Tafel steht.
    """
    tr = code_treffer(text, feld,
                      r"""\basync\s+function\s+_translateAndExec\s*\(""")
    if len(tr) != 1:
        return None
    auf = text.index("{", text.index(")", tr[0].start()))
    zu = klammer_zu(text, feld, auf, "{", "}")
    # Der allgemeine CRUD-Block beginnt bei `const entry=ROUTE_MAP[resource];`
    gm = re.search(r"""const\s+entry\s*=\s*ROUTE_MAP\s*\[""",
                   nur_code(text, feld, auf, zu + 1))
    crud_ab = auf + gm.start() if gm else zu
    waechter = re.search(r"""_RLS_SILENT_DENIAL_LABELS\s*\[\s*table\s*\]""",
                         nur_code(text, feld, auf, zu + 1))
    aus = {"von": zl[auf], "bis": zl[zu], "crud_ab": zl[crud_ab],
           "waechter_zeile": zl[auf + waechter.start()] if waechter else None,
           "vorbei": []}
    for m in code_treffer(
            text, feld,
            r"""\b(_sbPatch|_sbUpsert|_sbPost|_sbDelete|_sbDeleteWhere)\s*\(\s*["']([a-z_]+)["']"""):
        if auf < m.start() < crud_ab:
            aus["vorbei"].append({"zeile": zl[m.start()],
                                  "helfer": m.group(1),
                                  "tabelle": m.group(2)})
    # dazu die rohen fetch-PATCH/DELETE im selben Bereich
    for m in code_treffer(text, feld, r"""SB_REST\s*\+\s*["']/([a-z_]+)"""):
        if auf < m.start() < crud_ab:
            aus["vorbei"].append({"zeile": zl[m.start()], "helfer": "fetch",
                                  "tabelle": m.group(1)})
    return aus


def z_gate_naehe(text, feld, kfeld, stellen, ebenen=2):
    """Je Schreibstelle: steht im umschliessenden Block eine Rollenabfrage?"""
    mit, ohne = [], []
    for s in stellen:
        a = umgebung_start(text, feld, s["pos"], ebenen=ebenen)
        auss = ohne_kommentar(text, kfeld, a, s["pos"])
        (mit if ROLLENMARKE.search(auss) else ohne).append(s)
    return mit, ohne


# ───────────────────────── Die Selbstprobe ─────────────────────────
# Ein Koeder JE SCHREIBWEISE (doppelt/einfach zitierte Methode, Vorlagenliteral
# als Adresse, Regex im Rumpf, `}` in einer Zeichenkette) plus VIER Gegenproben
# (Zeilenkommentar, Blockkommentar, Zeichenkette, Backtick im Kommentar).

KOEDER = r"""
const ROUTE_MAP={
  "koederA":["koederA","tab_a"],
  'koederB':['koederB','tab_b'],
  "koederC":["koederC","tab_c"],
  "koederD":["koederD","tab_d"],
  "koederE":["koederE","tab_e"],
};
const _RLS_SILENT_DENIAL_LABELS=Object.freeze({
  tab_a:"Tafel A",
  tab_b:'Tafel B'/* Kommentar mit tab_zzz:"nicht zaehlen" */
});
async function _sbPatch(table,id,data){
  const r=await fetch(SB_REST+"/"+table,{method:"PATCH",headers:_sbWH()});
  try{return await r.json();}catch(_){return{ok:1};}
}
async function _sbDelete(table,id){
  const r=await fetch(SB_REST+"/"+table,{method:"DELETE",headers:_sbH()});
  return{ok:1};
}
async function _translateAndExec(url,method,body){
  if(resource==="koederA"&&method==="PUT"){
    await _sbPatch("tab_a",id,{x:1});
    return{ok:1};
  }
  const entry=ROUTE_MAP[resource];
  const table=entry[1];
  if(method==="PUT"){
    const _p=await _sbPatch(table,id,data);
    if(_RLS_SILENT_DENIAL_LABELS[table]&&Array.isArray(_p)&&_p.length===0){toast();}
  }
}
function koederGegated(){
  if(!canDo("koeder_eins",curUser))return;
  SQ.push({url:"/api/koederA/1",method:"PUT",body:{n:"a"}});
}
function koederUngegated(){
  SQ.push({url:"/api/koederB/1",method:'PUT',body:{n:'b'}});
}
function koederVorlage(id){
  SQ.push({url:`/api/koederC/${id}`,method:"DELETE"});
}
function koederRegexImRumpf(s){
  SQ.push({url:"/api/koederD/1",method:"POST",body:{t:s.replace(/[)}]/g,"")}});
}
function koederKlammerImString(){
  SQ.push({url:"/api/koederE/1",method:"PATCH",body:{t:"}) hier endet nichts"}});
}
// GEGENPROBE-ZEILENKOMMENTAR: SQ.push({url:"/api/nie/1",method:"PUT"})
/* GEGENPROBE-BLOCKKOMMENTAR: SQ.push({url:'/api/nie/2',method:'DELETE'})
   und ein Backtick-Zitat: `SQ.push({url:"/api/nie/3",method:"POST"})` */
const gegenprobe_string="SQ.push({url:'/api/nie/4',method:'PUT'})";
"""


def selbstprobe():
    fehler = []
    text = KOEDER
    feld = ist_code(text)
    kfeld = ist_kein_kommentar(text)
    zl = zeilenfeld(text)

    # --- 0: Einbettung. Jedes CODE-Zeichen ist auch KEIN Kommentar. ---
    # Ohne diese Probe koennte die zweite Maske still auseinanderlaufen.
    schief = [i for i in range(len(text)) if feld[i] and not kfeld[i]]
    if schief:
        fehler.append("ist_code ist NICHT in ist_kein_kommentar enthalten "
                      "(%d Stellen, erste bei %d)" % (len(schief), schief[0]))
    if sum(kfeld) <= sum(feld):
        fehler.append("ist_kein_kommentar findet nicht MEHR als ist_code "
                      "(%d vs %d) - die Zeichenketten fehlen" %
                      (sum(kfeld), sum(feld)))

    # --- A: SQ.push, ein Koeder je Schreibweise ---
    st = z_sq_push(text, feld, kfeld, zl)
    gefunden = sorted((s["route"], s["methode"]) for s in st)
    erwartet = sorted([("koederA", "PUT"), ("koederB", "PUT"),
                       ("koederC", "DELETE"), ("koederD", "POST"),
                       ("koederE", "PATCH")])
    if gefunden != erwartet:
        fehler.append("SQ.push-Koeder: %r statt %r" % (gefunden, erwartet))

    # --- B: Gegenproben. `nie` darf NIE auftauchen. ---
    if any(s["route"].startswith("nie") for s in st):
        fehler.append("GEGENPROBE: SQ.push aus Kommentar/Zeichenkette gezaehlt")
    # und die Ausblendung muss ueberhaupt etwas tun
    roh = len(re.findall(r"""\bSQ\.push\s*\(""", text))
    if not roh > len(st):
        fehler.append("Kommentar-Ausblendung wirkungslos: roh=%d, code=%d"
                      % (roh, len(st)))

    # --- C: ROUTE_MAP, beide Anfuehrungszeichen-Schreibweisen ---
    rm = z_route_map(text, feld, kfeld)
    if rm != {"koederA": "tab_a", "koederB": "tab_b", "koederC": "tab_c",
              "koederD": "tab_d", "koederE": "tab_e"}:
        fehler.append("ROUTE_MAP-Koeder: %r" % (rm,))

    # --- D: Tafel, beide Schreibweisen, Kommentar-Eintrag NICHT ---
    lb = z_labels(text, feld, kfeld)
    if lb != ["tab_a", "tab_b"]:
        fehler.append("Tafel-Koeder: %r statt ['tab_a','tab_b']" % (lb,))

    # --- E: Helfer-Blindheit ---
    hb = z_helfer_blind(text, feld)
    if not (hb.get("_sbPatch") or {}).get("sieht_zeilen"):
        fehler.append("_sbPatch muesste Zeilen SEHEN (_sbWH)")
    if (hb.get("_sbDelete") or {}).get("sieht_zeilen"):
        fehler.append("_sbDelete darf Zeilen NICHT sehen (_sbH)")

    # --- F: Umleitung am Waechter vorbei ---
    um = z_umleitungen(text, feld, zl)
    if um is None:
        fehler.append("_translateAndExec-Koeder nicht gefunden")
    else:
        tabs = sorted(v["tabelle"] for v in um["vorbei"])
        if tabs != ["tab_a"]:
            fehler.append("Umleitungs-Koeder: %r statt ['tab_a']" % (tabs,))
        if um["waechter_zeile"] is None:
            fehler.append("Waechter im Koeder nicht gefunden")

    # --- G: Rollenabfrage in der Umgebung ---
    mit, ohne = z_gate_naehe(text, feld, kfeld, st, ebenen=1)
    if sorted(s["route"] for s in mit) != ["koederA"]:
        fehler.append("Gate-Naehe, MIT Rollenabfrage: %r statt ['koederA']"
                      % (sorted(s["route"] for s in mit),))
    if sorted(s["route"] for s in ohne) != ["koederB", "koederC", "koederD",
                                            "koederE"]:
        fehler.append("Gate-Naehe, OHNE Rollenabfrage: %r"
                      % (sorted(s["route"] for s in ohne),))
    # GEGENPROBE zur Naeherung selbst: ein zu GROSSER Ausschnitt muss die
    # fremde Rollenabfrage einsammeln. Faellt diese Probe aus, misst die
    # Ebenen-Angabe nichts und die Zahlen unten waeren beliebig.
    mit3, ohne3 = z_gate_naehe(text, feld, kfeld, st, ebenen=4)
    if len(mit3) <= len(mit):
        fehler.append("Ebenen-Angabe wirkungslos: Ebene 1 -> %d mit, "
                      "Ebene 4 -> %d mit" % (len(mit), len(mit3)))

    if fehler:
        print("SELBSTPROBE GESCHEITERT - KEINE ZAHL IST GUELTIG:")
        for f in fehler:
            print("  * " + f)
        return False
    print("Selbstprobe bestanden: 5 SQ.push-Koeder (doppelt/einfach zitierte "
          "Methode, Vorlagenliteral, Regex im Rumpf, `}` in der Zeichenkette), "
          "4 Gegenproben (Zeilen-/Blockkommentar, Backtick-Zitat, "
          "Zeichenkette), Ausblendungs-Gegenprobe roh=%d > code=%d."
          % (roh, len(st)))
    return True


# ───────────────────────── Die Messung ─────────────────────────

def messen():
    text = lies(QUELLE)
    feld = ist_code(text)
    kfeld = ist_kein_kommentar(text)
    zl = zeilenfeld(text)
    a = {}
    v = code_treffer(text, feld, r"""APP_VERSION\s*=\s*["']([^"']+)["']""")
    a["version"] = v[0].group(1) if v else "?"
    a["zeilen"] = zl[-1]

    st = z_sq_push(text, feld, kfeld, zl)
    a["sq_push_gesamt"] = len(st)
    nach_meth = {}
    for s in st:
        nach_meth[s["methode"]] = nach_meth.get(s["methode"], 0) + 1
    a["sq_push_je_methode"] = nach_meth

    rm = z_route_map(text, feld, kfeld)
    a["route_map_eintraege"] = len(rm)
    lb = z_labels(text, feld, kfeld)
    a["tafel"] = lb

    # Tabellen je Methode
    tab_meth = {}
    ohne_route = []
    for s in st:
        t = rm.get(s["route"])
        if t is None:
            ohne_route.append(s)
            continue
        tab_meth.setdefault(s["methode"], {}).setdefault(t, []).append(s["zeile"])
    a["routen_ohne_route_map"] = sorted(set(
        s["route"] for s in ohne_route))
    a["tabellen_je_methode"] = {k: {t: len(v) for t, v in sorted(d.items())}
                                for k, d in tab_meth.items()}

    schreib = {}
    for meth in ("PUT", "PATCH"):
        for t, v in tab_meth.get(meth, {}).items():
            schreib[t] = schreib.get(t, 0) + len(v)
    a["patch_tabellen"] = schreib
    a["patch_gedeckt"] = sorted(t for t in schreib if t in lb)
    a["patch_ungedeckt"] = sorted(t for t in schreib if t not in lb)
    a["tafel_ohne_schreibstelle"] = sorted(t for t in lb if t not in schreib)

    loesch = {}
    for t, v in tab_meth.get("DELETE", {}).items():
        loesch[t] = len(v)
    a["delete_tabellen"] = loesch

    a["helfer"] = z_helfer_blind(text, feld)
    a["umleitungen"] = z_umleitungen(text, feld, zl)

    for eb in (1, 2, 3):
        mit, ohne = z_gate_naehe(text, feld, kfeld, st, ebenen=eb)
        a["gate_ebenen_%d" % eb] = {"mit": len(mit), "ohne": len(ohne)}
        if eb == 2:
            a["ohne_gate_stellen"] = [
                {"zeile": s["zeile"], "route": s["route"],
                 "methode": s["methode"], "tabelle": rm.get(s["route"], "?")}
                for s in ohne]
    return a


def bericht(a):
    print()
    print("UMFANG: index.html, %d Zeilen, APP_VERSION=%s" % (a["zeilen"], a["version"]))
    print("        Nur Quelltext. Ueber den Zeilenschutz der laufenden Datenbank")
    print("        sagt diese Messung NICHTS.")
    print()
    print("--- 1. Schreibwege ueber die Warteschlange ---")
    print("   SQ.push-Aufrufe im Code : %d" % a["sq_push_gesamt"])
    for k, v in sorted(a["sq_push_je_methode"].items()):
        print("      %-8s %4d" % (k, v))
    print("   ROUTE_MAP-Eintraege     : %d" % a["route_map_eintraege"])
    print("   Routen ohne ROUTE_MAP   : %s" % (a["routen_ohne_route_map"] or "-"))
    print()
    print("--- 2. Der Waechter _RLS_SILENT_DENIAL_LABELS ---")
    print("   Eintraege in der Tafel  : %d" % len(a["tafel"]))
    print("   PUT/PATCH-Tabellen      : %d" % len(a["patch_tabellen"]))
    print("   davon GEDECKT           : %d  (%s)" %
          (len(a["patch_gedeckt"]), ", ".join(a["patch_gedeckt"])))
    print("   davon UNGEDECKT         : %d  (%s)" %
          (len(a["patch_ungedeckt"]), ", ".join(a["patch_ungedeckt"])))
    print("   Tafel-Eintraege OHNE PUT/PATCH-Schreibstelle: %d  (%s)" %
          (len(a["tafel_ohne_schreibstelle"]),
           ", ".join(a["tafel_ohne_schreibstelle"])))
    print()
    print("--- 3. Loeschen: strukturell blind ---")
    for name, h in a["helfer"].items():
        if h is None:
            print("   %-16s NICHT GEFUNDEN" % name)
        else:
            print("   %-16s Header=%-6s  sieht getroffene Zeilen: %s" %
                  (name, h["header"], "JA" if h["sieht_zeilen"] else "NEIN"))
    print("   DELETE ueber die Warteschlange: %d Tabellen, %d Stellen" %
          (len(a["delete_tabellen"]), sum(a["delete_tabellen"].values())))
    for t, n in sorted(a["delete_tabellen"].items(), key=lambda x: -x[1]):
        print("      %-24s %3d" % (t, n))
    print()
    print("--- 4. Schreibvorgaenge, die am Waechter VORBEI laufen ---")
    um = a["umleitungen"]
    print("   _translateAndExec: Zeile %d bis %d" % (um["von"], um["bis"]))
    print("   allgemeiner CRUD-Block ab Zeile %d, Waechter in Zeile %s" %
          (um["crud_ab"], um["waechter_zeile"]))
    print("   direkte Schreibaufrufe DAVOR: %d" % len(um["vorbei"]))
    for v in um["vorbei"]:
        inTafel = " <- steht in der TAFEL" if v["tabelle"] in a["tafel"] else ""
        print("      Zeile %-6d %-16s %-22s%s" %
              (v["zeile"], v["helfer"], v["tabelle"], inTafel))
    print()
    print("--- 5. Rollenabfrage im umschliessenden Block einer Schreibstelle ---")
    print("   NAEHERUNG - irrt in BEIDE Richtungen (updSt/17037 falsch als MIT,")
    print("   _bulkApply/17041 falsch als OHNE). SUCHHILFE, kein Befund:")
    for eb in (1, 2, 3):
        g = a["gate_ebenen_%d" % eb]
        print("   %d Blockebene(n) nach aussen: mit %3d   ohne %3d   (%.0f %% ohne)"
              % (eb, g["mit"], g["ohne"],
                 100.0 * g["ohne"] / max(1, g["mit"] + g["ohne"])))


def main(argv):
    if not selbstprobe():
        return 2
    a = messen()
    bericht(a)
    if "--json" in argv:
        ziel = os.path.join(WURZEL, "docs", "befunde", "bughunt",
                            "rechte_schreibwege.json")
        with io.open(ziel, "w", encoding="utf-8", newline="") as f:
            f.write(json.dumps(a, ensure_ascii=False, indent=1))
        print("\nJSON: " + ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
