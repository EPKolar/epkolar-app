# -*- coding: utf-8 -*-
"""D2: die Waechtertafel 10 -> 23 Tabellen. Wo ist "0 Zeilen" NORMAL?

FRAGE
─────
Der Waechter meldet: PUT/PATCH auf eine gelistete Tabelle, HTTP 200 und
LEERES ARRAY -> Fehlertoast "NICHT gespeichert - keine Schreibberechtigung".

Er wirft NICHT neu; ein Fehlalarm kostet also keinen Datensatz, sondern
einen falschen Fehlertoast - und Vertrauen. Drei Tabellen sind aus genau
diesem Grund draussen geblieben (worker_projects, defects/tickets,
notifications). Die Frage ist, ob unter den DREIZEHN aufgenommenen eine
ist, die dazugehoert haette.

VERFAHREN
─────────
Je gelisteter Tabelle werden die SQ.push-Stellen mit PUT/PATCH gesucht
(die Ziel-Adresse steht als `/api/<ressource>/<id>`), dazu
 * ob dieselbe Ressource auch per POST geschrieben wird
   (Upsert-Muster: PATCH ins Leere, danach POST -> 0 Zeilen ist NORMAL),
 * ob dieselbe Ressource in der Loeschkaskade von `projects` steht
   (dann kann ein spaeterer PATCH aus der Warteschlange ins Leere gehen),
 * ob es einen frueheren Abfang gibt (`return{ok:1}`), der die generische
   Strecke gar nicht erst erreicht - so war `worker_projects` tot.

Alles ueber die Codemaske: die D2-Kommentare NENNEN die dreizehn
Tabellennamen woertlich, ein roher Textzaehler misst seine eigene
Begruendung mit.

KOEDER
──────
--koeder nimmt in einer KOPIE `notifications` in die Tafel auf. Das ist der
BEKANNTE Fall, bei dem 0 Zeilen normal ist (clear/read-all loeschen
dieselben Zeilen). Meldet das Skript ihn dann nicht als verdaechtig, sucht
es nicht nach dem, was es behauptet.
"""
import re
import sys

from nebenwirkung_helfer import lies, codemaske, zeile_von

NEU_V994 = ["werkzeuge", "projects", "finkzeit", "project_documents",
            "bauprovisorien_mieten", "bauprovisorien", "checklists",
            "material_orders", "supplier_configs", "supplier_orders",
            "fz_termine", "gefahrstoff_folders", "project_folders"]
ALT = ["fahrzeuge", "tankbelege", "forms", "bautagebuch", "material_catalogs",
       "arbeitsscheine", "plans", "absences"]
DRAUSSEN = ["worker_projects", "defects", "tickets", "notifications"]


def tafel(text, maske):
    a = text.index("const _RLS_SILENT_DENIAL_LABELS")
    b = text.index("});", a)
    namen = []
    for m in re.finditer(r"^\s*([a-z_]+)\s*:", text[a:b], re.M):
        p = a + m.start(1)
        if maske[p]:
            namen.append(m.group(1))
    return namen, a, b


def route_map(text, maske):
    """ROUTE_MAP: Client-Weg -> Supabase-Tabelle.

    MEIN ERSTER ZAEHLER WAR FALSCH: er verglich den Tabellennamen direkt mit
    der URL und meldete darum `time_entries: 0 PUT` - der Weg heisst aber
    `/api/entries/`. Ein Zaehler, der EINE Schreibweise nicht kennt, meldet
    "kommt nicht vor", und das sieht aus wie ein Befund. Jetzt aus dem
    GEMESSENEN ROUTE_MAP statt aus einer Annahme.
    """
    a = text.index("const ROUTE_MAP={")
    b = text.index("\n};", a)
    mp = {}
    for m in re.finditer(r'"([a-z_-]+)"\s*:\s*\[\s*"([a-z_-]+)"\s*,\s*"([a-z_]+)"\s*\]',
                         text[a:b]):
        # NICHT maske[m.start()] pruefen: das ist das OEFFNENDE
        # Anfuehrungszeichen und gilt als Zeichenkette, nicht als Code -
        # der Zaehler meldete darum 0 Wege, und das sah aus wie ein Befund.
        # Geprueft wird die schliessende eckige Klammer; die ist Code.
        if maske[a + m.end() - 1]:
            mp[m.group(1)] = m.group(3)
    return mp


def sq_stellen(text, maske):
    out = []
    for m in re.finditer(r"SQ\.push\(\{", text):
        p = m.start()
        if not maske[p]:
            continue
        blk = text[p:p + 600]
        u = re.search(r'url\s*:\s*["\'`]([^"\'`]+)', blk)
        me = re.search(r'method\s*:\s*["\']([A-Z]+)', blk)
        # url kann zusammengesetzt sein: "/api/werkzeuge/"+id
        out.append((p, zeile_von(text, p), u.group(1) if u else "", me.group(1) if me else ""))
    return out


def main():
    text = lies()
    if "--koeder" in sys.argv:
        anker = '  material_catalogs:"Material-Katalog"'
        if anker not in text:
            print("KOEDER GESCHEITERT: Anker nicht gefunden.")
            return 2
        text = text.replace(anker, '  notifications:"Benachrichtigung",\n' + anker, 1)
        print("KOEDER AKTIV: notifications kuenstlich in die Tafel aufgenommen.\n")
    maske = codemaske(text)

    namen, a, b = tafel(text, maske)
    print("Tafel _RLS_SILENT_DENIAL_LABELS: %d Eintraege (Zeile %d..%d)"
          % (len(namen), zeile_von(text, a), zeile_von(text, b)))
    print("  " + ", ".join(namen))
    print("")

    sq = sq_stellen(text, maske)
    print("SQ.push-Stellen im CODE: %d" % len(sq))
    meth = {}
    for _, _, _, m in sq:
        meth[m] = meth.get(m, 0) + 1
    print("  nach Verb: " + ", ".join("%s=%d" % (k or "?", v) for k, v in sorted(meth.items())))
    print("")

    # Loeschkaskade von projects
    k = text.index('const _kids=[')
    kids = re.findall(r'"([a-z_]+)"', text[k:text.index("]", k)])
    print("Loeschkaskade beim Loeschen eines Projekts loescht: %s" % ", ".join(kids))
    print("")

    rm = route_map(text, maske)
    print("ROUTE_MAP: %d Wege" % len(rm))
    ohne_weg = [t for t in namen if t not in rm.values()]
    print("Tafel-Eintraege OHNE Weg in ROUTE_MAP (koennen NIE feuern): %s"
          % (", ".join(ohne_weg) or "keiner"))
    print("")

    print("JE GELISTETER TABELLE: Schreibverben und Verdachtsgruende")
    print("%-24s %-6s %-6s %-6s  %s" % ("Tabelle", "PUT", "POST", "DEL", "Verdacht"))
    for t in namen:
        wege = [w for w, tab in rm.items() if tab == t]
        put = post = dele = 0
        for p, z, u, m in sq:
            mm = re.match(r"^/api/([a-z_-]+)", u)
            if not mm or mm.group(1) not in wege:
                continue
            if m in ("PUT", "PATCH"):
                put += 1
            elif m == "POST":
                post += 1
            elif m == "DELETE":
                dele += 1
        gruende = []
        if t in kids:
            gruende.append("steht in der Loeschkaskade von projects -> "
                           "ein spaeterer PATCH aus der Warteschlange trifft 0 Zeilen")
        if post and put:
            gruende.append("wird auch per POST geschrieben (Upsert-Muster moeglich)")
        if t in DRAUSSEN:
            gruende.append("🔴 GEHOERT NACH DER EIGENEN BEGRUENDUNG NICHT IN DIE TAFEL")
        if put == 0:
            gruende.append("KEINE PUT/PATCH-Stelle ueber SQ.push gefunden - "
                           "Eintrag moeglicherweise WIRKUNGSLOS (wie fz_schaeden)")
        mark = "NEU-v994" if t in NEU_V994 else ""
        print("%-24s %-6d %-6d %-6d  %-8s %s"
              % (t, put, post, dele, mark, "; ".join(gruende) or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
