# -*- coding: utf-8 -*-
"""SQL-Datei 1:1 aus der Datei an die Prod-Datenbank schicken (GF 24.11.2026: kein Abtippen von SQL).

Der Text wird per Datei-Lesen in die Abfrage gelegt (Supabase Management API, POST /v1/projects/<ref>/database/query).
Zugang: Umgebungsvariable SUPABASE_ACCESS_TOKEN (persoenlicher Zugangsschluessel, legt Sebastian selbst an; wird nie
ausgegeben, nie in Dateien geschrieben). Nur Projekt jiggujpruejkaomgxarp.

Saetze: mf (Monatsfreigabe), dispo (Dispo-Planung).
Aufrufe (aus dem Repo-Wurzelverzeichnis):
  python sql/_sql_aus_datei.py <satz> md5
  python sql/_sql_aus_datei.py <satz> probe          -> Probe aus der Datei, Urteil OK nur ohne Abweichung
  python sql/_sql_aus_datei.py <satz> einspielen <md5-entwurf> --ja
        NUR wenn (a) md5 der Entwurfsdatei == angegeben, (b) im Lauf-Protokoll eine Probe mit Urteil OK fuer GENAU diese
        md5 (Entwurf + Probe) steht, (c) die Probe den Entwurf woertlich enthaelt.
  python sql/_sql_aus_datei.py <satz> nachmessung    -> gleiche Pruefschritte gegen das eingespielte Modell
Vor jeder Probe/Nachmessung wird die Probe-Datei neu erzeugt und muss inhaltsgleich bleiben (sonst Abbruch).
Jeder Lauf haengt eine Zeile an C:/repos/epk-sql-laeufe.log an (Zeit, Satz, Modus, md5 je Datei, Ergebnis) - ohne Geheimnisse.
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

PROJEKT = "jiggujpruejkaomgxarp"
HIER = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(os.path.dirname(os.path.dirname(HIER)), "epk-sql-laeufe.log")  # ausserhalb des Repos


def _p(n):
    return os.path.join(HIER, n)


SAETZE = {
    "mf": {"entwurf": _p("MONATSFREIGABE_v1_ENTWURF.sql"), "probe": _p("MONATSFREIGABE_v1_PROBE.sql"),
           "ruecknahme": _p("MONATSFREIGABE_v1_RUECKNAHME.sql"), "nachmessung": _p("MONATSFREIGABE_v1_NACHMESSUNG.sql"),
           "bauer": _p("_mf_probe_bauen.py")},
    "dispo": {"entwurf": _p("DISPO_PLANUNG_v1_ENTWURF.sql"), "probe": _p("DISPO_PLANUNG_v1_PROBE.sql"),
              "ruecknahme": _p("DISPO_PLANUNG_v1_RUECKNAHME.sql"), "nachmessung": _p("DISPO_PLANUNG_v1_NACHMESSUNG.sql"),
              "bauer": _p("_dispo_planung_probe_bauen.py")},
}
DATEI_KEYS = ("entwurf", "probe", "ruecknahme", "nachmessung")

# Dispo: erwartete Teile des Ergebnistexts (laut Kopf von DISPO_PLANUNG_v1_PROBE.sql)
DISPO_SOLL = [
    r"import \[[^\]]+\] termin=2099-02-02 planung=2099-03-03/07:15/03:00/\S+ aktualisiert=1",
    r"monteur \[[^\]]+\] planen=42501 leeren=42501 normal=OK\(1\) unveraendert=OK\(1\)",
    r"techniker \[[^\]]+\] planen=42501 leeren=42501 normal=OK\(1\) unveraendert=OK\(1\)",
    r"projektleiter \[[^\]]+\] planen=OK\(1\) leeren=OK\(1\) normal=OK\(1\) unveraendert=OK\(1\)",
    r"buero \[[^\]]+\] planen=OK\(1\) leeren=OK\(1\) normal=OK\(1\) unveraendert=OK\(1\)",
    r"admin \[[^\]]+\] planen=OK\(1\) leeren=OK\(1\) normal=OK\(1\) unveraendert=OK\(1\)",
    r"nojwt[^|]*planen=OK\(1\)",
    r"service_role[^|]*planen=OK\(1\)",
]


def roh(p):
    with open(p, "rb") as f:
        return f.read()


def alle_md5(satz):
    d = SAETZE[satz]
    return {k: hashlib.md5(roh(d[k])).hexdigest() for k in DATEI_KEYS if os.path.exists(d[k])}


def protokoll(satz, modus, m, ergebnis):
    zeile = "%s\t%s\t%s\t%s\t%s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), satz, modus,
                                       " ".join("%s=%s" % (k, m[k]) for k in sorted(m)), ergebnis.replace("\n", " ")[:900])
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


def neu_erzeugt_gleich(satz):
    d = SAETZE[satz]
    vorher = {k: roh(d[k]) for k in ("probe", "nachmessung") if os.path.exists(d[k])}
    r = subprocess.run([sys.executable, d["bauer"]], capture_output=True, text=True)
    try:
        if r.returncode != 0:
            raise SystemExit("ABBRUCH: Probe-Bauer fehlgeschlagen: " + r.stderr[-300:])
        for k, b in vorher.items():
            if roh(d[k]).replace(b"\r\n", b"\n") != b.replace(b"\r\n", b"\n"):
                raise SystemExit("ABBRUCH: %s passt nicht zum Bauer (Datei geaendert?) - neu erzeugen, committen, Probe neu." % k)
    finally:
        for k, b in vorher.items():  # Original-Bytes zurueck (md5 und Arbeitsbaum bleiben unveraendert)
            with open(d[k], "wb") as f:
                f.write(b)


def entwurf_in_probe(satz):
    d = SAETZE[satz]
    ent = roh(d["entwurf"]).replace(b"\r\n", b"\n")
    if satz == "dispo":  # die Probe bettet den ausfuehrbaren Teil ab dem ersten ALTER TABLE ein
        ent = ent[ent.index(b"ALTER TABLE public.arbeitsscheine\n"):].rstrip() + b"\n"
    return ent in roh(d["probe"]).replace(b"\r\n", b"\n")


def urteil(satz, text):
    if satz == "mf":
        m = re.search(r"PROBE_ERGEBNIS ok=(\d+) fail=(\d+)[^\"\\]*", text)
        return ("OK" if m and m.group(2) == "0" else "ROT"), (m.group(0) if m else text[:400])
    m = re.search(r"PROBE-ERGEBNIS([^\"\\]*)", text)
    if not m:
        return "ROT", text[:400]
    fehlt = [s for s in DISPO_SOLL if not re.search(s, m.group(1))]
    return ("OK" if not fehlt else "ROT"), m.group(0) + ("" if not fehlt else "  || FEHLT: " + " ; ".join(fehlt))


def lauf_pruefen(satz, modus):
    neu_erzeugt_gleich(satz)
    if modus == "probe" and not entwurf_in_probe(satz):
        raise SystemExit("ABBRUCH: Probe-Datei enthaelt den Entwurf nicht woertlich.")
    m = alle_md5(satz)
    st, text = senden(roh(SAETZE[satz][modus]))
    u, kern = urteil(satz, text)
    protokoll(satz, modus, m, "%s %s" % (u, kern))
    print("md5:", json.dumps(m))
    print("HTTP", st, "->", kern)
    print("URTEIL:", u)
    return 0 if u == "OK" else 1


def lauf_einspielen(satz, soll, ja):
    m = alle_md5(satz)
    if not ja:
        raise SystemExit("ABBRUCH: --ja fehlt (Einspielen nur mit Sebastians Ja).")
    if m["entwurf"] != soll:
        raise SystemExit("ABBRUCH: md5 Entwurf %s != angegeben %s - Datei geaendert, Probe neu." % (m["entwurf"], soll))
    if not entwurf_in_probe(satz):
        raise SystemExit("ABBRUCH: Probe enthaelt den Entwurf nicht woertlich.")
    ok = False
    if os.path.exists(LOG):
        for z in io.open(LOG, encoding="utf-8"):
            t = z.rstrip("\n").split("\t")
            if len(t) >= 5 and t[1] == satz and t[2] == "probe" and t[4].startswith("OK") \
               and ("entwurf=" + m["entwurf"]) in t[3] and ("probe=" + m["probe"]) in t[3]:
                ok = True
    if not ok:
        raise SystemExit("ABBRUCH: keine Probe mit Urteil OK fuer genau diese md5 (Entwurf+Probe) im Protokoll - zuerst 'probe'.")
    st, text = senden(roh(SAETZE[satz]["entwurf"]))
    u = "OK" if 200 <= st < 300 else "ROT"
    protokoll(satz, "einspielen", m, "%s HTTP %s %s" % (u, st, text[:300]))
    print("md5:", json.dumps(m))
    print("HTTP", st, text[:600])
    print("URTEIL:", u, "- jetzt: python sql/_sql_aus_datei.py %s nachmessung" % satz)
    return 0 if u == "OK" else 1


def main(argv):
    if len(argv) < 3 or argv[1] not in SAETZE or argv[2] not in ("md5", "probe", "einspielen", "nachmessung"):
        print(__doc__)
        return 2
    satz, modus = argv[1], argv[2]
    if modus == "md5":
        print(json.dumps(alle_md5(satz), indent=1))
        return 0
    if modus == "einspielen":
        if len(argv) < 4:
            raise SystemExit("ABBRUCH: md5 des Entwurfs angeben.")
        return lauf_einspielen(satz, argv[3], "--ja" in argv)
    return lauf_pruefen(satz, modus)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
