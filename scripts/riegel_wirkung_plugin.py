# -*- coding: utf-8 -*-
"""pytest-Plugin: misst die WIRKUNG jedes Riegels, nicht seine Anwesenheit.

WOZU
────
Ein eingesammelter Fall, der gruen meldet, hat damit noch nichts geprueft.
Drei Formen sind belegt und statisch kaum zu unterscheiden:

  a) der Fall fuehrt im Lauf KEINE einzige Zusicherung aus
     (kein assert, oder ein `if ...: return` vor dem Rumpf)
  b) der Fall fuehrt eine Zusicherung ueber eine LEERE Grundgesamtheit aus
        treffer = [b for b in re.findall(MUSTER, quelle) if ...]
        assert not treffer
     ist gruen, sobald MUSTER nicht mehr trifft - die Liste ist dann leer,
     nicht weil der Code stimmt, sondern weil nichts gemessen wurde
  c) eine Schleife laeuft ueber eine LEERE Menge, die Zusicherungen in
     ihrem Rumpf werden also nie ausgefuehrt

ERSTE FASSUNG WAR BLIND
───────────────────────
Sie klammerte nur Kurzschreibungen, die DIREKT im Pruefausdruck eines
`assert` stehen. Die vorherrschende Schreibweise im Repo ist aber
`X = [...]` und erst danach `assert not X`. Ergebnis: 63 aufgezeichnete
Grundgesamtheiten auf 3177 Faelle - ein Messgeraet, das fuer genau die
gesuchte Ereignisklasse blind ist. Jetzt wird JEDE Kurzschreibung und JEDE
`for`-Schleife im Testmodul geklammert, unabhaengig vom Ort.

AUFRUF
──────
    set EPK_WIRKUNG_OUT=...\\wirkung.json
    python -m pytest tests/ -p scripts.riegel_wirkung_plugin -q

Das Plugin aendert KEINE Datei. Es liest keinen pyc-Zwischenspeicher
(sonst kaeme eine Fassung OHNE Zaehler von der Platte und das Messgeraet
meldete ueberall 0) und schreibt keinen.
"""
import ast
import builtins
import json
import os
import sys

# ── Sammelstelle ──────────────────────────────────────────────────────────
_AKTUELL = [None]
_TREFFER = {}
_AUSSERHALB = {"asserts": 0, "pop": 0}


def _eintrag():
    nid = _AKTUELL[0]
    if nid is None:
        return None
    return _TREFFER.setdefault(nid, {"asserts": 0, "pop": []})


def _epk_hit_(zeile):
    e = _eintrag()
    if e is None:
        _AUSSERHALB["asserts"] += 1
        return
    e["asserts"] += 1


def _epk_pop_(art, zeile, quelltext, iterierbar):
    """Grundgesamtheit einer Kurzschreibung oder einer for-Schleife."""
    werte = list(iterierbar)
    e = _eintrag()
    if e is None:
        _AUSSERHALB["pop"] += 1
    else:
        e["pop"].append({"art": art, "zeile": zeile,
                         "quelle": quelltext, "n": len(werte)})
    return werte


builtins._epk_hit_ = _epk_hit_
builtins._epk_pop_ = _epk_pop_

_GRENZE = 90


class _Umbau(ast.NodeTransformer):
    """Klammert JEDE Kurzschreibung und JEDE for-Schleife, ueberall im Modul."""

    def _klammere(self, art, zeile, knoten):
        try:
            txt = ast.unparse(knoten)[:_GRENZE]
        except Exception:
            txt = "<nicht darstellbar>"
        return ast.Call(
            func=ast.Name(id="_epk_pop_", ctx=ast.Load()),
            args=[ast.Constant(value=art), ast.Constant(value=zeile),
                  ast.Constant(value=txt), knoten],
            keywords=[])

    def _schon_geklammert(self, knoten):
        return (isinstance(knoten, ast.Call)
                and isinstance(knoten.func, ast.Name)
                and knoten.func.id == "_epk_pop_")

    def _comp(self, node):
        self.generic_visit(node)
        if node.generators and not self._schon_geklammert(node.generators[0].iter):
            g = node.generators[0]
            g.iter = self._klammere("comp", getattr(node, "lineno", 0), g.iter)
        return node

    visit_ListComp = _comp
    visit_SetComp = _comp
    visit_GeneratorExp = _comp
    visit_DictComp = _comp

    def visit_For(self, node):
        self.generic_visit(node)
        if not self._schon_geklammert(node.iter):
            node.iter = self._klammere("for", node.lineno, node.iter)
        return node

    def visit_Assert(self, node):
        self.generic_visit(node)
        zaehler = ast.Expr(value=ast.Call(
            func=ast.Name(id="_epk_hit_", ctx=ast.Load()),
            args=[ast.Constant(value=node.lineno)], keywords=[]))
        return [zaehler, node]


def _haenge_ein():
    import _pytest.assertion.rewrite as rw

    if getattr(rw, "_epk_eingehaengt", False):
        return
    urspruenglich = rw.rewrite_asserts

    def rewrite_asserts(mod, source, module_path=None, config=None):
        try:
            _Umbau().visit(mod)
            ast.fix_missing_locations(mod)
        except Exception as e:
            print("EPK-Umbau fehlgeschlagen fuer %s: %s" % (module_path, e),
                  file=sys.stderr)
        return urspruenglich(mod, source, module_path, config)

    rw.rewrite_asserts = rewrite_asserts
    rw._read_pyc = lambda *a, **k: None
    sys.dont_write_bytecode = True
    rw._epk_eingehaengt = True


_haenge_ein()


_ERGEBNIS = {}


def pytest_runtest_logstart(nodeid, location):
    _AKTUELL[0] = nodeid
    _TREFFER.setdefault(nodeid, {"asserts": 0, "pop": []})


def pytest_runtest_logfinish(nodeid, location):
    _AKTUELL[0] = None


def pytest_runtest_logreport(report):
    if report.when == "call":
        _ERGEBNIS[report.nodeid] = report.outcome
    elif report.when == "setup" and report.outcome in ("skipped", "failed"):
        _ERGEBNIS.setdefault(report.nodeid, report.outcome)


def pytest_sessionfinish(session, exitstatus):
    ziel = os.environ.get("EPK_WIRKUNG_OUT")
    if not ziel:
        return
    daten = {
        "exitstatus": exitstatus,
        "ausserhalb": _AUSSERHALB,
        "faelle": {nid: {"ausgang": _ERGEBNIS.get(nid, "?"),
                         "asserts": w["asserts"], "pop": w["pop"]}
                   for nid, w in _TREFFER.items()},
    }
    with open(ziel, "w", encoding="utf-8", newline="") as f:
        json.dump(daten, f, ensure_ascii=False)
