# Grundstand vor dem UI-Umbau

Aufgenommen am 25.09.2026 an der Live-App **v3.9.930** (`f77b53f`),
Mobil-Viewport 390x844 (iframe derselben Origin, weil `resize_window`
bei maximiertem Fenster `innerWidth` nicht ändert).

**Zweck:** Nach jedem Design-Commit wird dieselbe Aufnahme wiederholt.
Was hier steht, muss danach noch da sein. Verschwundene Knöpfe, Felder,
Auswahloptionen oder Zahlen sind ein Regressionsfehler — auch dann,
wenn die Seite hübscher aussieht und alle Tests grün sind.

**Nicht enthalten und bewusst so:** Aussehen, Reihenfolge, Gruppierung,
Beschriftungstexte. Die dürfen sich ändern — darum geht es ja. Geprüft
wird nur, dass die *Handlung* und die *Zahl* erhalten bleiben.

---

## Mengengerüst je Seite

| Seite | Knöpfe | Eingabefelder | Auswahlfelder | erkannte Zahlen |
|---|---|---|---|---|
| Home | 34 | 0 | 0 | 7 |
| Projekte | 19 | 4 | 0 | 6 |
| Arbeitsscheine | 228 | 2 | 1 | 0 |
| Planung | 45 | 0 | 0 | 2 |
| Werkzeuge | 25 | 5 | 3 | 1 |
| Mitarbeiter | 14 | 0 | 0 | 0 |
| Fahrzeuge | 19 | 0 | 0 | 0 |
| Abwesenheiten | 38 | 0 | 0 | 21 |

Die 228 auf Arbeitsscheinen kommen aus der Liste selbst (Aktionsknöpfe je
Schein) — die Zahl schwankt mit dem Datenbestand und ist kein harter Wert.
Bei allen anderen Seiten ist die Zahl stabil und taugt als Prüfgröße.

---

## Home (34 Knöpfe)

Kopf: Sync-Anzeige, Theme, Benachrichtigungen (3), Abmelden, Neu laden,
Einstellungen.

Schnellzugriff: Neues Projekt · Arbeitsscheine · Wochenplanung ·
Urlaub beantragen · Fahrzeuge · Auswertungen · Tanken

Kacheln: Projekte aktiv · Scheine offen · Fahrzeuge · Werkzeugwert
(16 490 €, 296 Geräte) · Abwesenheiten (164, alle bearbeitet) ·
Monatsabrechnung (0/0) · Material (0 von 6) · Bautagebuch (0 diese Woche)

Baustellen-Karten: DR.-GSCHMEIDLERSTRASSE 10 (PA241923, GEDESAG, 523.4h) ·
BVH Sparkasse Ravelsbach (PA242467, 85.2h) · Weingut Gerald Waltner
(PA242231, 39.8h), plus "Alle →"

Zahlen: 48% · 3.5h · 40.5h · 523.4h · 85.2h · 39.8h

Bottom-Bar: Home · Baustelle · Zeit · Fuhrpark · Mehr

## Projekte (19 Knöpfe, 4 Felder)

Ansichtsumschalter (Kachel/Liste) · + Neues Projekt ·
Filter Aktiv 3 / Abgeschlossen 0 / Archiv 0 / Alle 3 ·
je Karte: Bearb. / Archiv / Löschen

## Arbeitsscheine (228 Knöpfe, 2 Felder, 1 Auswahlfeld)

OFFA Excel · Statuskacheln: Gesamt 185 · Offen (alle) 37 · aufgenommen 0 ·
freigegeben 0 · in Bearbeitung 37 · aufgeschoben 0 · erledigt 6 ·
abgerechnet 124 · bar bezahlt 0 · storniert 18 · Fertig (alle) 130

Unterreiter: Liste · QR Scan · Kalender · Dispo

Filter: Alle · Offen · In Arbeit · Erledigt · Meine · Heute · Überfällig ·
Kein Monteur · Filter (aufklappbar)

Suchfeld: "Suche Nr, Kunde, Arbeit..."
Sortierung: Nummer · Erf.-Datum · Termin (best.) · Termin (vorg.) ·
Status · Kunde · Monteur

**Die elf Statuswerte und die sieben Sortierkriterien sind die harte
Prüfliste dieser Seite.**

## Planung (45 Knöpfe)

Woche zurück/vor · KW-Sprungmarken KW12, KW16, KW26–KW38, KW40 ·
Nächste Woche · + Zeile · Vorlage · Vorwoche
Tageszahlen: 5 MA / 4 MA

Beim Umbau entfallen die KW-Sprungmarken als Knöpfe — das ist gewollt.
Erhalten bleiben muss: jede dort erreichbare KW ist weiterhin erreichbar.

## Werkzeuge (25 Knöpfe, 5 Felder, 3 Auswahlfelder)

+ Neues Gerät · Labels · Excel · PDF
Fünf unbeschriftete Icon-Reiter (📷 📋 📤 🔧 ✏️) — **ohne Text, ohne title,
ohne aria-label.** Was sie tun, ist aus dem DOM nicht ermittelbar.
Vor dem Umbau muss geklärt werden, wofür jeder steht.

Filter: Alle (296) · Verfügbar (290) · Ausgegeben (0) ·
Kalibrierung fällig (6) · Defekt (0)
Suchfeld: "Name, Seriennr, Inventar..."
Auswahlfeld Status: Verfügbar · Ausgegeben · In Reparatur ·
Kalibrierung fällig · Verloren/Defekt · Stillgelegt
Auswahlfeld Kategorie: Elektrowerkzeug · Messgeräte · Handwerkzeug ·
Maschinen · Sicherheit/PSA · Verbrauchsmaterial · Kabelwerkzeug ·
Leiter/Gerüst · Sonstiges
Je Gerät: Ausleihen

## Mitarbeiter (14 Knöpfe)

Mein Profil · **Nur Aktive** (der Ehemalige-Umschalter) · + Neuer Mitarbeiter ·
Stempel-Pausenregeln (aufklappbar) · KV-Konstanten Metallgewerbe (aufklappbar)

## Fahrzeuge (19 Knöpfe)

Listen-/Kachelumschalter · Scan · Batch · Labels · Excel · PDF · + Fahrzeug ·
Favoritenstern je Fahrzeug

## Abwesenheiten (38 Knöpfe, 21 Zahlen)

Bearbeiten · Urlaub beantragen · Krankmeldung · Zeitausgleich ·
Anträge prüfen · Details · Datei/Foto hochladen · Excel ·
Server (SRVDC02) · vier Ansichtsreiter

Kontingente: Aliti 193h/0K · Barger 193h/5K · Cracana 193h/9K ·
Günther -13h/0K · Kiener 116h/9K · Lindhuber 116h/0K · Paschinger 116h/0K ·
Pinger 56h/2K · Riedmann 137h/5K · Schmid 116h/0K · Schober 69h/0K

**Aliti und Cracana stehen hier noch drin** — das ist der bekannte
Ehemalige-Fund und wird vom laufenden Ehemalige-Auftrag behoben. Nach
dessen Abschluss ist der Grundstand an dieser Stelle zu aktualisieren,
sonst schlägt die Prüfung fälschlich an.

---

# NACHTRAG (Claude Code, 25.09.2026) — eine Stelle ist bereits überholt

## Abwesenheiten/Kontingente: erwartete Abweichung ab v3.9.931

Der Ehemalige-Auftrag ist seit **v3.9.931** (`1cb8dcc`) angewandt. Die
Kontingentliste in `AbsView` ist damit über `_maIstEhemalig` gefiltert.

**Erwartet ab v3.9.931 — das ist KEIN Regressionsfehler, sondern der Fix:**

- **Aliti und Cracana fehlen in der Kontingentliste.** Elf Namen werden zu
  neun, die "21 erkannten Zahlen" auf der Seite sinken entsprechend.
- Dieselbe Filterung greift in der **Detailtabelle**, im **Excel-Blatt** und
  in dessen **Kopfzeile** ("N Mitarbeiter") — die Gesamtzeile rechnet
  seither über die gefilterte Menge.
- **Home, Kachel "Team aktiv"**: Zähler und Kachelband zeigen nur noch aktive
  Monteure. Die Knopfzahl auf Home kann dadurch unter 34 fallen.

**Was sich dort ausdrücklich NICHT ändern darf** (und wogegen eigene Riegel
laufen, `tests/test_ausgetretene_live_v931.py`):

- Der Arbeitsschein eines Ausgetretenen zeigt seinen Namen weiter — keine
  Fragezeichen, kein leeres Feld. Historie verliert niemanden.
- Die Filter-, Report- und Kalenderlisten führen ihn weiter (Arbeitsschein-
  Filter, Mängel-Filter, Stundenzettel, Auswertung, Abwesenheits-Kalender).
- Eine **bestehende** Zuweisung bleibt wählbar: der eigene Schein, die
  geladene Fahrerbescheinigung, das getragene Werkzeug.

## Ein zweiter Punkt, der vor dem Umbau geklärt gehört

Der Grundstand nennt die **fünf unbeschrifteten Icon-Reiter in Werkzeuge**
(📷 📋 📤 🔧 ✏️) als "aus dem DOM nicht ermittelbar". Das deckt sich mit dem
Bestandsschutz-Zusatz: sie werden **nicht angefasst, nicht umbenannt, nicht
entfernt**, bis ihr Zweck geklärt ist. Offen, siehe
`docs/ENTSCHEIDUNGEN-OFFEN.md`.

## Wogegen abgenommen wird

Diese Datei ist die Abnahmegrundlage. Bei einer Abweichung gilt die Reihenfolge
aus dem Bestandsschutz-Zusatz: **zurückrollen statt nachbessern.** Eine
Abweichung ohne Begründung ist ein Fehler, kein Detail.
