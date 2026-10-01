# -*- coding: utf-8 -*-
"""Was passiert beim Umschalten, wenn der Speicher NICHT schreiben kann?

🔴 DER VERDACHT, und er passt auf Sebastians Meldung Wort fuer Wort:
"der ganze Bildschirm bleibt dunkel, egal wie oft ich tippe".

    const setThemeMode=(mode)=>{try{
      ...
      localStorage.setItem("epk_theme",mode);   // <- wirft
      const d=resolveTheme(mode,_systemDark());
      setIsDark(d);                             // <- laeuft nie
      applyTheme(d);                            // <- laeuft nie
      _themeToast(mode);
    }catch(e){console.warn('[silent-ls]',...);}};

Das Schreiben steht VOR der Anzeige, und beides liegt im selben `try`. Wirft
`setItem`, bleibt die Oberflaeche unveraendert - und der `catch` schreibt in
die Konsole, die auf einem Telefon niemand sieht. Der Nutzer tippt, und
NICHTS passiert. Auch beim zehnten Mal nicht.

WANN WIRFT setItem AUF EINEM TELEFON - keine Theorie, bekannte Faelle:
  * iOS Safari im privaten Modus: Schreibkontingent null;
  * voller Speicher (QuotaExceededError) - diese App legt reichlich ab;
  * eine Browsereinstellung, die Seitendaten sperrt.

GEMESSEN WIRD DIE WIRKUNG: derselbe Lauf zweimal, einmal mit heilem
Speicher und einmal mit einem `setItem`, das fuer den Themenschluessel
wirft. Bleibt der Koerper im zweiten Lauf dunkel, ist der Verdacht belegt.

GEGENPROBE: der erste Lauf MUSS hell werden. Ohne ihn koennte die Messung
auch deshalb dunkel melden, weil der Schalter gar nicht getroffen wurde.
"""
import io
import json
import os
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = "https://epkolar.github.io/epkolar-app/index.html"


def _lokal_server():
    """🔴 Mit --lokal wird der ARBEITSBAUM gemessen statt der ausgelieferten
    Datei. Eine Kur muss VOR dem Ausliefern belegt sein; danach wird gegen
    LIVE gegengemessen, denn beides kann auseinanderlaufen."""
    import functools
    import http.server
    import socketserver
    import threading

    class Still(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    srv = socketserver.TCPServer(
        ("127.0.0.1", 0), functools.partial(Still, directory=WURZEL))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return "http://127.0.0.1:%d/index.html" % srv.server_address[1]


ZIEL_URL = LIVE

NUTZER = ("try{var u=JSON.parse(localStorage.getItem('epkolar_user')||'{}');"
          "u.role='admin';u.monteurId='M1';u.name='Gerhard Steinbichler';"
          "u.rolle='Geschaeftsfuehrer';"
          "localStorage.setItem('epkolar_user',JSON.stringify(u));}catch(e){}")

# Nach der Rollen-Saat eingesetzt: ab jetzt wirft jedes Schreiben auf den
# Themenschluessel - genau wie ein voller Speicher oder ein privater Modus.
SPEICHER_VOLL = """
(() => {
  const o = Storage.prototype.setItem;
  Storage.prototype.setItem = function (k, v) {
    if (String(k).indexOf('epk_theme') === 0) {
      const e = new Error('QuotaExceededError (nachgestellt)');
      e.name = 'QuotaExceededError';
      throw e;
    }
    return o.call(this, k, v);
  };
})();
"""

SCHALTER_JS = r"""
() => {
  const t = [];
  document.querySelectorAll('button,[role="button"]').forEach(e => {
    const s = ((e.innerText || '') + ' ' + (e.getAttribute('aria-label') || '')
               + ' ' + (e.title || '')).trim();
    if (!/hell|dunkel|dark|light|theme|auto|☀|🌙/i.test(s)) return;
    const r = e.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) return;
    t.push({text: s.slice(0, 48), x: r.x + r.width / 2, y: r.y + r.height / 2});
  });
  return t;
}
"""

MESS_JS = """
() => {
  let modus = null;
  try { modus = localStorage.getItem('epk_theme'); } catch (e) {}
  const b = getComputedStyle(document.body).backgroundColor;
  const m = /rgba?\\(([\\d.]+)[, ]+([\\d.]+)[, ]+([\\d.]+)/.exec(b || '');
  const h = m ? (0.2126 * +m[1] + 0.7152 * +m[2] + 0.0722 * +m[3]) / 255 : null;
  return {modus: modus, koerper: b, helligkeit: h};
}
"""


def lauf(pw, kaputt):
    b = pw.chromium.launch()
    try:
        ctx = b.new_context(viewport={"width": 390, "height": 844},
                            device_scale_factor=2, is_mobile=True,
                            has_touch=True, color_scheme="dark")
        s = ctx.new_page()
        s.add_init_script(NUTZER)
        s.add_init_script("try{localStorage.removeItem('epk_theme');}catch(e){}")
        if kaputt:
            s.add_init_script(SPEICHER_VOLL)
        s.goto(ZIEL_URL, wait_until="domcontentloaded", timeout=90000)
        s.wait_for_timeout(5000)
        getippt = []
        for _ in range(3):
            t = s.evaluate(SCHALTER_JS)
            if not t:
                break
            s.touchscreen.tap(t[0]["x"], t[0]["y"])
            getippt.append(t[0]["text"])
            s.wait_for_timeout(1200)
        m = s.evaluate(MESS_JS)
        m["getippt"] = getippt
        return m
    finally:
        b.close()


def main(argv):
    from playwright.sync_api import sync_playwright
    global ZIEL_URL
    if "--lokal" in argv:
        ZIEL_URL = _lokal_server()
    print("Gemessen gegen %s, 390 px, System DUNKEL\n"
          % ("den ARBEITSBAUM" if "--lokal" in argv
             else "die AUSGELIEFERTE Datei"))
    with sync_playwright() as pw:
        heil = lauf(pw, False)
        voll = lauf(pw, True)

    for name, m in (("A) Speicher heil", heil), ("B) Speicher VOLL", voll)):
        print("%-20s Modus=%-7s Koerper=%-22s Helligkeit=%s  (%d Tipps)"
              % (name, m.get("modus"), m.get("koerper"),
                 ("%.2f" % m["helligkeit"]) if m.get("helligkeit") is not None
                 else "?", len(m.get("getippt") or [])))

    io.open(os.path.join(WURZEL, "docs", "befunde",
                         "HELLMODUS_SPEICHER_VOLL.json"),
            "w", encoding="utf-8", newline="").write(
        json.dumps({"quelle": ZIEL_URL, "heil": heil, "voll": voll},
                   ensure_ascii=False, indent=1))
    print("\ngeschrieben: docs/befunde/HELLMODUS_SPEICHER_VOLL.json")

    if not (heil.get("helligkeit") or 0) > 0.5:
        print("\U0001F534 GEGENPROBE GESCHEITERT: schon mit heilem Speicher "
              "wird es nicht hell.\n   Dann misst dieser Lauf nicht, was er "
              "behauptet - der Schalter wurde nicht getroffen.")
        return 2
    if (voll.get("helligkeit") or 0) > 0.5:
        # 🔴 DERSELBE AUSGANG BEDEUTET HIER ZWEIERLEI, je nachdem, WAS
        # gemessen wurde. Gegen die ausgelieferte Datei heisst er: der
        # Verdacht traegt nicht. Gegen den Arbeitsbaum heisst er: die Kur
        # wirkt. Ein Werkzeug, das beides gleich benennt, erzaehlt in einem
        # der beiden Faelle etwas Falsches.
        if ZIEL_URL != LIVE:
            print("\U0001F7E2 BELEG DER KUR: auch mit blockiertem Speicher "
                  "wird der Bildschirm hell.\n"
                  "   Die Anzeige haengt nicht mehr am Schreiben.")
        else:
            print("\U0001F7E2 Auch mit vollem Speicher wird es hell - der "
                  "Verdacht traegt an dieser Stelle NICHT.")
        return 0
    print("\U0001F534 BELEGT: mit vollem Speicher bleibt der Bildschirm "
          "DUNKEL, obwohl getippt wurde.\n"
          "   Das Schreiben steht VOR der Anzeige und beides im selben try -\n"
          "   wirft setItem, laeuft applyTheme nie, und der catch schreibt "
          "nur in die\n   Konsole, die auf einem Telefon niemand sieht.")
    return 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
