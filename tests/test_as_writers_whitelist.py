# -*- coding: utf-8 -*-
"""Register #31e — Schreibstellen-Inventar + statisches Gate (Abrechnungs-Lebensader).

Juprowa ist die reine Maschinen-Bruecke App<->OFFA; jeder DIREKTE Schreibzugriff auf `arbeitsscheine`
(ausserhalb der Offline-Queue SQ.push -> _translateAndExec) umgeht das EINE Schreibgesetz (updAs/SQ) und
ist deshalb hoch-regressionskritisch. Dieses Gate FRIERT die auditierte Whitelist ein: taucht ein neuer,
un-auditierter direkter `_sbPatch/_sbPost("arbeitsscheine", ...)` auf ODER wandert ein Writer in einen
User-Handler, schlaegt der Test fehl und erzwingt eine erneute Pruefung (siehe
docs/dispo/SCHREIBSTELLEN_INVENTAR_arbeitsscheine.md).

Stand-Inventar (v3.9.756: 5 direkte Writer, alle Maschinen-Bruecke):
  _juprowaSync      x2  (PULL: existierenden Schein patchen / neuen posten — App<-OFFA)
  _juprowaPush      x3  (PUSH: push_error bei RPC-non-ok / echo-gated Reset / push_error im catch)
W2 (_juprowaMarkEdited, redundanter push_pending=true-Direktwrite = W2 der 31g-Forensik) wurde in v3.9.756
STILLGELEGT: push_pending fliesst jetzt nur ueber den SQ-Pfad (W1), der Push ueber die per-Schein-Debounce-
Klammer _juprowaSchedulePush. Damit ist die Whitelist von 6 auf 5 gesunken.
"""
import re

_WRITER = re.compile(r"""_sb(?:Patch|Post|Upsert|Delete|DeleteWhere)\((['"])arbeitsscheine\1""")
_FN = re.compile(r"(?:async\s+function|function)\s+(_?[A-Za-z0-9]+)\s*\(")

# Eingefrorene Whitelist: Funktion -> erwartete Anzahl direkter arbeitsscheine-Writer.
# v3.9.756: W2 (_juprowaMarkEdited push_pending:true-Direktwrite) STILLGELEGT -> von 6 auf 5 runter.
# push_pending fliesst jetzt ausschliesslich ueber den SQ-Pfad (W1); der Push laeuft ueber die
# per-Schein-Debounce-Klammer _juprowaSchedulePush (siehe #31g-Konsolidierung).
_WHITELIST = {"_juprowaSync": 2, "_juprowaPush": 3}
_WHITELIST_TOTAL = sum(_WHITELIST.values())

# User-Schreib-Handler: hier darf NIE ein direkter arbeitsscheine-Writer stehen — Writes gehen ueber SQ.push.
_USER_HANDLERS = ("const updAs=", "const storno=", "const verschieben=")


def _writer_sites(index_html):
    sites = []
    for m in _WRITER.finditer(index_html):
        pre = index_html[:m.start()]
        fns = list(_FN.finditer(pre))
        name = fns[-1].group(1) if fns else "?"
        line = index_html.count("\n", 0, m.start()) + 1
        sites.append((line, name))
    return sites


def test_genau_sechs_direkte_writer(index_html):
    sites = _writer_sites(index_html)
    assert len(sites) == _WHITELIST_TOTAL, (
        "Anzahl direkter arbeitsscheine-Writer veraendert (%d statt %d). Neuer/verschobener Direkt-Write "
        "auf der Abrechnungs-Lebensader — Inventar + Whitelist neu auditieren.\nGefunden: %s"
        % (len(sites), _WHITELIST_TOTAL, sites)
    )


def test_writer_nur_in_whitelist_funktionen(index_html):
    counts = {}
    for _line, name in _writer_sites(index_html):
        counts[name] = counts.get(name, 0) + 1
    assert counts == _WHITELIST, (
        "Whitelist-Verteilung verletzt.\nErwartet: %s\nGefunden : %s\n"
        "Ein direkter arbeitsscheine-Write ausserhalb der Sync/Push-Maschinerie umgeht das EINE "
        "Schreibgesetz (updAs/SQ)." % (_WHITELIST, counts)
    )


def test_keine_direkten_writer_in_user_handlern(index_html):
    """updAs/storno/verschieben duerfen NIE direkt auf arbeitsscheine schreiben — nur via SQ.push."""
    for marker in _USER_HANDLERS:
        assert marker in index_html, "User-Handler-Marker '%s' nicht gefunden (Refactor?)" % marker
        start = index_html.index(marker)
        # Ende des Handlers: bis zum naechsten 'const <name>=' auf gleicher Ebene (heuristisch 1500 Zeichen reichen).
        seg = index_html[start:start + 1500]
        assert '_sbPatch("arbeitsscheine"' not in seg and "_sbPatch('arbeitsscheine'" not in seg, (
            "Direkter _sbPatch auf arbeitsscheine im User-Handler '%s' — muss ueber SQ.push laufen" % marker)
        assert '_sbPost("arbeitsscheine"' not in seg and "_sbPost('arbeitsscheine'" not in seg, (
            "Direkter _sbPost auf arbeitsscheine im User-Handler '%s' — muss ueber SQ.push laufen" % marker)


def test_legitimer_drain_reset_ist_echo_gated(index_html):
    """Der einzige push_pending=false-Reset (der 'Drain'-Write) haengt am v616-Echo-Gate — nie blind."""
    assert "if(respData&&respData.ID){_v616Acc=true;patchData.push_pending=false;" in index_html, \
        "echo-gated Reset (v616) fehlt/veraendert — der Drain-Reset darf NIE ohne Bestaetigung schreiben"
