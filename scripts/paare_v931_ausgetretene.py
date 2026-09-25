# -*- coding: utf-8 -*-
"""v3.9.931 - Anker/Ersatz-Paare: Ausgetretene aus Live-Belegschaft und Anspruch.

Der Auftrag verlangt Paare statt einer Aenderung an index.html. Diese Datei ist
die MASCHINELL ANWENDBARE Fassung - eine abgetippte Liste verliert CRLF und
Einrueckung, und genau daran scheitert ein Anker.

Pruefen (aendert nichts):      python scripts/paare_v931_ausgetretene.py
Anwenden:                      python scripts/paare_v931_ausgetretene.py --anwenden

Jeder Anker muss GENAU EINMAL vorkommen; sonst bricht das Skript ab, ohne etwas
zu schreiben. Die Datei wird mit newline="" gelesen und geschrieben, damit die
CRLF-Zeilenenden erhalten bleiben.

Danach:
  python scripts/_bracket_check.py index.html      -> () -1 / {} 0 / [] 0
  python -m pytest tests/test_ausgetretene_live_v931.py tests/test_ma_waehlbar_v874.py
"""
import sys

from pathlib import Path

CRLF = "\r\n"


def _z(*zeilen):
    return CRLF.join(zeilen) + CRLF


PAARE = [
 # 1 HomeView: gefilterte Live-Belegschaft definieren
 (_z("  const isOps=isAdmin||_isBuero;"),
  _z("  const isOps=isAdmin||_isBuero;",
     "  /* v3.9.931 LIVE-BELEGSCHAFT. Der Block Team und die Kachel Team aktiv zeigten Ausgetretene",
     "     als aktuelle Teammitglieder, samt Fahrzeug-Chip, und zaehlten sie in ... gesamt mit. Das",
     "     ist keine Filter- und keine Reportliste, sondern die Anzeige der heutigen Mannschaft.",
     "     Gefiltert wird ueber das BESTEHENDE Praedikat _maIstEhemalig aus v3.9.866 - keine zweite",
     "     Datumslogik. Das Wiener Datum wird wie in _sichtbareMA EINMAL berechnet, nicht pro Zeile.",
     "     Namensaufloesung ueber monteure.find und alle Filter-/Reportlisten bleiben unberuehrt: an",
     "     Ausgetretenen haengen Zeiteintraege und Scheine, die Worker-Zeile ist die einzige",
     "     Namensquelle. */",
     "  const _hkHV=_ezHeuteISO();",
     "  const _teamAktiv=(monteure||[]).filter(m=>!_maIstEhemalig(m,_hkHV));")),

 # 2 HomeView: Zaehler der Kachel Team aktiv
 (', monteure.length, " gesamt" )',
  ', _teamAktiv.length, " gesamt" )'),

 # 3 HomeView: Kachelband Team
 ("            , monteure.map(m=>{" + CRLF,
  "            , _teamAktiv.map(m=>{" + CRLF),

 # 4 AbsView: gefilterte Namensliste fuer den Anspruch
 (_z("  const names=monteure.map(m=>m.n);"),
  _z("  const names=monteure.map(m=>m.n);",
     "  /* v3.9.931 EIN ANSPRUCH FUER JEMANDEN, DER NICHT MEHR DA IST, IST KEINE HISTORIE. Das",
     "     Urlaubskontingent fuehrte fuer Ausgetretene weiter einen Jahresanspruch samt Resturlaub -",
     "     in der Kompaktliste, in der Detailtabelle und im Excel-Blatt, dessen Gesamt-Zeile ihn",
     "     mitsummierte. _kontNames ist dieselbe Namensliste ohne Ausgetretene, gemessen mit dem",
     "     BESTEHENDEN Praedikat _maIstEhemalig aus v3.9.866. names bleibt unveraendert: Kalender,",
     "     Krankenstandsliste, Jahresuebersicht, Team-Timeline und der Abwesenheits-Export sind",
     "     Filter- bzw. Reportlisten - wer die alten Krankenstaende eines Ausgetretenen sucht, muss",
     "     ihn dort weiter finden. */",
     "  const _hkAK=_ezHeuteISO();",
     "  const _kontNames=monteure.filter(m=>!_maIstEhemalig(m,_hkAK)).map(m=>m.n);")),

 # 5 AbsView: Kontingent-Kompaktliste
 ("""!kontExpanded&&(React.createElement('div', { style: {display:"flex",flexDirection:"column",gap:6}}, (isAdmin?names:names.filter(n=>n===myMonteurName)).map(m=>{const ks=""",
  """!kontExpanded&&(React.createElement('div', { style: {display:"flex",flexDirection:"column",gap:6}}, (isAdmin?_kontNames:_kontNames.filter(n=>n===myMonteurName)).map(m=>{const ks="""),

 # 6 AbsView: Kontingent-Detailtabelle
 ("""React.createElement('tbody', {}, (isAdmin?names:names.filter(n=>n===myMonteurName)).map(m=>{const ks=""",
  """React.createElement('tbody', {}, (isAdmin?_kontNames:_kontNames.filter(n=>n===myMonteurName)).map(m=>{const ks="""),

 # 7a AbsView: Zeilen des Kontingent-Blattes (genXls sumCol 9 = die Gesamt-Zeile)
 ("const data=[];names.forEach(function(m,i){const ks=",
  "const data=[];_kontNames.forEach(function(m,i){const ks="),

 # 7b AbsView: Kopfzeile des Kontingent-Blattes
 ('COMPANY_FOOTER.name+" · "+names.length+" Mitarbeiter · Std/Woche-basiert"',
  'COMPANY_FOOTER.name+" · "+_kontNames.length+" Mitarbeiter · Std/Woche-basiert"'),

 # 8 WerkzeugView: Umbuchen an einen anderen Monteur
 (", monteure.filter(m=>m.id!==scannedWz.zugewiesen).map(m=>(React.createElement('button'",
  ", /* v3.9.931: Umbuchen ist eine ZUWEISUNG - die Ausgabeliste direkt darueber zieht seit v3.9.874 ueber _maWaehlbar, diese hier nicht. Der aktuelle Traeger wird wie bisher ausgenommen. */ _maWaehlbar(monteure,scannedWz.zugewiesen).filter(m=>m.id!==scannedWz.zugewiesen).map(m=>(React.createElement('button'"),

 # 9 FahrzeugView: Fahrer der Bescheinigung nach VO (EG) Nr. 561/2006
 ("""monteure.filter(m=>(m.fs||"").includes("C")).map(m=>React.createElement('option'""",
  """_maWaehlbar(monteure.filter(m=>(m.fs||"").includes("C")),((monteure||[]).find(x=>x.n===beschForm.fahrer)||{}).id||"")/* v3.9.931: eine Bescheinigung wird fuer einen AKTUELLEN Fahrer ausgestellt. Der getragene Wert reist mit, damit eine aus der Historie geladene Bescheinigung ihren Fahrer im eigenen Feld behaelt - das Feld fuehrt den NAMEN, der Vergleich braucht darum die id dazu. */.map(m=>React.createElement('option'"""),

 # 10 Arbeitsschein-Kommentare: Vorschlagsliste der Erwaehnungen
 ("const fieldMA=(monteure||[]).filter(m=>(m.n||'').toLowerCase().includes(mentionFilter));",
  "const fieldMA=_maWaehlbar(monteure,null).filter(m=>(m.n||'').toLowerCase().includes(mentionFilter));/* v3.9.931: wer erwaehnt wird, wird ausgewaehlt - Ausgetretene stehen nicht mehr im Vorschlag. */"),
]


def main():
    ziel = Path(__file__).resolve().parents[1] / "index.html"
    quelle = ziel.read_text(encoding="utf-8", newline="")
    neu = quelle
    fehler = 0
    for i, (anker, ersatz) in enumerate(PAARE, 1):
        n = neu.count(anker)
        print("Paar %2d: %d Treffer" % (i, n))
        if n != 1:
            fehler += 1
            print("   NICHT EINDEUTIG (erwartet 1): %r" % anker[:120])
            continue
        neu = neu.replace(anker, ersatz, 1)
    if fehler:
        print("ABBRUCH - %d Anker nicht eindeutig, es wurde NICHTS geschrieben." % fehler)
        return 1
    if "--anwenden" not in sys.argv:
        print("Trockenlauf in Ordnung. Zum Schreiben: --anwenden")
        return 0
    ziel.write_text(neu, encoding="utf-8", newline="")
    print("geschrieben: %d -> %d Bytes"
          % (len(quelle.encode("utf-8")), len(neu.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
