# -*- coding: utf-8 -*-
"""Riegel-Entwurf v3.9.909: eine ausgebliebene Messung darf nicht als Zahl erscheinen.

Vorgesehener Ort im Repo: tests/test_nichtgemessen_v909.py
Alle Pruefungen laufen KOMMENTARBLIND ueber tests/_hilfen.nur_code - sonst misst
der Riegel die Erklaerkommentare mit, die neben der Reparatur stehen (im Repo
inzwischen zehnmal passiert).

Aufruf hier (ausserhalb des Repos, zur Umkehrprobe):
    python riegel_v3_9_909.py <pfad-zu-index.html>
Exit 0 = gruen, Exit 1 = rot.
"""
import re
import sys


def nur_code(index_html):
    ohne = re.sub(r"/\*[\s\S]*?\*/", "", index_html)
    return "\n".join(l for l in ohne.splitlines()
                     if not l.lstrip().startswith("const APP_VERSION="))


# (Name, muss_vorkommen, darf_nicht_vorkommen)
FAELLE = [
    # 1 - Chef-Dashboard: drei Kacheln, deren Zustand auf null steht
    ("kachel_matOpen",   "catch(_){if(a)setMatOpen(null);}",   "catch(_){if(a)setMatOpen(0);}"),
    ("kachel_gsCount",   "catch(_){if(a)setGsCount(null);}",   "catch(_){if(a)setGsCount(0);}"),
    ("kachel_absPending", "catch(_){if(a)setAbsPending(null);}", "catch(_){if(a)setAbsPending(0);}"),
    # 2 - Monatsabrechnung offen
    ("finkOpen_catch",   "catch(_){if(alive)setFinkOpen(null);}", "catch(_){if(alive)setFinkOpen([]);}"),
    ("finkOpen_abruf",   "&select=worker_id,monat,status');",
     "&select=worker_id,monat,status').catch(()=>[]);"),
    # 3 - Abwesend naechste Woche
    ("nextWeekAbs_ungeladen", "{setNextWeekAbs(null);return;}", "{setNextWeekAbs([]);return;}"),
    ("nextWeekAbs_catch", "catch(_){setNextWeekAbs(null);}", "catch(_){setNextWeekAbs([]);}"),
    # 4 - Maengel & Tickets
    ("mtStats_catch", "setMtStats({tOpen:null,tOver:null,dOpen:null,dOver:null,top:[]})",
     "setMtStats({tOpen:0,tOver:0,dOpen:0,dOver:0,top:[]})"),
    ("mtStats_gate", "mtStats&&(mtStats.tOpen===null||mtStats.tOpen>0||mtStats.dOpen>0)",
     "mtStats&&(mtStats.tOpen>0||mtStats.dOpen>0)&&"),
    ("mtStats_abruf", 'status,project_id");\n    const df=', 'status,project_id").catch(()=>[]);'),
    # 5 - Monatsabrechnungs-Kachel im Ops-Dashboard
    ("finkStats_init", "pendingDetails:[],geladen:false}", "diffWarn:0,pendingDetails:[]});"),
    ("finkStats_stats", "diffWarn,pendingDetails,geladen:true}", "diffWarn,pendingDetails};"),
    ("finkStats_leer_ist_messung", "if(!Array.isArray(data))return;", "if(!data||!data.length)return;"),
    ("finkStats_kachel", 'finkStats.geladen?"Alle abgeglichen":"nicht gemessen"',
     'finkStats.offen+" offen":"Alle abgeglichen")'),
    # 6 - Live-KPIs
    ("liveKpis_init", "{matOpen:null,matTotal:null,btWeek:null,btTotal:null,actToday:null,loading:false}",
     "{matOpen:0,matTotal:0,btWeek:0,btTotal:0,actToday:0,loading:false}"),
    ("liveKpis_material", 'liveKpis.matOpen==null?"…":liveKpis.matOpen', 'fontFamily:mono}}, liveKpis.matOpen)'),
    ("liveKpis_bautagebuch", 'liveKpis.btWeek==null?"…":liveKpis.btWeek', 'fontFamily:mono}}, liveKpis.btWeek)'),
    ("liveKpis_team", 'liveKpis.actToday==null?"…":liveKpis.actToday', 'fontFamily:mono}}, liveKpis.actToday)'),
]


def main(pfad):
    code = nur_code(open(pfad, encoding="utf-8").read())
    rot = []
    for name, muss, darf_nicht in FAELLE:
        if muss not in code:
            rot.append(name + ": FEHLT -> " + muss[:70])
        if darf_nicht and darf_nicht in code:
            rot.append(name + ": STEHT NOCH DA -> " + darf_nicht[:70])
    for z in rot:
        print("ROT " + z)
    print(("GRUEN %d/%d" % (len(FAELLE), len(FAELLE))) if not rot
          else ("ROT %d Befunde" % len(rot)))
    return 1 if rot else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
