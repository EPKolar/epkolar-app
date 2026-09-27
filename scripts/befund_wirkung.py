# -*- coding: utf-8 -*-
"""Messung (2): welche eingesammelten Faelle koennen NIE rot werden?

Zwei Quellen werden zusammengefuehrt:

  LAUFZEIT  aus der JSON von scripts/riegel_wirkung_plugin.py
            - wie viele Zusicherungen hat der Fall WIRKLICH ausgefuehrt
            - wie gross war jede Grundgesamtheit (Kurzschreibung, for-Schleife)
  STATISCH  aus dem Syntaxbaum der Testdateien
            - Tautologien (assert True / assert 1 / assert "text" / x == x)
            - try/except, das den Fehler schluckt
            - `if ...: return` vor dem Rumpf

Klassen im Urteil:
  A  gruen, aber 0 Zusicherungen ausgefuehrt      -> kann nicht rot werden
  B  gruen, 0 Zusicherungen UND leere Schleife    -> Rumpf nie erreicht
  C  gruen, ALLE Grundgesamtheiten leer           -> nichts gemessen
  D  gruen, EINZELNE Grundgesamtheit leer         -> Verdacht, einzeln belegen
  E  Tautologie als einzige Zusicherung
  F  rot im Lauf

Aufruf:
    python scripts/befund_wirkung.py <wirkung.json> [--kurz]
"""
import ast
import json
import os
import sys
from collections import defaultdict

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.environ.get("EPK_TESTS_DIR") or os.path.join(WURZEL, "tests")

PRUEF_NAMEN = ("fail", "raises", "warns")


def _ist_tautologie(test):
    if isinstance(test, ast.Constant):
        if test.value is True:
            return "assert True"
        if isinstance(test.value, (int, float)) and test.value != 0:
            return "assert %r (konstant wahr)" % test.value
        if isinstance(test.value, str) and test.value:
            return "assert %r... (nichtleerer Text = immer wahr)" % test.value[:40]
        return None
    if isinstance(test, ast.Compare) and len(test.ops) == 1:
        try:
            links = ast.unparse(test.left)
            rechts = ast.unparse(test.comparators[0])
        except Exception:
            return None
        if links == rechts and isinstance(test.ops[0], (ast.Eq, ast.Is, ast.LtE,
                                                       ast.GtE, ast.In)):
            return "Vergleich stimmt immer: %s" % ast.unparse(test)[:60]
        if isinstance(test.left, ast.Call) and getattr(test.left.func, "id", "") == "len" \
                and isinstance(test.comparators[0], ast.Constant):
            w = test.comparators[0].value
            if isinstance(test.ops[0], ast.GtE) and w == 0:
                return "len(...) >= 0 stimmt immer"
            if isinstance(test.ops[0], ast.Gt) and isinstance(w, int) and w < 0:
                return "len(...) > %d stimmt immer" % w
    return None


class _Fallanalyse(ast.NodeVisitor):
    def __init__(self):
        self.funktionen = {}

    def _besuche_fn(self, node):
        if not node.name.startswith("test"):
            self.generic_visit(node)
            return
        info = {"zeile": node.lineno, "asserts": 0, "tautologien": [],
                "prueferufe": 0, "frueher_ausstieg": None,
                "schluckendes_except": [], "skip": False}
        for k in ast.walk(node):
            if isinstance(k, ast.Assert):
                info["asserts"] += 1
                t = _ist_tautologie(k.test)
                if t:
                    info["tautologien"].append((k.lineno, t))
            elif isinstance(k, ast.Call):
                nm = getattr(k.func, "attr", None) or getattr(k.func, "id", None)
                if nm in PRUEF_NAMEN:
                    info["prueferufe"] += 1
                if nm == "skip":
                    info["skip"] = True
                if nm and nm.startswith("assert"):
                    info["prueferufe"] += 1
            elif isinstance(k, ast.With):
                for it in k.items:
                    try:
                        if "raises" in ast.unparse(it.context_expr):
                            info["prueferufe"] += 1
                    except Exception:
                        pass
        koerper = [s for s in node.body
                   if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)
                           and isinstance(s.value.value, str))]
        for s in koerper[:2]:
            if isinstance(s, ast.If) and len(s.body) == 1 and \
                    isinstance(s.body[0], (ast.Return, ast.Pass)) and not s.orelse:
                try:
                    info["frueher_ausstieg"] = (s.lineno, ast.unparse(s.test)[:110])
                except Exception:
                    info["frueher_ausstieg"] = (s.lineno, "<nicht darstellbar>")
                break
        for k in ast.walk(node):
            if isinstance(k, ast.Try):
                im_try = any(isinstance(s, ast.Assert)
                             for b in k.body for s in ast.walk(b))
                if not im_try:
                    continue
                for h in k.handlers:
                    hat_check = any(isinstance(s, ast.Assert) for s in ast.walk(h))
                    if not hat_check:
                        info["schluckendes_except"].append(k.lineno)
                        break
        self.funktionen[node.name] = info

    visit_FunctionDef = _besuche_fn
    visit_AsyncFunctionDef = _besuche_fn


def statik():
    ergebnis = {}
    for name in sorted(os.listdir(TESTS)):
        if not name.startswith("test_") or not name.endswith(".py"):
            continue
        pfad = os.path.join(TESTS, name)
        with open(pfad, "r", encoding="utf-8", errors="replace") as f:
            quelle = f.read()
        try:
            baum = ast.parse(quelle, filename=pfad)
        except SyntaxError as e:
            print("SYNTAXFEHLER in %s: %s" % (name, e))
            continue
        a = _Fallanalyse()
        a.visit(baum)
        for fn, info in a.funktionen.items():
            ergebnis["tests/%s::%s" % (name, fn)] = info
    return ergebnis


def _grund(s):
    g = []
    if not s:
        return ["statisch nicht zugeordnet (Parameter-Fall?) - einzeln ansehen"]
    if s.get("asserts", 0) == 0 and not s.get("prueferufe"):
        g.append("Funktion enthaelt gar kein assert")
    if s.get("frueher_ausstieg"):
        g.append("frueher Ausstieg Z%d:  if %s: return"
                 % (s["frueher_ausstieg"][0], s["frueher_ausstieg"][1]))
    if s.get("schluckendes_except"):
        g.append("schluckendes except Z%s" % s["schluckendes_except"])
    if s.get("skip"):
        g.append("ruft skip()")
    return g or ["Grund offen - einzeln ansehen"]


def main(argv):
    if not argv:
        print("Aufruf: befund_wirkung.py <wirkung.json> [--kurz]")
        return 2
    kurz = "--kurz" in argv
    with open(argv[0], "r", encoding="utf-8") as f:
        lauf = json.load(f)
    st = statik()
    faelle = lauf["faelle"]

    pops = [p for w in faelle.values() for p in w["pop"]]
    print("pytest-exitstatus aus der Messdatei: %s" % lauf["exitstatus"])
    print("Faelle im Lauf: %d   statisch erfasste Faelle: %d" % (len(faelle), len(st)))
    ausg = defaultdict(int)
    for w in faelle.values():
        ausg[w["ausgang"]] += 1
    print("Ausgaenge: %s" % dict(ausg))
    print("Ausgefuehrte Zusicherungen: %d" % sum(w["asserts"] for w in faelle.values()))
    print("Aufgezeichnete Grundgesamtheiten: %d (davon leer: %d) in %d Faellen"
          % (len(pops), sum(1 for p in pops if p["n"] == 0),
             sum(1 for w in faelle.values() if w["pop"])))
    print("ausserhalb eines Falls: %s" % lauf.get("ausserhalb"))
    print("=" * 74)

    A, B, C, D, E, F = [], [], [], [], [], []
    for nid, w in sorted(faelle.items()):
        s = st.get(nid) or st.get(nid.split("[")[0])
        if w["ausgang"] == "failed":
            F.append(nid)
            continue
        if w["ausgang"] != "passed":
            continue
        leer = [p for p in w["pop"] if p["n"] == 0]
        if w["asserts"] == 0 and not (s or {}).get("prueferufe"):
            if leer and any(p["art"] == "for" for p in leer):
                B.append((nid, w, s, leer))
            else:
                A.append((nid, w, s))
            continue
        if w["pop"] and len(leer) == len(w["pop"]):
            C.append((nid, w, s, leer))
            continue
        if leer:
            D.append((nid, w, s, leer))
        if (s or {}).get("tautologien") and len(s["tautologien"]) >= s.get("asserts", 0) \
                and not s.get("prueferufe"):
            E.append((nid, s))

    print("A) GRUEN, aber 0 Zusicherungen ausgefuehrt: %d" % len(A))
    for nid, w, s in A:
        print("   %s" % nid)
        for g in _grund(s):
            print("      %s" % g)

    print("")
    print("B) GRUEN, 0 Zusicherungen UND leere Schleife (Rumpf nie erreicht): %d" % len(B))
    for nid, w, s, leer in B:
        print("   %s" % nid)
        for p in leer:
            print("      %s Z%d  n=0  <- %s" % (p["art"], p["zeile"], p["quelle"]))

    print("")
    print("C) GRUEN, ALLE Grundgesamtheiten leer (nichts gemessen): %d" % len(C))
    for nid, w, s, leer in C:
        print("   %s   (asserts=%d)" % (nid, w["asserts"]))
        for p in leer:
            print("      %s Z%d  n=0  <- %s" % (p["art"], p["zeile"], p["quelle"]))

    print("")
    print("E) Tautologie als einzige Zusicherung: %d" % len(E))
    for nid, s in E:
        for z, t in s["tautologien"]:
            print("   %s  Z%d  %s" % (nid, z, t))

    print("")
    print("F) ROT im Lauf: %d" % len(F))
    for nid in F:
        print("   %s" % nid)

    print("")
    print("=" * 74)
    print("D) VERDACHT: einzelne leere Grundgesamtheit, andere Zusicherungen liefen: %d"
          % len(D))
    if not kurz:
        for nid, w, s, leer in D:
            print("   %s  (asserts=%d, %d von %d Mengen leer)"
                  % (nid, w["asserts"], len(leer), len(w["pop"])))
            for p in leer:
                print("      %s Z%d  n=0  <- %s" % (p["art"], p["zeile"], p["quelle"]))

    print("")
    print("WEITERE STATISCHE VERDACHTE (zur Laufzeit gedeckt)")
    va = [(nid, s) for nid, s in sorted(st.items())
          if s.get("frueher_ausstieg") and nid in faelle
          and faelle[nid]["ausgang"] == "passed" and faelle[nid]["asserts"] > 0]
    print("  frueher Ausstieg, Rumpf lief trotzdem: %d" % len(va))
    for nid, s in va:
        print("     %s  Z%d  if %s: return"
              % (nid, s["frueher_ausstieg"][0], s["frueher_ausstieg"][1]))
    vs = [(nid, s) for nid, s in sorted(st.items())
          if s.get("schluckendes_except") and nid in faelle]
    print("  try/except schluckt eine Zusicherung: %d" % len(vs))
    for nid, s in vs:
        print("     %s  Z%s" % (nid, s["schluckendes_except"]))
    vt = [(nid, s) for nid, s in sorted(st.items())
          if s.get("tautologien") and nid not in [x[0] for x in E]]
    print("  Tautologie neben anderen Zusicherungen: %d" % len(vt))
    for nid, s in vt:
        for z, t in s["tautologien"]:
            print("     %s  Z%d  %s" % (nid, z, t))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
