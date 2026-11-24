# -*- coding: utf-8 -*-
"""Zaehlbeispiel Monatsfreigabe: rechnet fuer EINEN Mitarbeiter und EINEN Monat mit den ECHTEN Funktionen aus
index.html (_pzeBuildRows, _ezTageAusStempel, _ezDayEff ueber _mfSnapshot, Gegenprobe _ezEffTage) die Zahlen,
die der Monteur in der Monatsfreigabe sehen wuerde: Stempelstunden gesamt, Arbeitstage, Anzahl Entfernungszulage
klein/mittel/gross, dazu je Tag. KEINE Euro-Betraege.

Eingabe: JSON-Datei (Export siehe sql/MONATSFREIGABE_ZAEHLBEISPIEL_EXPORT.sql), Form:
  {"worker": {"id": "w4", "name": "Nachname", "role": "Monteur"}, "ym": "2026-10",
   "stempel_log": [{"worker_id": "w4", "ts": "...", "direction": "kommen|gehen", ...}],
   "pause_rules": {...} oder null, "ez_tage": [{"worker_id": "w4", "datum": "2026-10-05", "stufe": "mittel", "aktiv": true}],
   "abs": {"<name>_<iso>": {"type": "urlaub", "status": "genehmigt"}} (optional), "approvals": {} (optional)}
Aufruf: python scripts/mf_zaehlbeispiel.py eingabe.json   (oder --selbsttest mit erfundenen Daten)
Nur lesen, nichts wird geschrieben oder gesendet.
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WURZEL, "tests"))

FUNKTIONEN = ["_ezWtag", "_ezKey", "_ezMonthGrid", "_ezKW", "_ezDayEff", "_ezEffTage", "_ezStufeMeta", "_ezAbsSet",
              "_ezStufeFromRow", "_easterSunday", "_isATFeiertag", "_zeMonatName", "_vrDE", "_nWort", "_pzeBuildRows",
              "_ezTageAusStempel", "_stPauseAbzug"]


def _fn(s, name):
    from test_monatsfreigabe_v1108 import _fn as f
    return f(s, name)


def _pze_helfer(s):
    """Alle function _pze*/_kv*/_resolveApprK, die _pzeBuildRows braucht (namentlich gesucht, nicht geraten)."""
    namen = set(re.findall(r"\bfunction (_pze\w+|_st[A-Z]\w*|_kv[A-Z]\w*|_resolveApprK)\(", s))
    return [n for n in sorted(namen) if n not in ("_pzeBuildRows", "_pzePdf", "_stPauseAbzug") and not n.startswith("_stLoad") and ("async function " + n + "(") not in s]


SELBST = {"worker": {"id": "wX", "name": "Beispiel", "role": "Monteur"}, "ym": "2026-10",
          "stempel_log": [], "pause_rules": None,
          "ez_tage": [{"worker_id": "wX", "datum": "2026-10-07", "stufe": "mittel", "aktiv": True}], "abs": {}, "approvals": {}}
for tag, (k, g) in {"01": ("07:00", "15:30"), "02": ("07:00", "12:00"), "05": ("06:30", "17:00"), "07": ("07:00", "16:00")}.items():
    SELBST["stempel_log"].append({"worker_id": "wX", "ts": "2026-10-%sT%s:00+02:00" % (tag, k), "direction": "kommen"})
    SELBST["stempel_log"].append({"worker_id": "wX", "ts": "2026-10-%sT%s:00+02:00" % (tag, g), "direction": "gehen"})


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    daten = SELBST if argv[1] == "--selbsttest" else json.load(io.open(argv[1], encoding="utf-8"))
    s = io.open(os.path.join(WURZEL, "index.html"), encoding="utf-8", newline="").read().replace("\r\n", "\n")
    i = s.index("//@MONATSFREIGABE-START")
    blk = s[i:s.index("//@MONATSFREIGABE-END", i)]
    pm = "\n".join(m.group(0).replace("const ", "var ") for m in re.finditer(r"const STEMPEL_[A-Z_]+=[^;]*;", s) if "FALLBACK" not in m.group(0))
    fb = re.search(r"const STEMPEL_PAUSE_FALLBACK=\{[^}]*\};", s).group(0).replace("const ", "var ")
    iw = re.search(r"const isoWof=\(dd\)=>\{.*?\};", s).group(0).replace("const ", "var ")
    teile = [pm, fb, iw, "var AT_T={};", "var React={createElement:function(){return null;}};"]
    for n in FUNKTIONEN + _pze_helfer(s):
        try:
            teile.append(_fn(s, n))
        except AssertionError:
            pass
    js = "\n".join(teile) + "\n" + blk + r"""
var D=JSON.parse(process.argv[2]);var w=D.worker;var ym=D.ym;
var y=+ym.slice(0,4),m=+ym.slice(5,7);var bis=ym+"-"+String(new Date(y,m,0).getDate()).padStart(2,"0");
var evs=(D.stempel_log||[]).map(function(e){return Object.assign({},e,{ts:e.ts});});
var rules=D.pause_rules||STEMPEL_PAUSE_FALLBACK;
var rows=_pzeBuildRows(w,ym+"-01",bis,evs,rules,[],{},[]);
var hMap=_ezTageAusStempel(evs,w,D.pause_rules,ym);
var flags={};(D.ez_tage||[]).forEach(function(x){flags[_ezKey(x.worker_id,x.datum)]={stufe:_ezStufeFromRow(x.stufe,!!x.aktiv)};});
var absSet=_ezAbsSet(D.abs||{},D.approvals||{},w.name);
var snap=_mfSnapshot(w.id,ym,rows,hMap,flags,absSet);
var gegen=_ezEffTage(hMap,flags,w.id,{klein:0,mittel:0,gross:0},absSet);
console.log(JSON.stringify({summe:snap.summe,tage:snap.tage,gegenprobe:{klein:gegen.tageKlein,mittel:gegen.tageMittel,gross:gegen.tageGross}}));
"""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "z.cjs")
        io.open(p, "w", encoding="utf-8", newline="\n").write(js)
        r = subprocess.run(["node", p, json.dumps(daten)], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        print(r.stderr[-2000:])
        return 3
    e = json.loads(r.stdout.strip().splitlines()[-1])
    s_ = e["summe"]
    print("Mitarbeiter %s, Monat %s" % (daten["worker"]["id"], daten["ym"]))
    print("Stempelstunden gesamt: %d:%02d h" % (s_["min"] // 60, s_["min"] % 60))
    print("Arbeitstage:           %d" % s_["arbeitstage"])
    print("Entfernungszulage klein/mittel/gross: %d / %d / %d" % (s_["z"]["klein"], s_["z"]["mittel"], s_["z"]["gross"]))
    g = e["gegenprobe"]
    gleich = [g["klein"], g["mittel"], g["gross"]] == [s_["z"]["klein"], s_["z"]["mittel"], s_["z"]["gross"]]
    print("Gegenprobe _ezEffTage: %d / %d / %d -> %s" % (g["klein"], g["mittel"], g["gross"], "gleich" if gleich else "ABWEICHUNG"))
    for t in e["tage"]:
        print("  %s  %d:%02d h  %s" % (t["d"], t["min"] // 60, t["min"] % 60, t["st"] or "-"))
    return 0 if gleich else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
