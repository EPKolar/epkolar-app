# -*- coding: utf-8 -*-
"""Kommt an, was gepusht wurde? - die Schicht zwischen main und dem Geraet.

🔴 WARUM ES DIESES WERKZEUG GIBT.
Am 29.09.2026 habe ich drei Kuren am Hell-/Dunkel-Schalter gebaut, jede mit
gruenen Toren, jede gepusht. Sebastian meldete dreimal "geht nicht". Ich habe
danach gesucht in: Standalone-Modus, manifest.json, der Statusleisten-Marke,
dem Abmeldepfad, dem Service Worker, dem dynamischen Stilblock, den
CSS-Variablen, echten Fingertippen und schliesslich in WebKit auf einem
iPhone-Profil. Sechs Messungen, zwei Engines.

Die Ursache war keine davon: **GitHub Pages war abgeschaltet.**

    repos/.../epkolar-app  ->  has_pages: false
    https://<host>/index.html  ->  HTTP 404
    letzter Pages-Bau 08:36 UTC, mein Push 13:29 UTC ohne Bau

Eine installierte PWA laeuft aus ihrem Zwischenspeicher weiter: die App
startet, Supabase antwortet, alles fuehlt sich normal an - nur jede
Aktualisierung scheitert STILL. Keine der drei Kuren konnte ihn je erreichen.

ZWISCHEN `git push` UND DEM GERAET LIEGEN DREI SCHICHTEN, und jede kann
schweigend eine Version zurueckhaengen:

    1. der Bau der Auslieferung   (Pages baut, oder eben nicht)
    2. die Auslieferung selbst    (200 oder 404)
    3. der Service Worker         (holt beim START, nicht beim Anmelden)

Dieses Werkzeug misst die ersten beiden. Die dritte kann nur das Geraet
beantworten - deshalb nennt der Bericht am Ende, wo der Nutzer nachsieht.

🔴 ES GEHOERT NICHT IN DIE TORKETTE. Die misst den Arbeitsbaum und muss ohne
Netz laufen. Dieses hier gehoert NACH den Push - und die Antwort auf
"ist es beim Nutzer?" ist nicht "die Tore waren gruen".
"""
import io
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)

URL = os.environ.get("EPK_LIVE_URL",
                     "https://epkolar.github.io/epkolar-app/index.html")

VERSION = re.compile(r'const APP_VERSION\s*=\s*"(\d+\.\d+\.\d+)')


def lokal():
    t = io.open(os.path.join(WURZEL, "index.html"),
                encoding="utf-8", newline="").read()
    m = VERSION.search(t)
    return m.group(1) if m else None


def kopf():
    """Die Version im letzten Commit auf origin/main - nicht im Arbeitsbaum."""
    try:
        r = subprocess.run(["git", "show", "origin/main:index.html"],
                           cwd=WURZEL, capture_output=True, timeout=120)
        t = r.stdout.decode("utf-8", "replace")
        m = VERSION.search(t)
        return m.group(1) if m else None
    except Exception:
        return None


def live(url):
    # 🔴 Der Zeitstempel umgeht jeden Zwischenspeicher. Ohne ihn misst man
    #    womoeglich eine Kopie und nicht die Auslieferung.
    voll = url + ("&" if "?" in url else "?") + "_v=%d" % (os.getpid() * 7919)
    bitte = urllib.request.Request(voll, headers={
        "Cache-Control": "no-cache", "Pragma": "no-cache",
        "User-Agent": "epkolar-auslieferungspruefung"})
    try:
        with urllib.request.urlopen(bitte, timeout=30) as a:
            roh = a.read().decode("utf-8", "replace")
            m = VERSION.search(roh)
            return {"status": a.status, "version": m.group(1) if m else None,
                    "bytes": len(roh)}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "version": None, "bytes": 0,
                "fehler": "HTTP %d" % e.code}
    except Exception as e:
        return {"status": None, "version": None, "bytes": 0,
                "fehler": str(e)[:120]}


def main(argv):
    url = argv[0] if argv else URL
    lv, kv = lokal(), kopf()
    a = live(url)
    print("Arbeitsbaum        v%s" % lv)
    print("origin/main        v%s" % (kv or "?"))
    print("ausgeliefert       %s%s"
          % ("v" + a["version"] if a["version"] else "-",
             "   (HTTP %s%s)" % (a["status"],
                                 ", " + a["fehler"] if a.get("fehler") else "")))
    print("   %s" % url)

    ziel = os.path.join(WURZEL, "docs", "befunde", "AUSLIEFERUNG.json")
    io.open(ziel, "w", encoding="utf-8", newline="").write(
        json.dumps({"url": url, "arbeitsbaum": lv, "origin_main": kv,
                    "live": a}, ensure_ascii=False, indent=1))

    if a["status"] != 200:
        print("\n\U0001F534 DIE APP WIRD NICHT AUSGELIEFERT (HTTP %s)."
              % a["status"])
        print("   Eine installierte PWA laeuft dann aus ihrem Zwischenspeicher")
        print("   weiter und holt KEINE neue Fassung - still, ohne Fehlermeldung.")
        print("   Zu pruefen: Settings -> Pages (Quelle gesetzt?), und ob das")
        print("   Repository privat ist - Pages fuer private Repos braucht")
        print("   einen kostenpflichtigen Plan.")
        return 2
    if kv and a["version"] != kv:
        print("\n\U0001F534 AUSGELIEFERT IST v%s, auf origin/main steht v%s."
              % (a["version"], kv))
        print("   Der Bau haengt zurueck oder ist nicht gelaufen.")
        return 1
    print("\n\U0001F7E2 Ausgeliefert wird, was auf origin/main steht.")
    print("   Beim Nutzer kommt es erst beim naechsten START der App an -")
    print("   Ab- und Anmelden laedt die Seite NICHT neu. Er sieht die Zahl")
    print("   unter Einstellungen -> App-Info -> Version.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
