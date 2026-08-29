# -*- coding: utf-8 -*-
"""
Tab-Durchlauf: oeffnet jede Hauptansicht und meldet Abstuerze.

WOFUER DAS DA IST
-----------------
Am 25.08.2026 stand der Tab "Monatsabrechnung" monatelang kaputt live: die
Callsite reichte die nackte Bindung `approvals` durch (der State heisst
`absApprovals`). Ein Klick darauf riss die GANZE App auf die Fehlerseite.

Kein bestehendes Gate konnte das sehen, und das ist kein Zufall:

  node_check.py   parst die Datei, fuehrt sie nicht aus
  _bracket_check  zaehlt Klammern
  pytest          statisch (String-/Regex-Asserts ueber den Quelltext)
  Browser-Check   laedt nur die Startseite

Der Ausdruck wird wegen des &&-Kurzschlusses NUR ausgewertet, wenn genau dieser
Tab aktiv ist. Und schlimmer: ein pytest-Test hatte den kaputten Wortlaut sogar
WORTGLEICH festgeschrieben und war gruen dabei.

Dieses Skript ist das einzige Gate, das diese Fehlerklasse ueberhaupt sehen kann.
Es kostet rund zwei Minuten.

VORAUSSETZUNG
-------------
    pip install playwright
    playwright install chromium

BENUTZUNG
---------
    python scripts/tab_sweep.py                     # gegen die Live-App
    python scripts/tab_sweep.py http://127.0.0.1:8899/index.html   # lokal

Exit 0 = alle Ansichten sauber. Exit 1 = mindestens eine Ansicht ist kaputt.

HINWEIS ZUR HERKUNFT
--------------------
Die Abfolge war zunaechst eine Transkription des Laufs, der am 25.08.2026 gegen
v3.9.874 live durchgefuehrt wurde (alle 18 Ansichten ok). Das SKRIPT selbst lief
drei Handoffs lang nie, weil im Arbeitsklon kein Playwright installiert war.

Am 29.08.2026 ist es zum ersten Mal echt gelaufen - gegen v3.9.896 live, wieder
alle 18 Ansichten sauber. Der erste Lauf starb allerdings an der ERSTEN Ansicht,
und zwar an sich selbst: siehe die stdout-Umstellung unten. Der Fehler sass
nicht im Messen, sondern im Berichten. Merksatz fuer das naechste Werkzeug:
die Transkription eines Laufs ist kein ausgefuehrter Lauf.
"""
import sys

# ERSTER LAUF, 29.08.2026 - UND DAS GATE STARB AN SICH SELBST, NICHT AN DER APP.
# Die Tab-Namen der App tragen Emoji ("\U0001f3e0 Home"). Windows-stdout ist
# cp1252, und `print("  %-20s ok" % name)` warf beim ERSTEN Tab
# UnicodeEncodeError. Das Skript ist also nie ueber Ansicht 1 hinausgekommen -
# ein Gate, das abstuerzt, bevor es etwas melden kann, ist kein Gate.
#
# Bemerkenswert: der Fehler steckte nicht im Messen, sondern im BERICHTEN. Genau
# deshalb steht in der Kopfnotiz "beim ersten Lauf mit kritischem Blick
# draufschauen" - die Transkription eines Laufs ist eben kein ausgefuehrter Lauf.
for _strom in (sys.stdout, sys.stderr):
    try:
        _strom.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

LIVE = "https://epkolar.github.io/epkolar-app/index.html"

# Test-Sitzung ohne echte Zugangsdaten: die App braucht nur einen plausibel
# geformten Token und einen User im localStorage. Die Daten-Requests laufen
# danach in 401 - das ist erwartet und stoert den Test nicht, weil er auf
# Abstuerze prueft, nicht auf Inhalte.
INIT = """
try{
  var b=function(s){return btoa(s).replace(/=+$/,'');};
  var jwt=b(JSON.stringify({alg:"HS256",typ:"JWT"}))+"."+
          b(JSON.stringify({sub:"1",role:"authenticated",
                            exp:Math.floor(Date.now()/1000)+86400}))+".sig";
  localStorage.setItem('epkolar_auth',JSON.stringify({at:jwt,rt:"r",exp:Date.now()+86400000}));
  localStorage.setItem('epkolar_user',JSON.stringify({
    id:"1",username:"admin",name:"Sweep",role:"admin",
    rolle:"Geschaeftsfuehrer",permissions:[],perms_override:{}}));
}catch(e){}
"""

# Rauschen des Testzugangs - keine echten Befunde.
IGNORIEREN = ("401", "403", "Failed to load", "net::", "supabase",
              "fetch", "Unauthorized", "workers-load")


def main(url=LIVE):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright fehlt.  pip install playwright && playwright install chromium")
        return 2

    fehler = []
    kaputt = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 390, "height": 844},
                                  has_touch=True, is_mobile=True)
        ctx.add_init_script(INIT)
        seite = ctx.new_page()
        seite.on("pageerror", lambda e: fehler.append("pageerror: " + str(e)[:140]))

        def konsole(m):
            # In Playwright-fuer-Python sind .type/.text je nach Version Eigenschaft
            # ODER Methode. Trifft man die falsche Variante, vergleicht man gegen ein
            # Funktionsobjekt - der Vergleich ist dann IMMER falsch und das Skript
            # meldet faelschlich "sauber". Genau die Sorte stiller Fehlgruen, die
            # dieses Gate eigentlich verhindern soll. Deshalb beide Formen bedienen.
            art = m.type() if callable(getattr(m, "type", None)) else getattr(m, "type", "")
            if art != "error":
                return
            t = m.text() if callable(getattr(m, "text", None)) else getattr(m, "text", "")
            t = str(t)
            if not any(x.lower() in t.lower() for x in IGNORIEREN):
                fehler.append("console: " + t[:130])
        seite.on("console", konsole)

        seite.goto(url, wait_until="domcontentloaded")
        seite.wait_for_timeout(6000)

        version = seite.evaluate("() => typeof APP_VERSION!=='undefined' ? APP_VERSION : '?'")
        print("Version:", version)

        namen = seite.evaluate("""() => {
            const t = e => (e.textContent||'').trim().replace(/\\s+/g,' ');
            const bar = [...document.querySelectorAll('.tab-bar')]
              .find(b => t(b).indexOf('Home')>=0 && t(b).indexOf('Projekte')>=0);
            return bar ? [...bar.querySelectorAll('button')].map(b => t(b).slice(0,18)) : [];
        }""")
        if not namen:
            print("FEHLER: keine Tab-Leiste gefunden - laedt die App ueberhaupt?")
            browser.close()
            return 1

        for i, name in enumerate(namen):
            seite.evaluate("""(idx) => {
                const t = e => (e.textContent||'').trim().replace(/\\s+/g,' ');
                const bar = [...document.querySelectorAll('.tab-bar')]
                  .find(b => t(b).indexOf('Home')>=0 && t(b).indexOf('Projekte')>=0);
                if(!bar) return;
                const bs = [...bar.querySelectorAll('button')];
                if(bs[idx]) bs[idx].click();
            }""", i)
            seite.wait_for_timeout(1100)

            zustand = seite.evaluate("""() => {
                const crash = document.body.innerText.indexOf('App-Fehler') >= 0;
                return {
                  crash: crash,
                  meldung: crash ? document.body.innerText.split('\\n').slice(0,3).join(' | ').slice(0,120) : null,
                  mainPad: !!document.querySelector('.main-pad')
                };
            }""")

            if zustand["crash"]:
                print("  %-20s KAPUTT -> %s" % (name, zustand["meldung"]))
                kaputt.append(name)
                seite.reload(wait_until="domcontentloaded")
                seite.wait_for_timeout(5000)
            elif not zustand["mainPad"]:
                print("  %-20s kein Inhaltsbereich" % name)
                kaputt.append(name)
            else:
                print("  %-20s ok" % name)

        browser.close()

    print()
    if kaputt:
        print("KAPUTT: " + ", ".join(kaputt))
    if fehler:
        print("JS-Fehler:")
        for f in fehler[:10]:
            print("   " + f)
    if not kaputt and not fehler:
        print("Alle %d Ansichten sauber." % len(namen))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else LIVE))
