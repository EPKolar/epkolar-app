# -*- coding: utf-8 -*-
"""SQL-Datei 1:1 aus der Datei an die Prod-Datenbank schicken (GF 24.11.2026: kein Abtippen von SQL).

Der Text wird per Datei-Lesen in die Abfrage gelegt (Supabase Management API, POST /v1/projects/<ref>/database/query).
Zugang: Umgebungsvariable SUPABASE_ACCESS_TOKEN (persoenlicher Zugangsschluessel, legt Sebastian selbst an; wird nie
ausgegeben, nie in Dateien geschrieben). Nur Projekt jiggujpruejkaomgxarp.

Aufrufe (Python 3, aus dem Repo-Wurzelverzeichnis):
  python sql/_sql_aus_datei.py probe        -> MONATSFREIGABE_v1_PROBE.sql, Erwartung "PROBE_ERGEBNIS ok=N fail=0"
  python sql/_sql_aus_datei.py einspielen <md5-entwurf> --ja
                                            -> MONATSFREIGABE_v1_ENTWURF.sql, NUR wenn
                                               (a) md5 der Datei == angegebener md5,
                                               (b) im Lauf-Protokoll eine Probe mit fail=0 fuer GENAU diese md5-Kombination steht,
                                               (c) die Probe-Datei den Entwurf woertlich enthaelt.
  python sql/_sql_aus_datei.py nachmessung  -> MONATSFREIGABE_v1_NACHMESSUNG.sql, Erwartung fail=0
Jeder Lauf haengt eine Zeile an C:/repos/epk-mf-laeufe.log an (Zeit, Modus, md5 je Datei, Ergebnis) - ohne Geheimnisse.
"""
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

PROJEKT = "jiggujpruejkaomgxarp"
HIER = os.path.dirname(os.path.abspath(__file__))
DATEIEN = {
    "entwurf": os.path.join(HIER, "MONATSFREIGABE_v1_ENTWURF.sql"),
    "probe": os.path.join(HIER, "MONATSFREIGABE_v1_PROBE.sql"),
    "ruecknahme": os.path.join(HIER, "MONATSFREIGABE_v1_RUECKNAHME.sql"),
    "nachmessung": os.path.join(HIER, "MONATSFREIGABE_v1_NACHMESSUNG.sql"),
}
LOG = os.path.join(os.path.dirname(os.path.dirname(HIER)), "epk-mf-laeufe.log")  # ausserhalb des Repos (Arbeitsbaum bleibt sauber)


def roh(p):
    with open(p, "rb") as f:
        return f.read()


def md5(p):
    return hashlib.md5(roh(p)).hexdigest()


def alle_md5():
    return {k: md5(v) for k, v in DATEIEN.items() if os.path.exists(v)}


def protokoll(modus, m, ergebnis):
    zeile = "%s\t%s\t%s\t%s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), modus,
                                   " ".join("%s=%s" % (k, m[k]) for k in sorted(m)), ergebnis.replace("\n", " ")[:600])
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(zeile)


def senden(sql_bytes):
    token = os.environ.get("SUPABASE_ACCESS_TOKEN", "")
    if not token:
        raise SystemExit("ABBRUCH: SUPABASE_ACCESS_TOKEN fehlt in der Umgebung - nichts gesendet.")
    body = json.dumps({"query": sql_bytes.decode("utf-8")}).encode("utf-8")
    req = urllib.request.Request("https://api.supabase.com/v1/projects/%s/database/query" % PROJEKT, data=body, method="POST",
                                 headers={"Authorization": "Bearer " + token, "Content-Type": "application/json",
                                          "User-Agent": "epk-sql-aus-datei"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def probe_ergebnis(text):
    m = re.search(r"PROBE_ERGEBNIS ok=(\d+) fail=(\d+)", text)
    return (int(m.group(1)), int(m.group(2))) if m else None


def lauf_probe(modus):
    m = alle_md5()
    datei = DATEIEN[modus]
    if modus == "probe":
        ent = roh(DATEIEN["entwurf"]).replace(b"\r\n", b"\n")
        if ent not in roh(datei).replace(b"\r\n", b"\n"):
            raise SystemExit("ABBRUCH: Probe-Datei enthaelt den Entwurf nicht woertlich - Probe neu erzeugen (sql/_mf_probe_bauen.py).")
    st, text = senden(roh(datei))
    e = probe_ergebnis(text)
    urteil = "OK" if e and e[1] == 0 else "ROT"
    protokoll(modus, m, "%s %s" % (urteil, (re.search(r"PROBE_ERGEBNIS[^\"\\]*", text) or [text[:300]])[0]))
    print("md5:", json.dumps(m))
    print("HTTP", st, "->", (re.search(r"PROBE_ERGEBNIS[^\"\\]*", text) or [text[:600]])[0])
    print("URTEIL:", urteil)
    return 0 if urteil == "OK" else 1


def lauf_einspielen(soll, ja):
    m = alle_md5()
    if not ja:
        raise SystemExit("ABBRUCH: --ja fehlt (Einspielen nur mit Sebastians Ja).")
    if m["entwurf"] != soll:
        raise SystemExit("ABBRUCH: md5 Entwurf %s != angegeben %s - Datei geaendert, Probe neu." % (m["entwurf"], soll))
    ok = False
    if os.path.exists(LOG):
        for z in io.open(LOG, encoding="utf-8"):
            t = z.rstrip("\n").split("\t")
            if len(t) >= 4 and t[1] == "probe" and t[3].startswith("OK") \
               and ("entwurf=" + m["entwurf"]) in t[2] and ("probe=" + m["probe"]) in t[2]:
                ok = True
    if not ok:
        raise SystemExit("ABBRUCH: keine gruene Probe (fail=0) fuer genau diese md5 (Entwurf+Probe) im Protokoll - zuerst 'probe'.")
    st, text = senden(roh(DATEIEN["entwurf"]))
    urteil = "OK" if 200 <= st < 300 else "ROT"
    protokoll("einspielen", m, "%s HTTP %s %s" % (urteil, st, text[:300]))
    print("md5:", json.dumps(m))
    print("HTTP", st, text[:600])
    print("URTEIL:", urteil, "- jetzt: python sql/_sql_aus_datei.py nachmessung")
    return 0 if urteil == "OK" else 1


def main(argv):
    if len(argv) < 2 or argv[1] not in ("probe", "einspielen", "nachmessung", "md5"):
        print(__doc__); return 2
    if argv[1] == "md5":
        print(json.dumps(alle_md5(), indent=1)); return 0
    if argv[1] == "einspielen":
        if len(argv) < 3:
            raise SystemExit("ABBRUCH: md5 des Entwurfs angeben.")
        return lauf_einspielen(argv[2], "--ja" in argv)
    return lauf_probe(argv[1])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
