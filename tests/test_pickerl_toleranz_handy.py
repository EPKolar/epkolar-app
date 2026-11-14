# -*- coding: utf-8 -*-
"""Handy-Befund F1 (14.11.2026): abgelaufene Pickerl standen ORANGE in der Fahrzeugliste.

Ursache: das Listen-Abzeichen faerbte `warn` und `overdue` gleich (pickerlWarn).
Regel jetzt (Paragraph 57a KFG): Begutachtung bis Ende des 4. Monats nach dem
gelochten Monat erlaubt. Innerhalb der Toleranz = orange "Toleranzfrist bis ...",
danach rot "abgelaufen".

Der Riegel FUEHRT die beiden Helfer woertlich aus index.html aus (mit festem
"heute" = 14.11.2026, den Faellen vom Handy) und prueft zusaetzlich, dass Liste,
Kachel-Abzeichen, QR-Abzeichen und Home-Banner dieselbe Regel benutzen.
UMKEHRPROBE: Toleranz auf 0 Monate -> die Messung MUSS rot werden.
"""
import json
import pathlib
import re

from conftest import run_node_snippet

SRC = pathlib.Path(__file__).resolve().parent.parent / "index.html"
HTML = SRC.read_text(encoding="utf-8")

_FAKE_HEUTE = (
    "const TIME_DAY=86400000;const window={};const _RD=Date;"
    "globalThis.Date=class extends _RD{constructor(...a){if(a.length)super(...a);else super(2026,10,14,10,0,0);}"
    "static now(){return new _RD(2026,10,14,10,0,0).getTime();}};\n"
)

FAELLE = {
    # Handy-Faelle (heute 14.11.2026)
    "2026-06-01": ("overdue", "2026-10-31"),   # TU-266BP (X5): Toleranz vorbei -> ROT
    "2026-11-10": ("toleranz", "2027-03-31"),  # TU-516CP
    "2026-09-15": ("toleranz", "2027-01-31"),  # TU-266BP Mercedes
    "2026-08-10": ("toleranz", "2026-12-31"),  # TU-545BC
    "2026-07-31": ("toleranz", "2026-11-30"),  # Grenze: Toleranz endet Ende November
    "2026-07-01": ("toleranz", "2026-11-30"),  # Monat zaehlt, nicht der Tag
    "2026-06-30": ("overdue", "2026-10-31"),
    "2026-12-01": ("warn", None),              # 17 Tage hin
    "2027-06-01": ("ok", None),
}


def _helfer(html):
    a = re.search(r"window\._pickerlStatus=\(datum,warnDays\)=>\{.*?\};", html)
    b = re.search(r"window\._pickerlFrist=\(datum\)=>\{.*\};", html)  # gierig bis Zeilenende
    assert a and b, "Pickerl-Helfer nicht gefunden (Umbau in index.html?)"
    return a.group(0) + "\n" + b.group(0)


def _lauf(node_exe, koerper):
    js = _FAKE_HEUTE + koerper + "\nconst F=%s;const out={};for(const d of F){out[d]=window._pickerlFrist(d);}" \
        "out['__leer']=window._pickerlFrist('');out['__kaputt']=window._pickerlFrist('abc');" \
        "process.stdout.write(JSON.stringify(out));" % json.dumps(list(FAELLE))
    return json.loads(run_node_snippet(node_exe, js))


def _abweichungen(out):
    fehl = []
    for d, (st, tb) in FAELLE.items():
        r = out[d]
        if r["st"] != st or (tb is not None and r["tolBis"] != tb):
            fehl.append((d, r, st, tb))
    return fehl


def test_toleranzregel_handy_faelle(node_exe):
    out = _lauf(node_exe, _helfer(HTML))
    assert _abweichungen(out) == []
    assert out["__leer"] is None and out["__kaputt"] is None


def test_umkehrprobe_ohne_toleranz(node_exe):
    """Toleranz auf 0 Monate -> die drei Toleranzfaelle kippen, der Riegel MUSS rot werden."""
    alt = _helfer(HTML).replace("(+m[2]-1)+5,0)", "(+m[2]-1)+1,0)")
    assert alt != _helfer(HTML), "Umkehrprobe greift nicht - Ausdruck umgebaut?"
    assert _abweichungen(_lauf(node_exe, alt)) != [], "UMKEHRPROBE BLIND"


def test_alle_pickerl_anzeigen_nutzen_dieselbe_regel():
    # Listenansicht + Kachel-Abzeichen
    assert "const _pkFr=window._pickerlFrist(f.pickerl)||{};" in HTML
    assert "const pickerlRot=_pkFr.st==='overdue';" in HTML
    assert 'pickerlRot?" · abgelaufen":_pkFr.st===\'toleranz\'?" · Toleranzfrist bis "' in HTML
    # QR-Abzeichen
    assert "window._pickerlFrist(fzScannedItem.pickerl)" in HTML
    # Home-Banner: "abgelaufen" zaehlt nach der Toleranzregel, nicht nach _pickerlStatus
    i = HTML.index("if(pickerFaellig.length>0){")
    block = HTML[i:HTML.index("alerts.push", i)]
    assert "window._pickerlFrist(f.pickerl)" in block
    assert "_pickerlStatus(f.pickerl)==='overdue'" not in block
    assert "in Toleranzfrist" in block
