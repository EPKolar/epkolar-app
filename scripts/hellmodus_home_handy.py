# -*- coding: utf-8 -*-
"""Bleibt HOME dunkel, wenn man am Handy auf hell schaltet?

🔴 WARUM ES DIESES WERKZEUG GIBT. `hellmodus_nach_dem_schalten.py` misst 18
Ansichten und meldet null dunkle. In seiner eigenen Ausgabe steht aber:

    Home                   NICHT gemessen

Im Rohstand liegt der Grund: `{"__fehler": "kein-sichtbarer-knopf"}`. Es
navigiert ueber die sichtbaren Navigationsknoepfe, und bei 390 px ist der fuer
Home keiner. **Die eine Ansicht, auf der der Nutzer landet, ist die einzige,
die nach dem Umschalten nie gemessen wurde.** Eine Null, die den gesuchten
Fall nicht enthaelt, ist keine Entwarnung.

Home braucht auch keine Navigation - dort startet die App. Also: laden,
umschalten, messen, ohne einen Knopf zu suchen.

DREI UNTERSCHIEDE ZU DEN BISHERIGEN MESSUNGEN, jeder einzeln wichtig:

  1. Gemessen wird gegen die AUSGELIEFERTE Datei, nicht gegen den
     Arbeitsbaum. Was der Nutzer sieht, ist das, was auf dem Server liegt.
  2. Das Betriebssystem steht auf DUNKEL (`colorScheme='dark'`). Sebastians
     Handy steht so, und `_systemDark()` fragt auf *light* ab und gibt bei
     jedem anderen Ausgang dunkel zurueck - auch im Fehlerfall.
  3. Gemessen wird NACH dem Umschalten zur Laufzeit, ohne Neuladen. Die
     Farben kommen aus Gettern auf ein Modul-`_dark`; wer den Wert beim
     ersten Rendern in eine Konstante uebernommen hat, behaelt die dunkle
     Farbe, bis sein Bauteil neu gebaut wird.

GEGENPROBE, ohne die die Zahl nichts wert ist: derselbe Lauf mit
`epk_theme='light'` VOR dem Laden. Ist Home dann hell und nach dem
Umschalten dunkel, liegt es am Umschalten. Ist es in beiden Faellen dunkel,
liegt es nicht am Umschalten, sondern an Home.
"""
import io
import json
import os
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = "https://epkolar.github.io/epkolar-app/index.html"

MESS_JS = r"""
() => {
  const raus = {gross: [], modus: null, wurzel: null, koerper: null};
  try { raus.modus = localStorage.getItem('epk_theme'); } catch (e) {}
  // 🔴 DURCHSICHTIG IST NICHT DUNKEL. Der erste Entwurf rechnete die
  // Helligkeit auch fuer rgba(0,0,0,0) aus und bekam 0 - also meldete er
  // JEDE Flaeche ohne eigenen Hintergrund als schwarz. Die Liste war voll
  // mit "dunklen Flaechen 453 %", waehrend der Koerper nachweislich hell
  // war. Das war ein Befund AM MESSGERAET, kein Befund an der App.
  const hell = (f) => {
    const m = /rgba?\(([\d.]+)[, ]+([\d.]+)[, ]+([\d.]+)(?:[, ]+([\d.]+))?/
              .exec(f || '');
    if (!m) return null;
    if (m[4] !== undefined && +m[4] < 0.05) return null;   // durchsichtig
    const r = +m[1], g = +m[2], b = +m[3];
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
  };
  raus.koerper = getComputedStyle(document.body).backgroundColor;
  raus.wurzel = getComputedStyle(document.documentElement).backgroundColor;
  raus.koerperHell = hell(raus.koerper);
  const flaeche = innerWidth * innerHeight;
  document.querySelectorAll('div,section,main,header,aside,nav').forEach(e => {
    const r = e.getBoundingClientRect();
    if (r.width * r.height < flaeche * 0.04) return;
    const s = getComputedStyle(e);
    if (s.visibility === 'hidden' || s.display === 'none') return;
    const h = hell(s.backgroundColor);
    if (h === null || h >= 0.5) return;
    raus.gross.push({tag: e.tagName.toLowerCase(), farbe: s.backgroundColor,
                     helligkeit: h, anteil: (r.width * r.height) / flaeche,
                     text: (e.innerText || '').slice(0, 60)});
  });
  raus.gross.sort((a, b) => b.anteil - a.anteil);
  raus.gross = raus.gross.slice(0, 6);
  return raus;
}
"""

SCHALTER_JS = r"""
() => {
  const treffer = [];
  document.querySelectorAll('button,[role="button"],a,label,select').forEach(e => {
    const t = ((e.innerText || '') + ' ' + (e.getAttribute('aria-label') || '')
               + ' ' + (e.title || '')).trim();
    if (!t) return;
    if (!/hell|dunkel|dark|light|theme|auto|system|☀|☼|🌙/i.test(t)) return;
    const r = e.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) return;
    treffer.push({text: t.slice(0, 50), x: r.x + r.width / 2,
                  y: r.y + r.height / 2});
  });
  return treffer;
}
"""


def lauf(pw, breite, vorgabe, schalten, engine='chromium'):
    """Einen Durchgang fahren. vorgabe=None -> nichts gesetzt."""
    # 🔴 ZWEI ENGINES. Chromium allein sagt ueber ein iPhone wenig:
    # WebKit behandelt prefers-color-scheme, color-scheme und die
    # Darstellung von Bedienelementen anders. Eine Messung in der
    # falschen Engine ist eine Messung an einer anderen
    # Grundgesamtheit.
    b = (pw.webkit if engine == 'webkit' else pw.chromium).launch()
    try:
        ctx = b.new_context(viewport={"width": breite, "height": 844},
                            device_scale_factor=2, is_mobile=True,
                            has_touch=True, color_scheme="dark")
        s = ctx.new_page()
        _nav = {"n": 0}
        s.on("framenavigated",
             lambda f: _nav.__setitem__("n", _nav["n"] + 1))
        # 🔴 Ohne eine gesetzte Rolle landet der Lauf auf der ANMELDEMASKE,
        # und dort gibt es gar keinen Umschalter - der erste Lauf dieses
        # Werkzeugs hat genau das gemessen und "kein Schalter" gemeldet.
        # Das ist eine ortsuebliche Rollen-Saat wie in
        # hellmodus_nach_dem_schalten.py: kein echtes Anmelden, keine
        # Zugangsdaten, nur ein lokaler Eintrag, damit die angemeldete
        # Oberflaeche rendert. Die Daten bleiben leer - gemessen werden
        # FARBEN, nicht Inhalte.
        s.add_init_script(
            "try{var u=JSON.parse(localStorage.getItem('epkolar_user')"
            "||'{}');u.role='admin';u.monteurId='M1';"
            "u.name='Gerhard Steinbichler';u.rolle='Geschaeftsfuehrer';"
            "localStorage.setItem('epkolar_user',JSON.stringify(u));}"
            "catch(e){}")
        s.add_init_script(
            "try{localStorage.removeItem('epk_theme');}catch(e){}"
            + ("try{localStorage.setItem('epk_theme','%s');}catch(e){}"
               % vorgabe if vorgabe else ""))
        s.goto(LIVE, wait_until="domcontentloaded", timeout=90000)
        s.wait_for_timeout(5000)
        getippt = []
        if schalten:
            for _ in range(4):
                t = s.evaluate(SCHALTER_JS)
                if not t:
                    break
                z = t[0]
                # 🔴 TIPPEN, NICHT KLICKEN. Ein echter Finger loest
                # touchstart/touchend UND einen abgeleiteten Klick aus; eine
                # Maus nur den Klick. Gegen das doppelte Feuern sitzt im
                # Schalter eine 350-ms-Sperre - ob die traegt, kann ein
                # Mausklick gar nicht zeigen. Genau dieser Unterschied
                # trennt meinen Pruefstand von Sebastians Handy.
                if schalten == "tippen":
                    s.touchscreen.tap(z["x"], z["y"])
                else:
                    s.mouse.click(z["x"], z["y"])
                s.wait_for_timeout(900)
                # 🔴 In WebKit ist der Ausfuehrungskontext nach dem Tippen
                # einmal ZERSTOERT worden - "most likely because of a
                # navigation". Das ist selbst ein Befund und darf den Lauf
                # nicht abbrechen: abwarten, bis die Seite wieder steht, und
                # vermerken, DASS neu geladen wurde.
                try:
                    s.wait_for_load_state("domcontentloaded", timeout=20000)
                except Exception:
                    pass
                s.wait_for_timeout(1200)
                getippt.append(z["text"])
                if s.evaluate("()=>{try{return localStorage.getItem("
                              "'epk_theme');}catch(e){return null;}}") \
                        == "light":
                    break
        s.wait_for_timeout(1500)
        try:
            m = s.evaluate(MESS_JS)
        except Exception as e:
            s.wait_for_timeout(2500)
            m = s.evaluate(MESS_JS)
            m["__nachgefasst"] = str(e)[:90]
        m["navigationen"] = _nav["n"]
        m["getippt"] = getippt
        return m
    finally:
        b.close()


def main(argv):
    from playwright.sync_api import sync_playwright
    breite = int(argv[0]) if argv else 390
    print("Gemessen gegen die AUSGELIEFERTE Datei, %d px, System auf DUNKEL\n"
          % breite)
    with sync_playwright() as pw:
        a = lauf(pw, breite, None, "tippen")
        b = lauf(pw, breite, "light", False)
        c = lauf(pw, breite, None, "klicken")
        w = lauf(pw, breite, None, "tippen", "webkit")

    def zeile(name, m):
        print("%-24s Modus=%-8s Koerper=%-22s Helligkeit=%s"
              % (name, m.get("modus"), m.get("koerper"),
                 ("%.2f" % m["koerperHell"]) if m.get("koerperHell")
                 is not None else "?"))
        if m.get("getippt"):
            print("   getippt: %s" % " -> ".join(m["getippt"]))
        for g in m.get("gross", []):
            print("   dunkle Flaeche %5.1f %%  %-22s %s"
                  % (g["anteil"] * 100, g["farbe"], g["text"][:40]))

    zeile("A) GETIPPT (Finger)", a)
    print()
    zeile("B) vorgegeben", b)
    print()
    zeile("C) geklickt (Maus)", c)
    print()
    zeile("D) WebKit, getippt", w)

    io.open(os.path.join(WURZEL, "docs", "befunde",
                         "HELLMODUS_HOME_%d.json" % breite),
            "w", encoding="utf-8", newline="").write(
        json.dumps({"breite": breite, "quelle": LIVE,
                    "getippt": a, "vorgegeben": b, "geklickt": c, "webkit": w},
                   ensure_ascii=False, indent=1))
    print("\ngeschrieben: docs/befunde/HELLMODUS_HOME_%d.json" % breite)

    da = len(a.get("gross", []))
    db = len(b.get("gross", []))
    print("\nDunkle Grossflaechen: umgeschaltet %d, vorgegeben %d" % (da, db))
    if a.get("modus") != "light":
        print("\U0001F534 Der Schalter hat 'light' NICHT erreicht (Modus: %r)."
              " Das ist der Befund." % a.get("modus"))
        return 1
    if da > db:
        print("\U0001F534 Home bleibt NACH DEM UMSCHALTEN dunkel - beim "
              "Vorgeben nicht. Es liegt am Umschalten.")
        return 1
    if da and db:
        print("\U0001F534 Home ist in BEIDEN Faellen dunkel - es liegt NICHT "
              "am Umschalten, sondern an Home selbst.")
        return 1
    print("\U0001F7E2 Home wird hell, umgeschaltet wie vorgegeben.")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
