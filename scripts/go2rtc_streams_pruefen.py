# -*- coding: utf-8 -*-
"""Abnahme der go2rtc-Streams auf der QNAP (EPKolar Kamera-Gateway, 21.11.2026).

Aufruf AUF DER QNAP (oder von einem Rechner, der go2rtc :1984 erreicht):
    python3 go2rtc_streams_pruefen.py [http://<QNAP-LAN-IP>:1984] [--fenster 30] [--takt 3] [--nur-streams]
    (Standard: http://$QNAP_LAN_IP:1984, ohne QNAP_LAN_IP http://127.0.0.1:1984)
Exit 0 nur, wenn die go2rtc-Anmeldung wirkt (siehe unten; bei localhost nur mit --nur-streams uebersprungen) UND
JEDER erwartete Stream innerhalb des Fensters mindestens einmal
  (a) Bilddaten geliefert hat UND
  (b) in /api/streams waehrenddessen einen VERBUNDENEN Erzeuger (producer) hatte.
Exit 1 sonst (Liste der fehlenden Streams), Exit 2 bei Bedienfehler.

Warum anstossen: go2rtc verbindet eine Quelle nur, solange ein Zuschauer da ist (Bedarfsbetrieb). Ohne Zuschauer
steht in /api/streams nur die konfigurierte Quelle ({"url": ...}) - das beweist nichts. Darum oeffnet das Skript je
Stream kurz einen Zuschauer, liest die ersten Bytes, fragt BEI OFFENER Verbindung /api/streams ab und schliesst wieder:
  mjpeg  (Mobotix) -> /api/stream.mjpeg?src=<s>   (Durchreichen, keine Umwandlung)
  h264   (UniFi G3) -> /api/stream.mp4?src=<s>    (Umverpacken, keine Umwandlung - NICHT frame.jpeg/stream.mjpeg,
                                                  die bei H.264 ffmpeg auf der ARM-CPU starten wuerden)
"Verbunden" = ein producer-Eintrag mit mehr als nur "url" (go2rtc fuellt dann medias/receivers/remote_addr ...).
Wackelige Kameras: Fehlversuche werden im Takt wiederholt, bis das Fenster abgelaufen ist.
Ausgabe nur Streamnamen und Zustand - NIE die producer-URL (sie kann Zugangsdaten enthalten).

API-Anmeldung (go2rtc api username/password): aus der Umgebung GO2RTC_USER / GO2RTC_PASS (nie als Argument,
nie ausgegeben). go2rtc laesst localhost OHNE Anmeldung durch - mit der LAN-Adresse (http://<QNAP-LAN-IP>:1984)
prueft das Skript zusaetzlich, dass die Anmeldung wirkt: ohne Anmeldung UND mit den woertlichen Platzhaltern
"${GO2RTC_USER}:${GO2RTC_PASS}" (fehlende kam.env-Zeile) muss /api/streams 401 liefern, MIT dem Paar 200.
"""
import base64
import os
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# Erwartete Streams = tools/kamera-proxy-auth/qnap/go2rtc.yaml (Riegel: tests/test_kamera_mobotix_v1090.py)
G3 = ("hochregal01", "verkauf02", "elektrolager03", "cam39")
MOBOTIX = ("hof01", "hochregal03", "hochregal02", "elektrolager01", "elektrolager02")
ERWARTET = tuple((s, "h264") for s in G3) + tuple((s, "mjpeg") for s in MOBOTIX)
STANDARD_URL = "http://127.0.0.1:1984"


def standard_url():
    """LAN-Adresse aus QNAP_LAN_IP (dort wirkt die go2rtc-Anmeldung), sonst localhost."""
    ip = os.environ.get("QNAP_LAN_IP", "").strip()
    return "http://%s:1984" % ip if ip else STANDARD_URL
PFAD = {"mjpeg": "/api/stream.mjpeg", "h264": "/api/stream.mp4"}


def _oeffne_echt(url, timeout, kopf=None):
    h = {"User-Agent": "epk-go2rtc-pruefen"}
    h.update(kopf or {})
    return urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout)


def basic_kopf(user, passwort):
    if not user and not passwort:
        return {}
    return {"Authorization": "Basic " + base64.b64encode((user + ":" + passwort).encode("utf-8")).decode("ascii")}


def ist_localhost(basis):
    host = (urllib.parse.urlsplit(basis).hostname or "").lower()
    return host == "localhost" or host.startswith("127.") or host == "::1"


def anmeldung_pruefen(basis, kopf, oeffne=_oeffne_echt, timeout=6.0):
    """Rueckgabe Liste von Befunden (leer = Anmeldung wirkt). Nur sinnvoll fuer Nicht-localhost.
    Ohne Anmeldung und mit woertlichen Platzhaltern -> 401; mit GO2RTC_USER/GO2RTC_PASS -> 200."""
    b = []
    if not kopf:
        b.append("GO2RTC_USER/GO2RTC_PASS nicht gesetzt - Anmeldung mit dem echten Paar nicht pruefbar")
    else:
        try:
            a = oeffne(basis.rstrip("/") + "/api/streams", timeout, kopf)
            a.close()
        except urllib.error.HTTPError as e:
            b.append("go2rtc-API mit GO2RTC_USER/GO2RTC_PASS: HTTP %d statt 200" % e.code)
        except Exception as e:  # noqa: BLE001
            b.append("go2rtc-API mit Anmeldung nicht erreichbar: %s" % type(e).__name__)
    for art, kopf in (("ohne Anmeldung", {}), ("mit woertlichen Platzhaltern", basic_kopf("${GO2RTC_USER}", "${GO2RTC_PASS}"))):
        try:
            a = oeffne(basis.rstrip("/") + "/api/streams", timeout, kopf)
            a.close()
            b.append("go2rtc-API antwortet " + art + " - Anmeldung wirkt NICHT")
        except urllib.error.HTTPError as e:
            if e.code != 401:
                b.append("go2rtc-API %s: HTTP %d statt 401" % (art, e.code))
        except Exception as e:  # noqa: BLE001
            b.append("go2rtc-API %s nicht erreichbar: %s" % (art, type(e).__name__))
    return b


def verbunden(eintrag):
    """Anzahl verbundener Erzeuger in einem /api/streams-Eintrag eines Streams."""
    if not isinstance(eintrag, dict):
        return 0
    n = 0
    for p in eintrag.get("producers") or []:
        if isinstance(p, dict) and any(k != "url" for k in p):
            n += 1
    return n


def _stream_eintrag(daten, name):
    if isinstance(daten, dict) and name in daten:
        return daten[name]
    if isinstance(daten, dict) and "producers" in daten:   # Antwort von /api/streams?src=<name>
        return daten
    return None


def einmal_pruefen(basis, name, typ, oeffne, timeout, kopf=None):
    """Ein Versuch fuer einen Stream. Rueckgabe (ok, grund)."""
    q = urllib.parse.urlencode({"src": name})
    try:
        zuschauer = oeffne(basis + PFAD[typ] + "?" + q, timeout, kopf)
    except Exception as e:  # noqa: BLE001 - jeder Fehler = dieser Versuch gescheitert
        return False, "anstossen: " + type(e).__name__
    try:
        try:
            erste = zuschauer.read(1024)
        except Exception as e:  # noqa: BLE001
            return False, "lesen: " + type(e).__name__
        if not erste:
            return False, "keine Bilddaten"
        if typ == "mjpeg" and b"\xff\xd8" not in erste and b"--" not in erste:
            return False, "keine MJPEG-Daten"
        try:
            antwort = oeffne(basis + "/api/streams?" + q, timeout, kopf)
            try:
                daten = json.loads(antwort.read().decode("utf-8"))
            finally:
                antwort.close()
        except Exception as e:  # noqa: BLE001
            return False, "api/streams: " + type(e).__name__
        n = verbunden(_stream_eintrag(daten, name))
        if n < 1:
            return False, "kein verbundener producer"
        return True, "producer=%d" % n
    finally:
        try:
            zuschauer.close()
        except Exception:  # noqa: BLE001
            pass


def pruefen(basis, erwartet=ERWARTET, fenster=30.0, takt=3.0, oeffne=_oeffne_echt, schlafen=time.sleep,
            uhr=time.monotonic, timeout=6.0, ausgabe=print, kopf=None):
    """Wiederholt im Takt, bis alle erwarteten Streams einmal ok waren oder das Fenster ablaeuft.
    Rueckgabe: (alle_ok, {name: grund})."""
    basis = basis.rstrip("/")
    offen = dict(erwartet)
    stand = {}
    ende = uhr() + fenster
    runde = 0
    while True:
        runde += 1
        for name, typ in list(offen.items()):
            ok, grund = einmal_pruefen(basis, name, typ, oeffne, timeout, kopf)
            stand[name] = grund
            if ok:
                del offen[name]
                ausgabe("OK      %-16s %s (Runde %d)" % (name, grund, runde))
        if not offen or uhr() + takt > ende:
            break
        schlafen(takt)
    for name in offen:
        ausgabe("FEHLT   %-16s %s" % (name, stand.get(name, "nicht geprueft")))
    return not offen, stand


def main(argv):
    basis, fenster, takt, nur_streams = standard_url(), 30.0, 3.0, False
    rest = list(argv)
    try:
        while rest:
            a = rest.pop(0)
            if a == "--nur-streams":
                nur_streams = True
            elif a == "--fenster":
                fenster = float(rest.pop(0))
            elif a == "--takt":
                takt = float(rest.pop(0))
            elif a.startswith("http://") or a.startswith("https://"):
                basis = a
            else:
                raise ValueError(a)
    except (ValueError, IndexError):
        print(__doc__)
        return 2
    kopf = basic_kopf(os.environ.get("GO2RTC_USER", ""), os.environ.get("GO2RTC_PASS", ""))
    befunde = []
    if ist_localhost(basis):
        if nur_streams:
            print("HINWEIS localhost + --nur-streams: Anmeldung NICHT geprueft (go2rtc laesst localhost ohne Anmeldung durch)")
        else:
            befunde = ["Anmeldepruefung braucht die LAN-Adresse (localhost umgeht die go2rtc-Anmeldung) - "
                       "http://<QNAP-LAN-IP>:1984 angeben oder bewusst --nur-streams"]
    else:
        befunde = anmeldung_pruefen(basis, kopf)
    for x in befunde:
        print("FEHLER  " + x)
    alle_ok, _ = pruefen(basis, fenster=fenster, takt=takt, kopf=kopf)
    gut = alle_ok and not befunde
    print("ERGEBNIS " + ("OK - alle %d Streams geliefert" % len(ERWARTET) if gut else "FEHLER - siehe FEHLT/FEHLER"))
    return 0 if gut else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
