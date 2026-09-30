# -*- coding: utf-8 -*-
"""Rollen und Rollenabfragen in index.html zaehlen - je Schreibweise einzeln.

WARUM ES DIESES SKRIPT GIBT
───────────────────────────
Das Gebiet "Berechtigungen gegen Oberflaeche" stand im Befundzettel
`docs/befunde/BUGHUNT_2026-09-30.md` als OFFEN. Die Frage dahinter: wo bietet
die Oberflaeche eine Handlung an, die der Zeilenschutz der Datenbank abweist?

Der erste Schritt ist eine Zaehlung, und eine Zaehlung ist nur so gut wie ihre
Eichung. Deshalb hat JEDER Zaehler hier einen eigenen Koeder (Positivfall) UND
eine Gegenprobe (etwas, das er NICHT zaehlen darf). Scheitert eine Probe,
bricht das Skript mit Rueckgabewert 2 ab und nennt KEINE Zahl.

Drei Fallen dieser Datei, gegen die geeicht wird:
  1. Kommentare zitieren alte Formen. `index.html` enthaelt zwei Kommentare
     von 284 000 bzw. 88 500 Zeichen, in denen fast jeder Rollenname vorkommt.
  2. Es gibt EINFACHE und DOPPELTE Anfuehrungszeichen.
  3. Rollen werden ueber ZWEI verschiedene Felder abgefragt: `user.role`
     (die Anmelde-Rolle) und `user.rolle` (die Anzeige-Rolle aus `workers.r`).
     Ein Zaehler, der nur eines kennt, meldet "kommt nicht vor".

UMFANG
──────
Gemessen wird AUSSCHLIESSLICH der Quelltext von `index.html`. Ueber den
tatsaechlichen Zeilenschutz der laufenden Datenbank sagt dieses Skript NICHTS.

AUFRUF
──────
    python scripts/rechte_rollen_messen.py            # Selbstprobe + Messung
    python scripts/rechte_rollen_messen.py --json     # zusaetzlich JSON
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

QUELLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "index.html")


# ───────────────────────── Werkzeug ─────────────────────────

def lies(pfad):
    with io.open(pfad, "r", encoding="utf-8", errors="replace", newline="") as f:
        return f.read()


def zeilenfeld(text):
    aus = []
    z = 1
    for ch in text:
        aus.append(z)
        if ch == "\n":
            z += 1
    return aus


def code_treffer(text, feld, muster, flags=0):
    """Treffer, deren ERSTES Zeichen Code ist (also nicht im Kommentar/String)."""
    return [m for m in re.finditer(muster, text, flags) if feld[m.start()]]


def klammer_zu(text, feld, i, auf, zu):
    """Position der passenden schliessenden Klammer - nur CODE-Zeichen zaehlen.

    `text[i]` muss das oeffnende Zeichen sein. Liefert den Index des
    schliessenden Zeichens, oder -1. Anders als code_scan._klammer_zu zaehlt
    diese Fassung NUR Code-Zeichen - ein `}` in einer Zeichenkette oder in
    einem Kommentar bleibt damit aussen vor.
    """
    tiefe = 0
    n = len(text)
    j = i
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


# ───────────────────────── Die Zaehler ─────────────────────────
# Jeder Zaehler ist eine Funktion text,feld -> Wert. Zu jedem gehoert ein
# Koeder-Erwartungswert in KOEDER_ERWARTUNG.

# Die Schreibweisen der Rollenabfrage. EINE Zeile je Schreibweise, damit eine
# fehlende Form als 0 SICHTBAR wird statt in einer Summe unterzugehen.
#   Der Namensteil `[Rr]oll?e` deckt role/rolle/Role/Rolle ab; der optionale
#   Punkt-Vorsatz deckt `curUser.role`, `u.role`, `_gpRole`, `maRole`.
ROLLENNAME = r"""(?:[\w$]+\.)?_?[Rr]oll?e"""
VERGLEICH = r"""\s*(?:===|!==|==|!=)\s*"""

SCHREIBWEISEN = [
    ("role_vergleich_dopp", ROLLENNAME + VERGLEICH + r'''"[A-Za-z_]+"'''),
    ("role_vergleich_einf", ROLLENNAME + VERGLEICH + r"""'[A-Za-z_]+'"""),
    ("rolle_vergleich",     r"""\.rolle\b"""),
    ("role_lesen_ohne_vergleich", r"""\.role\b(?!\s*(?:===|!==|==|!=))"""),
    ("hasPerm_aufruf",      r"""\bhasPerm\s*\("""),
    ("canDo_aufruf",        r"""\bcanDo\s*\("""),
    ("ROLES_index",         r"""\bROLES\s*\["""),
    ("ROLLE_enum_nutzung",  r"""\bROLLE\.[A-Z]+"""),
    ("permsOverride",       r"""\bperms(?:Override|_override)\b"""),
    ("curUser_punkt_role",  r"""\bcurUser\s*\.\s*role\b"""),
]


def z_schreibweisen(text, feld):
    aus = {}
    for name, mus in SCHREIBWEISEN:
        aus[name] = len(code_treffer(text, feld, mus))
    return aus


def z_roles_katalog(text, feld):
    """Die Schluessel des ROLES-Objektliterals - die Rollen der Anwendung."""
    tr = code_treffer(text, feld, r"""\bconst\s+ROLES\s*=\s*\{""")
    if len(tr) != 1:
        return None
    auf = text.index("{", tr[0].start())
    zu = klammer_zu(text, feld, auf, "{", "}")
    if zu < 0:
        return None
    rumpf = text[auf:zu]
    # Schluessel auf oberster Ebene: nach { oder , und vor : gefolgt von {
    namen = []
    tiefe = 0
    i = 0
    while i < len(rumpf):
        if not feld[auf + i]:
            i += 1
            continue
        c = rumpf[i]
        if c == "{":
            tiefe += 1
        elif c == "}":
            tiefe -= 1
        elif tiefe == 1:
            m = re.match(r"""\s*([A-Za-z_]\w*)\s*:\s*\{""", rumpf[i:])
            if m and (rumpf[i - 1] in "{," if i > 0 else False):
                namen.append(m.group(1))
                i += m.end() - 1
                continue
        i += 1
    return namen


def z_rolle_enum(text, feld):
    """Die Werte des eingefrorenen ROLLE-Aufzaehlers."""
    tr = code_treffer(text, feld, r"""\bconst\s+ROLLE\s*=\s*Object\.freeze\s*\(\s*\{""")
    if len(tr) != 1:
        return None
    auf = text.index("{", tr[0].start())
    zu = klammer_zu(text, feld, auf, "{", "}")
    if zu < 0:
        return None
    return re.findall(r"""[A-Z_]+\s*:\s*['"]([a-z_]+)['"]""", text[auf:zu])


def z_candoi(text, feld):
    """Die Aktionen, die canDo KENNT - und die, die jemand ABFRAGT."""
    tr = code_treffer(text, feld, r"""\bfunction\s+canDo\s*\(""")
    if len(tr) != 1:
        return None
    auf = text.index("(", tr[0].start())
    kopf_zu = klammer_zu(text, feld, auf, "(", ")")
    rumpf_auf = text.index("{", kopf_zu)
    rumpf_zu = klammer_zu(text, feld, rumpf_auf, "{", "}")
    if rumpf_zu < 0:
        return None
    rumpf = text[rumpf_auf:rumpf_zu]
    # die Tafel m={...}
    mm = re.search(r"""\bconst\s+m\s*=\s*\{""", rumpf)
    tafel = []
    if mm:
        t_auf = rumpf_auf + rumpf.index("{", mm.start())
        t_zu = klammer_zu(text, feld, t_auf, "{", "}")
        inner = text[t_auf:t_zu]
        tiefe = 0
        i = 0
        while i < len(inner):
            if not feld[t_auf + i]:
                i += 1
                continue
            c = inner[i]
            if c == "{":
                tiefe += 1
            elif c == "}":
                tiefe -= 1
            elif tiefe == 1 and i > 0 and inner[i - 1] in "{,":
                k = re.match(r"""\s*([a-z_]\w*)\s*:""", inner[i:])
                if k:
                    tafel.append(k.group(1))
            i += 1
    # die Sonderfaelle: if(action==="...")
    sonder = re.findall(r"""action\s*===\s*['"]([a-z_]+)['"]""", rumpf)
    # die Abfragen im ganzen Dokument
    gefragt = {}
    for m in code_treffer(text, feld, r"""\bcanDo\s*\(\s*['"]([a-z_]+)['"]"""):
        k = m.group(1)
        gefragt[k] = gefragt.get(k, 0) + 1
    return {"definiert": sorted(set(tafel) | set(sonder)),
            "tafel": tafel, "sonder": sonder, "gefragt": gefragt}


def z_hasperm(text, feld):
    """Die Module, die ROLES kennt - und die, die jemand ABFRAGT.

    🔴 DREI SCHREIBWEISEN, und die erste Fassung kannte nur eine.
    `hasPerm(curUser,"werkzeuge")` ist die eine. `hasPerm(curUser,t.perm)`
    ist die zweite - das Modul steht dann NICHT am Aufruf, sondern in einer
    Tafel (`{pm:"maengel"}`, `{perm:"admin"}`, `{nav:"projekte"}`). Wer nur
    die erste zaehlt, meldet neun Module als "nie abgefragt", die in
    Wirklichkeit ueber die Navigationstafel jeden Aufruf gaten. Genau das ist
    dieser Messung beim ersten Anlauf passiert.
    """
    tr = code_treffer(text, feld, r"""\bconst\s+PERMS_DESC\s*=\s*\{""")
    erklaert = []
    if len(tr) == 1:
        auf = text.index("{", tr[0].start())
        zu = klammer_zu(text, feld, auf, "{", "}")
        erklaert = re.findall(r"""[{,]\s*([a-z_]+)\s*:""", text[auf:zu + 1])
    gefragt = {}
    for m in code_treffer(text, feld,
                          r"""\bhasPerm\s*\([^,\n)]{0,60},\s*['"]([a-z_]+)['"]"""):
        k = m.group(1)
        gefragt[k] = gefragt.get(k, 0) + 1
    # Schreibweise 2: das Modul kommt aus einer Variablen
    ueber_var = len(code_treffer(
        text, feld,
        r"""(?<!function )\bhasPerm\s*\([^,\n)]{0,60},\s*(?!['"])[A-Za-z_$][\w.$]*\s*\)"""))
    # Schreibweise 3: die Modulnamen in den Navigations-/Kacheltafeln
    tafel = {}
    for m in code_treffer(text, feld,
                          r"""\b(?:pm|perm|nav)\s*:\s*['"]([a-z_]+)['"]"""):
        k = m.group(1)
        tafel[k] = tafel.get(k, 0) + 1
    return {"erklaert": erklaert, "gefragt": gefragt,
            "ueber_variable": ueber_var, "in_tafel": tafel}


def z_admin_aliasse(text, feld, zl, rollen):
    """Wie viele VERSCHIEDENE Rollenmengen heissen im Code `isAdmin`?

    Eine oertliche Konstante mit dem Namen `isAdmin` ist der haeufigste
    Rollen-Riegel der Datei. Bedeutet sie an zwei Stellen ZWEI verschiedene
    Rollenmengen, dann zeigt dieselbe Oberflaeche fuer dieselbe Bedingung
    unterschiedlichen Leuten unterschiedliche Knoepfe - und der Zeilenschutz
    der Datenbank kennt nur EINE Wahrheit.
    """
    aus = {}
    for m in code_treffer(
            text, feld,
            r"""(?:const|let|var)\s+(_?[A-Za-z0-9]*[Aa]dmin[A-Za-z0-9]*)\s*=\s*([^;\n]{0,900})"""):
        name, rhs = m.group(1), m.group(2)
        if "role" not in rhs and "rolle" not in rhs and "Perm" not in rhs \
                and "canDo" not in rhs and not re.match(r"""^\s*_?is""", rhs):
            continue
        menge = tuple(sorted(set(x.lower() for x in
                                 re.findall(r"""['"]([A-Za-z_]+)['"]""", rhs))
                             & set(rollen)))
        zus = tuple(k for k in ("hasPerm", "canDo") if k in rhs)
        aus.setdefault((name, menge, zus), []).append(zl[m.start()])
    return aus


def z_rollenliterale(text, feld):
    """Alle Rollen-Zeichenketten, die im CODE mit .role/.rolle verglichen werden."""
    aus = {}
    for m in code_treffer(
            text, feld,
            ROLLENNAME + VERGLEICH + r"""(['"])([A-Za-z_]+)\1"""):
        k = m.group(2)
        aus[k] = aus.get(k, 0) + 1
    return aus


# ───────────────────────── Die Selbstprobe ─────────────────────────
# Ein Koeder JE SCHREIBWEISE, dazu Gegenproben: dieselbe Form im
# Zeilenkommentar, im Blockkommentar und in einer Zeichenkette. Der Koeder ist
# SELBST GEBAUT und haengt an keiner Stelle von index.html - sonst wuerde er
# bei der naechsten Kur mit rot oder blind.

KOEDER = r"""
const ROLES={
  admin:{l:"Administrator",modules:["projekte","admin"]},
  monteur:{l:"Monteur",modules:["projekte"]},
  viewer:{l:"Nur Lesen",modules:[]},
};
const PERMS_DESC={projekte:"P",admin:"A",niefragt:"N"};
const ROLLE=Object.freeze({ADMIN:'admin', MONTEUR:'monteur'});
function canDo(action,user,ownerId){
  if(!user)return false;const r=user.role;const isA=r==="admin";
  const m={koeder_eins:isA,koeder_zwei:isA,koeder_nie:isA};
  if(action==="koeder_sonder")return isA;
  return !!m[action];
}
function hasPerm(user,mod){return true;}
const KOEDER_NAV=[{l:"P",pm:"projekte"},{l:"A",perm:"admin"},{l:"N",nav:"niefragt"}];
function koederNav(u,t){ return KOEDER_NAV.filter(x=>hasPerm(u,x.pm)); }
// GEGENPROBE-ZEILENKOMMENTAR: canDo("darf_nicht_zaehlen") hasPerm(u,"nie_modul") ROLES["x"] a.role==="admin"
/* GEGENPROBE-BLOCKKOMMENTAR: canDo('darf_nicht_zaehlen') a.rolle permsOverride ROLLE.ADMIN */
const gegenprobe_string="canDo(\"darf_nicht_zaehlen\") hasPerm(u,'nie_modul') a.role==='admin' a.rolle ROLLE.ADMIN";
function koederAliasse(u){
  const isAdmin=u.role==="admin";                       /* Menge A */
  const isAdmin2=u.role==="admin"||u.role==='monteur';  /* Menge B */
  const _isAdmin=u.role==="admin";                      /* Menge A, anderer Name */
  const adminTabs=[1,2,3];                              /* KEINE Rollenmenge */
  return [isAdmin,isAdmin2,_isAdmin,adminTabs];
}
function koederRumpf(u){
  const a=u.role==="admin";            /* Schreibweise role_vergleich_dopp */
  const b=u.role==='monteur';          /* Schreibweise role_vergleich_einf */
  const c=(u.rolle||"").toLowerCase(); /* Schreibweise rolle_vergleich     */
  const d=u.role;                      /* role_lesen_ohne_vergleich        */
  const e=hasPerm(u,"projekte");       /* hasPerm_aufruf                   */
  const f=canDo("koeder_eins",u);      /* canDo_aufruf, doppelt zitiert    */
  const g=canDo('koeder_zwei',u);      /* canDo_aufruf, einfach zitiert    */
  const h2=ROLES[u.role];              /* ROLES_index                      */
  const i2=ROLLE.ADMIN;                /* ROLLE_enum_nutzung               */
  const j2=u.permsOverride;            /* permsOverride                    */
  const k2=curUser.role==="monteur";   /* curUser_punkt_role               */
  const l2=u.perms_override;           /* permsOverride, zweite Schreibweise */
  return [a,b,c,d,e,f,g,h2,i2,j2,k2,l2];
}
"""

KOEDER_ERWARTUNG = {
    # Schreibweise -> erwartete Anzahl IM KOEDER (Gegenproben zaehlen NICHT mit)
    "role_vergleich_dopp": 5,   # 3x koederAliasse, koederRumpf a, koederRumpf k2
    "role_vergleich_einf": 2,   # koederAliasse isAdmin2, koederRumpf b
    "rolle_vergleich": 1,       # koederRumpf c
    "role_lesen_ohne_vergleich": 3,  # canDo `user.role`, koederRumpf d, ROLES[u.role]
    "hasPerm_aufruf": 3,        # Definition + Aufruf mit Zeichenkette + mit Variablen
    "canDo_aufruf": 3,          # Definition + zwei Aufrufe
    "ROLES_index": 1,
    "ROLLE_enum_nutzung": 1,
    "permsOverride": 2,         # beide Schreibweisen
    "curUser_punkt_role": 1,
}


def selbstprobe():
    """Ein Koeder je Schreibweise plus Gegenproben. Bei Fehlschlag: False."""
    fehler = []
    text = KOEDER
    feld = ist_code(text)

    # --- A: jede Schreibweise findet ihren eigenen Koeder ---
    ist = z_schreibweisen(text, feld)
    for name, erw in KOEDER_ERWARTUNG.items():
        if ist.get(name) != erw:
            fehler.append("Schreibweise %s: %r gefunden, %r erwartet"
                          % (name, ist.get(name), erw))

    # --- B: Gegenprobe. Keine dieser Zeichenketten darf gezaehlt werden. ---
    for m in code_treffer(text, feld, r"""\bcanDo\s*\(\s*['"]([a-z_]+)['"]"""):
        if m.group(1) == "darf_nicht_zaehlen":
            fehler.append("GEGENPROBE: canDo aus Kommentar/String gezaehlt")
    for m in code_treffer(text, feld,
                          r"""\bhasPerm\s*\([^,\n)]{0,60},\s*['"]([a-z_]+)['"]"""):
        if m.group(1) == "nie_modul":
            fehler.append("GEGENPROBE: hasPerm aus Kommentar/String gezaehlt")

    # --- C: ROLES-Katalog ---
    kat = z_roles_katalog(text, feld)
    if kat != ["admin", "monteur", "viewer"]:
        fehler.append("ROLES-Katalog: %r statt ['admin','monteur','viewer']" % (kat,))

    # --- D: ROLLE-Aufzaehler ---
    en = z_rolle_enum(text, feld)
    if en != ["admin", "monteur"]:
        fehler.append("ROLLE-Aufzaehler: %r statt ['admin','monteur']" % (en,))

    # --- E: canDo definiert vs. gefragt ---
    cd = z_candoi(text, feld)
    if cd is None:
        fehler.append("canDo: Rumpf nicht gefunden")
    else:
        if sorted(cd["tafel"]) != ["koeder_eins", "koeder_nie", "koeder_zwei"]:
            fehler.append("canDo-Tafel: %r" % (sorted(cd["tafel"]),))
        if cd["sonder"] != ["koeder_sonder"]:
            fehler.append("canDo-Sonderfaelle: %r" % (cd["sonder"],))
        if sorted(cd["gefragt"]) != ["koeder_eins", "koeder_zwei"]:
            fehler.append("canDo gefragt: %r" % (sorted(cd["gefragt"]),))
        # Der KERN der Messung: eine Aktion, die niemand fragt, MUSS auffallen.
        nie = set(cd["definiert"]) - set(cd["gefragt"])
        if nie != {"koeder_nie", "koeder_sonder"}:
            fehler.append("nie gefragte Aktionen: %r statt "
                          "{'koeder_nie','koeder_sonder'}" % (nie,))

    # --- F: hasPerm-Module ---
    hp = z_hasperm(text, feld)
    if sorted(hp["erklaert"]) != ["admin", "niefragt", "projekte"]:
        fehler.append("PERMS_DESC: %r" % (sorted(hp["erklaert"]),))
    if sorted(hp["gefragt"]) != ["projekte"]:
        fehler.append("hasPerm gefragt (Zeichenkette): %r" % (sorted(hp["gefragt"]),))
    # 🔴 Koeder fuer die ZWEITE Schreibweise: das Modul kommt aus einer Variablen.
    if hp["ueber_variable"] != 1:
        fehler.append("hasPerm ueber Variable: %d statt 1" % hp["ueber_variable"])
    # 🔴 Koeder fuer die DRITTE Schreibweise: das Modul steht in der Navi-Tafel.
    if sorted(hp["in_tafel"]) != ["admin", "niefragt", "projekte"]:
        fehler.append("Module in der Navi-Tafel: %r statt "
                      "['admin','niefragt','projekte']" % (sorted(hp["in_tafel"]),))

    # --- G: Rollenliterale ---
    lit = z_rollenliterale(text, feld)
    if sorted(lit) != ["admin", "monteur"]:
        fehler.append("Rollenliterale: %r statt ['admin','monteur']" % (sorted(lit),))

    # --- G2: isAdmin-Aliasse. Zwei gleiche Namen, zwei Mengen. ---
    al = z_admin_aliasse(text, feld, zeilenfeld(text), ["admin", "monteur", "viewer"])
    schl = sorted((n, m) for (n, m, _z) in al)
    erw_al = [("_isAdmin", ("admin",)), ("isAdmin", ("admin",)),
              ("isAdmin2", ("admin", "monteur"))]
    if schl != erw_al:
        fehler.append("isAdmin-Aliasse: %r statt %r" % (schl, erw_al))
    if any(n == "adminTabs" for (n, _m, _z) in al):
        fehler.append("GEGENPROBE: adminTabs ist KEINE Rollenmenge und wurde "
                      "trotzdem gezaehlt")

    # --- H: Eine Probe, die SCHEITERN muss, wenn die Eichung blind wird. ---
    # Gegenprobe zur Gegenprobe: derselbe Koeder OHNE Kommentar-Ausblendung
    # muss MEHR finden. Faellt diese Probe aus, misst die Ausblendung nichts.
    roh = len(re.findall(r"""\bcanDo\s*\(\s*['"][a-z_]+['"]""", text))
    echt = len(code_treffer(text, feld, r"""\bcanDo\s*\(\s*['"][a-z_]+['"]"""))
    if not roh > echt:
        fehler.append("Kommentar-Ausblendung wirkungslos: roh=%d, code=%d"
                      % (roh, echt))

    if fehler:
        print("SELBSTPROBE GESCHEITERT - KEINE ZAHL IST GUELTIG:")
        for f in fehler:
            print("  * " + f)
        return False
    print("Selbstprobe bestanden: %d Schreibweisen je eigener Koeder, "
          "3 Gegenproben (Zeilenkommentar, Blockkommentar, Zeichenkette), "
          "Ausblendungs-Gegenprobe roh=%d > code=%d." %
          (len(KOEDER_ERWARTUNG), roh, echt))
    return True


# ───────────────────────── Die Messung ─────────────────────────

def messen(pfad):
    text = lies(pfad)
    feld = ist_code(text)
    zl = zeilenfeld(text)
    aus = {}
    aus["datei"] = pfad
    aus["zeilen"] = zl[-1] if zl else 0
    v = code_treffer(text, feld, r"""APP_VERSION\s*=\s*["']([^"']+)["']""")
    aus["version"] = v[0].group(1) if v else "?"

    aus["schreibweisen"] = z_schreibweisen(text, feld)
    aus["roles_katalog"] = z_roles_katalog(text, feld)
    aus["rolle_enum"] = z_rolle_enum(text, feld)
    aus["rollenliterale"] = z_rollenliterale(text, feld)
    aus["canDo"] = z_candoi(text, feld)
    aus["hasPerm"] = z_hasperm(text, feld)

    # Module je Rolle aus ROLES
    mods = {}
    tr = code_treffer(text, feld, r"""\bconst\s+ROLES\s*=\s*\{""")
    if tr:
        auf = text.index("{", tr[0].start())
        zu = klammer_zu(text, feld, auf, "{", "}")
        for m in re.finditer(
                r"""([a-z_]+)\s*:\s*\{[^{}]*?modules\s*:\s*\[([^\]]*)\]""",
                text[auf:zu]):
            mods[m.group(1)] = re.findall(r"""['"]([a-z_]+)['"]""", m.group(2))
    aus["module_je_rolle"] = mods

    alle_rollen = sorted(set(aus["roles_katalog"] or []) |
                         set(aus["rollenliterale"].keys()))
    al = z_admin_aliasse(text, feld, zl, [r.lower() for r in alle_rollen])
    aus["admin_aliasse"] = [{"name": n, "menge": list(m), "zusatz": list(z),
                             "zeilen": v} for (n, m, z), v in
                            sorted(al.items(), key=lambda x: (x[0][0], x[0][1]))]
    return aus


def bericht(a):
    print()
    print("UMFANG: %s, %d Zeilen, APP_VERSION=%s" %
          (os.path.basename(a["datei"]), a["zeilen"], a["version"]))
    print("        Gemessen wird NUR der Quelltext. Ueber den Zeilenschutz der")
    print("        laufenden Datenbank sagt diese Messung NICHTS.")
    print()
    print("--- 1. Rollen ---")
    print("ROLES-Katalog (%d): %s" % (len(a["roles_katalog"] or []),
                                      ", ".join(a["roles_katalog"] or [])))
    print("ROLLE-Aufzaehler (%d): %s" % (len(a["rolle_enum"] or []),
                                         ", ".join(a["rolle_enum"] or [])))
    nur_enum = set(a["rolle_enum"] or []) - set(a["roles_katalog"] or [])
    nur_kat = set(a["roles_katalog"] or []) - set(a["rolle_enum"] or [])
    print("  nur im Aufzaehler: %s   |   nur im Katalog: %s" %
          (sorted(nur_enum) or "-", sorted(nur_kat) or "-"))
    print()
    print("Rollen-Zeichenketten, die im CODE mit .role/.rolle verglichen werden:")
    for k, n in sorted(a["rollenliterale"].items(), key=lambda x: -x[1]):
        mark = "" if k in (a["roles_katalog"] or []) else "   <- NICHT im ROLES-Katalog"
        print("   %-18s %4d%s" % (k, n, mark))
    print()
    print("--- 2. Schreibweisen der Rollenabfrage ---")
    ges = 0
    for name, _ in SCHREIBWEISEN:
        n = a["schreibweisen"][name]
        ges += n
        print("   %-28s %5d%s" % (name, n, "   <- NULL" if n == 0 else ""))
    print("   %-28s %5d" % ("SUMME (Stellen, mit Ueberschneidung)", ges))
    print()
    print("--- 3. canDo: definiert gegen abgefragt ---")
    cd = a["canDo"]
    nie = sorted(set(cd["definiert"]) - set(cd["gefragt"]))
    print("   definierte Aktionen : %d" % len(cd["definiert"]))
    print("   je abgefragte       : %d" % len(cd["gefragt"]))
    print("   NIE abgefragt       : %d" % len(nie))
    for k in nie:
        print("       - " + k)
    print()
    print("--- 4. hasPerm: erklaerte Module gegen abgefragte ---")
    hp = a["hasPerm"]
    erreicht = set(hp["gefragt"]) | set(hp["in_tafel"])
    nie_m = sorted(set(hp["erklaert"]) - erreicht)
    print("   in PERMS_DESC erklaert            : %d" % len(hp["erklaert"]))
    print("   direkt als Zeichenkette abgefragt : %d" % len(hp["gefragt"]))
    print("   Aufrufe mit Modul aus einer Variablen: %d" % hp["ueber_variable"])
    print("   Modulnamen in den Navi-/Kacheltafeln : %d" % len(hp["in_tafel"]))
    print("   weder direkt noch ueber eine Tafel erreicht: %d  (%s)" %
          (len(nie_m), ", ".join(nie_m) or "-"))
    ohne_desc = sorted(erreicht - set(hp["erklaert"]))
    print("   gegatet, aber in PERMS_DESC nicht erklaert : %d  (%s)" %
          (len(ohne_desc), ", ".join(ohne_desc) or "-"))
    print()
    print("--- 5. `isAdmin` und seine Geschwister: ein Name, mehrere Mengen ---")
    namen = {}
    for e in a["admin_aliasse"]:
        namen.setdefault(e["name"], set()).add(tuple(e["menge"]))
        print("   %-14s %-44s %-9s %s" %
              (e["name"], "|".join(e["menge"]) or "-",
               ",".join(e["zusatz"]) or "-", e["zeilen"]))
    mehrdeutig = sorted(n for n, s in namen.items() if len(s) > 1)
    print("   Namen mit MEHR ALS EINER Rollenmenge: %d  (%s)" %
          (len(mehrdeutig), ", ".join(mehrdeutig) or "-"))
    print("   verschiedene Rollenmengen insgesamt : %d" %
          len(set(tuple(e["menge"]) for e in a["admin_aliasse"])))
    print()
    print("--- 6. Module je Rolle (ROLES) ---")
    for r, ms in a["module_je_rolle"].items():
        print("   %-14s %2d  %s" % (r, len(ms), " ".join(ms)))


def main(argv):
    if not selbstprobe():
        return 2
    a = messen(QUELLE)
    bericht(a)
    if "--json" in argv:
        ziel = os.path.join(os.path.dirname(QUELLE), "docs", "befunde",
                            "bughunt", "rechte_rollen.json")
        with io.open(ziel, "w", encoding="utf-8", newline="") as f:
            f.write(json.dumps(a, ensure_ascii=False, indent=1))
        print("\nJSON: " + ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
