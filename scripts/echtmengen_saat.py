# -*- coding: utf-8 -*-
"""Die Saat auf REALITAETSNAHE Mengen heben - und die Mindestmenge pruefbar machen.

WARUM DIESE DATEI EXISTIERT
───────────────────────────
Sebastians echter Bestand: 185 Arbeitsscheine, 296 Werkzeuge, 21 Fahrzeuge,
9 aktive Mitarbeiter. Die vorhandene Saat fuehrt 6 Scheine, 6 Werkzeuge,
3 Fahrzeuge und - je Sondengruppe verschieden - 3 oder 5 Mitarbeiter.

Eine Wochenplanung mit drei Monteuren hat weniger kleine Beschriftungen als
eine mit neun. Eine Fahrzeugliste mit drei Zeilen hat weniger Tippziele als
eine mit 21. Ein Pruefstand, der nur drei Monteure sieht, KANN nicht finden,
was bei neun auftritt - er meldet gruen, weil die Grundgesamtheit den Fall
nicht enthaelt.

WAS HIER NICHT NEU GEBAUT WIRD
──────────────────────────────
Die Feldformen stammen aus den vorhandenen Saatfunktionen und werden NICHT
nachgebaut: `B._scheine()` liefert die Schein-Form, `B.WERKZEUGE` die
Werkzeug-Form, `B12._fahrzeuge12()` die Fahrzeug-Form, `S._plandaten()` und
`S._formulare()` die Projektakte. Diese Datei nimmt genau diese Listen als
ERSTE Elemente und haengt an. Damit bleiben die Koeder der bestehenden
Messungen gueltig:

  * S1/S2 bleiben OFFA-verwaist, S3 bleibt juprowa-gebunden aber frisch
    (Gegenprobe im Datensatz selbst, aus `S._scheine8`).
  * M4 bleibt der Ausgetretene MIT Beitrag, M5 der OHNE - das ist Koeder K14
    aus `b3_stufen_12_15_messen`.

🔴 KEINE ECHTEN PERSONENDATEN. Alle Namen sind erfunden. Absichtlich dabei:

  * ZWEI Nachnamenpaare mit gleichem Anfang, damit eine Kuerzung auf sechs
    Zeichen zur Verwechslung fuehrt:
      Steinbichler / Steinberger      -> beide "Steinb"
      Hinterleitner / Hinterhuber     -> beide "Hinter"
  * ZWEI ungewoehnlich lange Nachnamen (24 Zeichen), dazu der schon
    vorhandene Wieshofer-Prandtner (19):
      Pfeiffenberger-Dollinger
      Brandstetter-Hollenstein

DIE MINDESTMENGE
────────────────
`MINDEST` haelt je Speicher die Zahl, unter der ein Lauf NICHT AUSSAGEKRAEFTIG
ist. `mindestmenge_pruefen()` gibt die Verletzungen zurueck; der Melder in
`echtmengen_messen.py` stempelt den Lauf dann als „nicht aussagekraeftig" und
NICHT als bestanden. Das ist dieselbe Regel, die `bestand.py` und
`code_scan.py` tragen: eine leere oder zu duenne Grundgesamtheit besteht keine
Probe.
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import mob_ansicht_messen as M           # noqa: E402
import b3_vier_ansichten_messen as B     # noqa: E402
import b3_stufen_8_11_messen as S        # noqa: E402
import b3_stufen_12_15_messen as B12     # noqa: E402


# ══════════════════════════════════════════════════════════════════════════
# Mindestmengen - der Kern des Auftrags
# ══════════════════════════════════════════════════════════════════════════
# Unter diesen Zahlen ist eine Messung eine Aussage ueber einen Prueffall,
# nicht ueber die App. Die Richtwerte kommen aus Sebastians Bestand.
MINDEST = {
    "monteure": 11,          # 9 aktive + 2 ausgetretene
    "monteure_aktiv": 9,
    "monteure_ausgetreten": 2,
    "fahrzeuge": 21,
    "werkzeuge": 290,        # Richtwert 300, echter Bestand 296
    "arbeitsscheine": 180,   # Richtwert 185
    "projects": 3,
}

# Wieviele verschiedene Saatmarken muss eine Ansicht zeigen, damit ihre Zahlen
# etwas ueber die App sagen? Eine Ansicht, die zwei Namen zeigt, ist nicht
# "bestanden", sie ist UNGEMESSEN.
MINDEST_MARKEN_IN_ANSICHT = 3


# ══════════════════════════════════════════════════════════════════════════
# Mitarbeiter: 9 aktive + 2 ausgetretene
# ══════════════════════════════════════════════════════════════════════════
# Die ersten fuenf sind UNVERAENDERT aus B12.MONTEURE - M4/M5 tragen Koeder
# K14 (ausgetreten mit / ohne Beitrag).
_NEUE_MONTEURE = [
    # Gleicher Anfang wie Steinbichler -> "Steinb" bei sechs Zeichen
    {"id": "M6", "n": "Maximilian Steinberger", "r": "Monteur",
     "austritt": "", "rolle": "Monteur", "aktiv": True},
    # Gleicher Anfang wie Hinterleitner -> "Hinter" bei sechs Zeichen
    {"id": "M7", "n": "Annemarie Hinterhuber", "r": "Helfer",
     "austritt": "", "rolle": "Helfer", "aktiv": True},
    # Ungewoehnlich lang (24 Zeichen Nachname)
    {"id": "M8", "n": "Konstantin Pfeiffenberger-Dollinger",
     "r": "Obermonteur", "austritt": "", "rolle": "Obermonteur",
     "aktiv": True},
    # Ungewoehnlich lang (24 Zeichen Nachname)
    {"id": "M9", "n": "Katharina Brandstetter-Hollenstein", "r": "Monteur",
     "austritt": "", "rolle": "Monteur", "aktiv": True},
    {"id": "M10", "n": "Fabian Grubmueller", "r": "Lehrling",
     "austritt": "", "rolle": "Lehrling", "aktiv": True},
    {"id": "M11", "n": "Veronika Tauchner", "r": "Monteur",
     "austritt": "", "rolle": "Monteur", "aktiv": True},
]

MONTEURE = [dict(m) for m in B12.MONTEURE] + [dict(m) for m in _NEUE_MONTEURE]

AKTIVE = [m["id"] for m in MONTEURE if not m.get("austritt")]
AUSGETRETEN = [m["id"] for m in MONTEURE if m.get("austritt")]

# Die Verwechslungspaare ausdruecklich benannt, damit eine spaetere Messung
# sie nicht suchen muss.
VERWECHSLUNGSPAARE = [("Steinbichler", "Steinberger"),
                      ("Hinterleitner", "Hinterhuber")]
LANGE_NAMEN = ["Pfeiffenberger-Dollinger", "Brandstetter-Hollenstein",
               "Wieshofer-Prandtner"]


# ══════════════════════════════════════════════════════════════════════════
# Projekte: 3
# ══════════════════════════════════════════════════════════════════════════
PROJEKTE = [dict(p) for p in B.PROJEKTE] + [
    {"id": "P3", "nr": "PA243311",
     "name": "BVH Wohnhausanlage Muehlbachgasse 22-26", "kunde": "NOEWOG",
     "ort": "Sankt Leonhard am Hornerwald", "status": "aktiv",
     "fortschritt": 71},
]


# ══════════════════════════════════════════════════════════════════════════
# Werkzeuge: ~300
# ══════════════════════════════════════════════════════════════════════════
# Form aus B.WERKZEUGE abgelesen, nicht geraten. Die sechs Originale bleiben
# W1..W6 und behalten ihre Status (darunter `verloren` und `stillgelegt`).
_WZ_STATUS = ["verfuegbar", "ausgegeben", "reparatur", "kalibrierung",
              "verloren", "stillgelegt"]
_WZ_KAT = ["elektro", "mess", "kabel", "leiter", "maschine", "sicherheit"]
_WZ_MARKEN = [
    ("Hilti", ["TE 7-C Bohrhammer", "SFC 22-A Akkuschrauber",
               "DD 150-U Diamantbohrgeraet", "PM 40-MG Multilinienlaser",
               "AG 125-A22 Winkelschleifer"]),
    ("Fluke", ["T6-1000 Spannungspruefer", "279 FC Waermebild-Multimeter",
               "1663 Installationstester", "i400 Stromzange",
               "435-II Netzanalysator"]),
    ("Knipex", ["Crimpzange 97 52 36", "Seitenschneider 74 02 250",
                "Abisolierwerkzeug 12 42 195", "Wasserpumpenzange Cobra XL"]),
    ("Guenzburger", ["Schiebeleiter 3x12 Sprossen",
                     "Rollgeruest Basic Plus 4,4 m",
                     "Podestleiter 6 Stufen fahrbar"]),
    ("Bosch", ["GWS 18V-10 Winkelschleifer", "GSR 18V-90 FC Akkuschrauber",
               "GLL 3-80 CG Linienlaser", "GAS 35 L Industriesauger"]),
    ("uvex", ["Schutzbrille sportstyle", "Gehoerschutz K2P Kapsel",
              "Schnittschutzhandschuh C500 wet"]),
    ("Weidmueller", ["Abmantelwerkzeug Stripax Ultimate",
                     "Crimpzange PZ 6 Roto L"]),
    ("Testo", ["875i Waermebildkamera", "760-3 TRMS Multimeter"]),
    ("Rothenberger", ["Rohrbiegegeraet Robend 4000",
                      "Pressmaschine Romax 4000 Basic"]),
]
_WZ_ORTE = ["Lager", "Lager Regal 4 links", "Baustelle", "Werkstatt/Service",
            "Fahrzeug GU-123EP", "Fahrzeug GU-777EP", "Buero Krems",
            "Aussenlager Ravelsbach", "unbekannt"]


def _werkzeuge(bis=300):
    """Die sechs Originale plus generierte bis `bis` Stueck.

    Absichtlich dabei: sehr lange Bezeichnungen (Marke + Typ + Zusatz), weil
    genau die in einer Tabellenspalte kuerzen, umbrechen oder quer rollen -
    und weil eine Liste kurzer Namen davon nichts zeigt.
    """
    aus = [dict(w) for w in B.WERKZEUGE]
    k = len(aus)
    i = 0
    while len(aus) < bis:
        marke, typen = _WZ_MARKEN[i % len(_WZ_MARKEN)]
        typ = typen[(i // len(_WZ_MARKEN)) % len(typen)]
        nr = len(aus) + 1
        stat = _WZ_STATUS[i % len(_WZ_STATUS)]
        kat = _WZ_KAT[(i // 2) % len(_WZ_KAT)]
        zusatz = (" mit Transportkoffer und Zubehoersatz"
                  if i % 7 == 0 else
                  (" Set inkl. Ladegeraet und zwei Akkus" if i % 7 == 3
                   else ""))
        aus.append({
            "id": "W%d" % nr,
            "name": "%s %s%s" % (marke, typ, zusatz),
            "kat": kat,
            "seriennr": "%s-%05d-%02d" % (marke[:2].upper(), 10000 + nr * 7,
                                          i % 97),
            "inventarnr": "EK-%s%03d" % (kat[:1].upper(), nr),
            "status": stat,
            "zugewiesen": AKTIVE[i % len(AKTIVE)] if stat == "ausgegeben"
                          else "",
            "projekt": PROJEKTE[i % 3]["id"] if stat == "ausgegeben" else "",
            "standort": _WZ_ORTE[i % len(_WZ_ORTE)],
            "letzteKalib": "2025-%02d-%02d" % (1 + i % 12, 1 + i % 27)
                           if kat == "mess" else "",
            "naechsteKalib": "2026-%02d-%02d" % (1 + i % 12, 1 + i % 27)
                             if kat == "mess" else "",
            "anschaffung": "%d-%02d-%02d" % (2014 + i % 12, 1 + i % 12,
                                             1 + i % 27),
            "wert": 45 + (i * 37) % 3200,
            "notizen": ("Kalibrierung ueberfaellig, Termin beim Hersteller "
                        "angefragt" if stat == "kalibrierung" else
                        ("Auf der Baustelle verschwunden" if stat == "verloren"
                         else "")),
            "zustandBewertung": 1 + i % 5,
        })
        i += 1
    assert len(aus) >= bis, len(aus)
    assert k == 6, k
    return aus


WERKZEUGE = _werkzeuge(300)


# ══════════════════════════════════════════════════════════════════════════
# Fahrzeuge: 21
# ══════════════════════════════════════════════════════════════════════════
_FZ = [("Mercedes", "Sprinter 317 CDI Kastenwagen Hochdach"),
       ("VW", "Crafter 35 TDI Kastenwagen lang"),
       ("Ford", "Transit Custom 320 L2H1 Trend"),
       ("Renault", "Master L3H2 dCi 150"),
       ("Fiat", "Ducato Maxi 35 Multijet 3 Kastenwagen"),
       ("Opel", "Vivaro Cargo L Edition"),
       ("Peugeot", "Boxer 335 L2H2 BlueHDi"),
       ("Iveco", "Daily 35S14 Pritsche Doppelkabine"),
       ("Toyota", "Proace City Verso Family"),
       ("VW", "Caddy Cargo Maxi TDI")]
_FZ_STATUS = ["aktiv", "faehrt", "steht", "wartet", "inaktiv", "kein_tracker",
              "stillgelegt"]


def _fahrzeuge(bis=21):
    """Die drei Originale aus B12._fahrzeuge12() plus generierte bis 21."""
    aus = [dict(f) for f in B12._fahrzeuge12()]
    i = 0
    while len(aus) < bis:
        nr = len(aus) + 1
        marke, modell = _FZ[i % len(_FZ)]
        stat = _FZ_STATUS[i % len(_FZ_STATUS)]
        fahrer = AKTIVE[i % len(AKTIVE)] if stat in ("aktiv", "faehrt") else ""
        km = 12000 + (i * 18731) % 290000
        aus.append({
            "id": "F%d" % nr,
            "kennzeichen": "%s-%d%02dEP" % (["GU", "KR", "HO", "ZT"][i % 4],
                                            1 + i % 9, 10 + i % 89),
            "marke": marke, "modell": modell, "status": stat,
            "fahrer": fahrer, "kmStand": km,
            "naechstePickerl": B12._iso_vor(-(i * 13 % 300) + 40),
            "tankLog": [{"datum": B12._iso_vor(2 + i % 20),
                         "liter": 40.0 + (i * 3) % 45,
                         "preis": 70.0 + (i * 5) % 90,
                         "km": km - 300}],
            "schaeden": ([{"id": "SD%d" % nr, "status": "offen",
                           "beschreibung": "Heckklappenschloss schwergaengig, "
                                           "Dichtung Fahrertuer eingerissen",
                           "datum": B12._iso_vor(5 + i % 40)}]
                         if i % 3 == 0 else []),
            "serviceheft": [], "verbrauchsmaterial": {},
        })
        i += 1
    return aus


FAHRZEUGE = _fahrzeuge(21)


# ══════════════════════════════════════════════════════════════════════════
# Arbeitsscheine: ~185 ueber ALLE Scheinstatus
# ══════════════════════════════════════════════════════════════════════════
# 🔴 GEMESSEN, NICHT ANGENOMMEN: `AS_STATUS` in index.html fuehrt ACHT
# Scheinstatus, nicht elf -
#   aufgenommen · freigegeben · in_bearbeitung · aufgeschoben ·
#   erledigt · abgerechnet · bar_bezahlt · storniert
# (Gruppen: offen / fertig / storniert). Der Auftrag nannte elf; die Zahl
# steht im Bericht als Abweichung. Verteilt wird ueber alle acht.
STATUS_ALLE = ["aufgenommen", "freigegeben", "in_bearbeitung", "aufgeschoben",
               "erledigt", "abgerechnet", "bar_bezahlt", "storniert"]

_KUNDEN = [
    ("Marktgemeinde Sankt Leonhard am Hornerwald", "Steiner Landstrasse 44",
     "3572"),
    ("Hinterleitner Gebaeudetechnik GmbH", "Wachaustrasse 118a", "3620"),
    ("GEDESAG Gemeinnuetzige Donau-Ennstaler Siedlungs-AG",
     "Dr.-Gschmeidlerstrasse 10", "3500"),
    ("Weingut Gerald Waltner", "Kellergasse 7", "3491"),
    ("Sparkasse Ravelsbach Zweigstelle", "Hauptplatz 2", "3720"),
    ("Pfarre Sankt Michael Oberoesterreich", "Kirchenplatz 1", "4362"),
    ("Steinberger Landtechnik und Hofservice OG", "Feldgasse 12b", "3580"),
    ("Hinterhuber Baustoffhandel KG", "Industriestrasse 4", "3510"),
    ("NOEWOG Wohnbau Niederoesterreich", "Muehlbachgasse 22-26", "3550"),
    ("Volksschule Oberstockstall Gemeindeverband",
     "Schulgasse 1a", "3470"),
    ("Kellergassenverein Roehrenbach-Waldreichs", "Am Kellerberg 3", "3593"),
    ("Autohaus Pfeiffenberger GmbH & Co KG", "Wiener Strasse 88", "3500"),
]
_ARBEITEN = [
    "Zaehlerkasten tauschen, Hauptleitung neu ziehen, FI-Schutzschalter "
    "nachruesten und Endpruefung samt Protokoll",
    "Stoerung Aussenbeleuchtung Stiegenhaus 2 - Bewegungsmelder defekt, "
    "Ersatz mitbringen",
    "Wartung Notlichtanlage, 24 Leuchten, Batterietest und Pruefbuch "
    "nachtragen",
    "Neuinstallation Weinkeller: 14 Steckdosen, 6 Leuchten, Verteiler "
    "erweitern",
    "Netzwerkverkabelung Schalterhalle, 18 Datendosen Cat.7",
    "Blitzschutz Pruefung nach OeVE/OeNORM E 8049 mit Befund",
    "Ladestation 22 kW setzen, Zuleitung 5x6 mm2, Lastmanagement anbinden",
    "Rauchwarnmelder Tausch in 14 Wohnungen, Uebergabeprotokoll je Wohnung",
]
_SCHEINART = ["stoerung", "wartung", "montage", "reparatur", "kein"]
_PRIO = ["keine", "normal", "hoch", "dringend"]


def _scheine(bis=185):
    """Die acht Scheine aus B12._scheine12() plus generierte bis `bis`.

    Die ersten acht bleiben BYTEGLEICH: S1/S2 sind OFFA-verwaist, S3 ist
    juprowa-gebunden aber frisch (die Gegenprobe im Datensatz selbst),
    S7/S8 haengen an M4 - dem Ausgetretenen MIT Beitrag. Wer diese acht
    ersetzt, nimmt drei Koedern ihre Grundlage.
    """
    aus = [dict(s) for s in B12._scheine12()]
    tage = B._tage(-21, 42)
    i = 0
    while len(aus) < bis:
        nr = len(aus) + 1
        kd = _KUNDEN[i % len(_KUNDEN)]
        stat = STATUS_ALLE[i % len(STATUS_ALLE)]
        # Ausgetretene bekommen nur in der `fertig`-Gruppe Scheine; M5 nie.
        mid = (AKTIVE[i % len(AKTIVE)] if stat in
               ("aufgenommen", "freigegeben", "in_bearbeitung", "aufgeschoben")
               else (["M4"] + AKTIVE)[i % (len(AKTIVE) + 1)])
        if i % 11 == 0:
            mid = ""          # ohne Monteur: die Dispo muss sie unterbringen
        aus.append({
            "id": "S%d" % nr, "nummer": "AS-%d" % (2400 + nr),
            "kundName": kd[0], "kunde": kd[0],
            "kundNr": "K-%05d" % (10000 + nr * 13),
            "arbeitsort": kd[1], "plz": kd[2],
            "arbeitsanweisungen": _ARBEITEN[i % len(_ARBEITEN)],
            "monteur": mid,
            "aufgenommen": tage[i % len(tage)],
            "erfassungsdatum": B12._iso_vor(i % 160),
            "terminBestaetigt": tage[(i + 3) % len(tage)] if i % 4 else "",
            "terminVorschlag": tage[(i + 5) % len(tage)] if i % 4 == 0 else "",
            "terminZeit": ["07:30", "08:00", "09:15", "13:00"][i % 4],
            "scheinstatus": stat,
            "prioritaet": _PRIO[i % len(_PRIO)],
            "prio": _PRIO[i % len(_PRIO)],
            "scheinart": _SCHEINART[i % len(_SCHEINART)],
            "sachbearbeiter": MONTEURE[i % len(MONTEURE)]["n"],
            "projektnr": PROJEKTE[i % 3]["nr"],
            "dauer": ["2h", "4h", "6h", "8h"][i % 4],
        })
        i += 1
    return aus


ARBEITSSCHEINE = _scheine(185)


# ══════════════════════════════════════════════════════════════════════════
# Zeiten, Abwesenheiten, Stundenzettel, Kontingente - ueber ALLE 9 Aktiven
# ══════════════════════════════════════════════════════════════════════════
def _eintraege():
    """Die Eintraege aus B12._eintraege12() plus je Aktiven zehn Tage."""
    aus = [dict(e) for e in B12._eintraege12()]
    n = 0
    for mid in AKTIVE:
        for t in range(10):
            n += 1
            pid = PROJEKTE[(n + t) % 3]["id"]
            aus.append({
                "id": "ZE%04d" % n, "worker": mid, "w": mid,
                "datum": B12._iso_vor(t + 1)[:10],
                "date": B12._iso_vor(t + 1)[:10],
                "project_id": pid, "pid": pid, "p": pid,
                "arbeitsschein_id": "S%d" % (1 + n % 180),
                "taetigkeit": "Verteiler erweitern, Leitungen ziehen und "
                              "Endpruefung dokumentieren",
                "hours": 8 if t % 3 else 6.5,
                "stunden": 8 if t % 3 else 6.5,
                "von": "07:00", "bis": "16:00", "pause": 1,
                "gewerk": "Elektro", "gw": "Elektro",
                "bemerkung": "Anfahrt Krems - Zwettl gemeinsam",
            })
    return aus


ZEITEINTRAEGE = _eintraege()


def _abs():
    """Abwesenheiten je `<monteurId>_<datum>` - Form aus B12._abs12().

    M5 bekommt weiterhin KEINE (Koeder K14). Alle neun Aktiven bekommen
    welche, sonst zeigt die Abwesenheitsmatrix neun leere Zeilen und die
    Messung der kleinen Beschriftungen laeuft an einer Zeile statt an neun.
    """
    a = dict(B12._abs12())
    arten = ["urlaub", "krank", "zeitausgleich", "feiertag", "sonstige"]
    zustand = ["genehmigt", "offen", "abgelehnt"]
    for k, mid in enumerate(AKTIVE):
        for t in range(4):
            tag = B12._iso_vor(3 + k * 2 + t * 7)[:10]
            a["%s_%s" % (mid, tag)] = {"type": arten[(k + t) % len(arten)],
                                       "status": zustand[(k + t) % 3],
                                       "worker": mid}
    return a


def _absApprovals():
    aus = [dict(x) for x in B12._absApprovals12()]
    arten = ["urlaub", "zeitausgleich", "krank", "sonstige"]
    for k, mid in enumerate(AKTIVE):
        aus.append({"id": "AA%d" % (k + 10), "worker": mid,
                    "von": B12._iso_vor(-(5 + k * 3))[:10],
                    "bis": B12._iso_vor(-(2 + k * 3))[:10],
                    "type": arten[k % len(arten)],
                    "status": "offen" if k % 2 else "genehmigt",
                    "tage": 1 + k % 5,
                    "eingereicht": B12._iso_vor(1 + k)[:10]})
    return aus


def _stundenzettel():
    aus = [dict(x) for x in B12._stundenzettel12()]
    for k, mid in enumerate(AKTIVE):
        for monat in ("2026-07", "2026-08"):
            aus.append({"id": "SZ%s%s" % (mid, monat[-2:]), "worker": mid,
                        "monat": monat,
                        "status": ["offen", "freigegeben", "abgerechnet"][k % 3],
                        "stundenApp": 160.0 + k * 2.5,
                        "stundenFink": 160.0 + k * 2.5 - (1.5 if k % 4 else 0)})
    return aus


def _urlaubskontingent():
    aus = dict(B12._urlaubskontingent12())
    for k, mid in enumerate(AKTIVE):
        aus[mid] = {"jahr": 2026, "anspruch": 25 + (5 if k % 3 == 0 else 0),
                    "verbraucht": 2 + (k * 3) % 21}
    return aus


# ══════════════════════════════════════════════════════════════════════════
# Die vollstaendige Saat
# ══════════════════════════════════════════════════════════════════════════
def saat():
    """Genau die Speicherform von B12._saat12(), nur in echten Mengen."""
    return {"monteure": MONTEURE,
            "arbeitsscheine": ARBEITSSCHEINE,
            "projects": PROJEKTE,
            "entries": ZEITEINTRAEGE,
            "werkzeuge": WERKZEUGE,
            "planData": S._plandaten(),
            "forms": S._formulare(),
            "fahrzeuge": FAHRZEUGE,
            "abs": _abs(),
            "absApprovals": _absApprovals(),
            "stundenzettel": _stundenzettel(),
            "urlaubskontingent": _urlaubskontingent()}


def saat_leer():
    """Die LEERE Saat - der Koeder fuer die Mindestmengen-Pruefung.

    Ein Melder, der ZAEHLT, wird beim eigenen Ausfall gruen. Die Frage „ist
    die Grundgesamtheit gross genug?" braucht deshalb einen Fall, bei dem die
    Antwort NEIN ist und der Melder das sagen MUSS. Genau den liefert diese
    Funktion. Die Gegenprobe ist `saat()`: dort darf kein Verstoss stehen.
    """
    return {"monteure": [], "arbeitsscheine": [], "projects": [],
            "entries": [], "werkzeuge": [], "fahrzeuge": [],
            "abs": {}, "absApprovals": [], "stundenzettel": [],
            "urlaubskontingent": {}}


def saat_duenn():
    """Die ALTE Saat der Sondengruppe 12-15 - drei bis fuenf Monteure.

    Der zweite Koeder: die Mindestmengen-Pruefung muss auch DIESE Saat als
    nicht aussagekraeftig melden, denn genau mit ihr ist v3.9.954 gemessen
    worden. Faengt der Melder nur die leere Saat, dann prueft er auf
    „ueberhaupt Daten" und nicht auf „genug Daten" - und das ist ein anderer
    Melder als der behauptete.
    """
    return B12._saat12()


def mengen_aus_saat(daten):
    """Die Ist-Zahlen einer Saat, wie die Pruefung sie sehen wuerde."""
    m = daten.get("monteure") or []
    return {
        "monteure": len(m),
        "monteure_aktiv": len([x for x in m if not x.get("austritt")]),
        "monteure_ausgetreten": len([x for x in m if x.get("austritt")]),
        "fahrzeuge": len(daten.get("fahrzeuge") or []),
        "werkzeuge": len(daten.get("werkzeuge") or []),
        "arbeitsscheine": len(daten.get("arbeitsscheine") or []),
        "projects": len(daten.get("projects") or []),
    }


def mindestmenge_pruefen(ist):
    """Gibt die Liste der Verletzungen zurueck. LEER heisst aussagekraeftig.

    `ist` ist entweder eine Saat (dict mit Speichern) oder schon das Ergebnis
    von `mengen_aus_saat`.
    """
    if "monteure_aktiv" not in ist:
        ist = mengen_aus_saat(ist)
    verstoss = []
    for name, soll in sorted(MINDEST.items()):
        habe = ist.get(name, 0)
        if habe < soll:
            verstoss.append("%s: %d von mindestens %d" % (name, habe, soll))
    return verstoss


# Das Saatwort muss nach dem Neuladen in IRGENDEINER Ansicht auftauchen.
# Die vorhandene Regel aus B.SAATWORT bleibt gueltig; die neuen Marken kommen
# dazu, damit auch die neuen Namen als Nachweis taugen.
import re  # noqa: E402

SAATMARKEN = ["Steinbichler", "Steinberger", "Hinterleitner", "Hinterhuber",
              "Pfeiffenberger-Dollinger", "Brandstetter-Hollenstein",
              "Wieshofer-Prandtner", "Grubmueller", "Tauchner",
              "Aschenbrenner", "Steiner Landstra", "Hilti", "Fluke",
              "Guenzburger", "Rothenberger", "Weidmueller", "NOEWOG",
              "Muehlbachgasse", "AS-24", "GU-", "PA2439", "PA24"]
SAATWORT = re.compile("|".join(re.escape(x) for x in SAATMARKEN))


def marken_im_text(text):
    """Wieviele VERSCHIEDENE Saatmarken stehen in diesem Text?

    Verschiedene, nicht Treffer: 40 Mal „Hilti" ist eine Marke und belegt
    nicht, dass die Ansicht einen Bestand zeigt.
    """
    t = text or ""
    return sorted(set(mk for mk in SAATMARKEN if mk in t))


def _selbstprobe():
    """Belegt die Behauptungen dieser Datei, statt sie zu behaupten."""
    fehler = []
    ist = mengen_aus_saat(saat())
    for name, soll in sorted(MINDEST.items()):
        if ist.get(name, 0) < soll:
            fehler.append("volle Saat verletzt %s: %d < %d"
                          % (name, ist.get(name, 0), soll))
    # Koeder 1: leere Saat MUSS auffallen.
    v_leer = mindestmenge_pruefen(saat_leer())
    if len(v_leer) < len(MINDEST):
        fehler.append("KOEDER LEER STUMM: nur %d von %d Mindestmengen "
                      "gemeldet" % (len(v_leer), len(MINDEST)))
    # Koeder 2: die ALTE, duenne Saat MUSS ebenfalls auffallen - sonst prueft
    # der Melder auf „ueberhaupt Daten" statt auf „genug Daten".
    v_duenn = mindestmenge_pruefen(saat_duenn())
    if not v_duenn:
        fehler.append("KOEDER DUENN STUMM: die alte Saat aus v3.9.954 gilt "
                      "als aussagekraeftig - der Melder prueft nicht auf "
                      "Menge, sondern nur auf Anwesenheit")
    # Gegenprobe: die volle Saat darf NICHT gemeldet werden.
    v_voll = mindestmenge_pruefen(saat())
    if v_voll:
        fehler.append("GEGENPROBE ROT: die volle Saat wird als zu duenn "
                      "gemeldet (%s)" % "; ".join(v_voll))
    # Namensforderungen
    namen = [m["n"].split()[-1] for m in MONTEURE]
    for a, b in VERWECHSLUNGSPAARE:
        if a[:6] != b[:6]:
            fehler.append("Paar %s/%s teilt keine sechs Zeichen" % (a, b))
        for x in (a, b):
            if not any(x in n for n in namen):
                fehler.append("Name %s fehlt in der Saat" % x)
    lang = [n for n in namen if len(n) >= 19]
    if len(lang) < 3:
        fehler.append("zu wenige lange Nachnamen: %s" % lang)
    return fehler, ist, v_leer, v_duenn


if __name__ == "__main__":
    fehler, ist, v_leer, v_duenn = _selbstprobe()
    print("Saatmengen:")
    for k, v in sorted(ist.items()):
        print("  %-22s %5d   (mindestens %s)" % (k, v, MINDEST.get(k, "-")))
    print("\nKoeder 1 (leere Saat)  -> %d Verstoesse gemeldet" % len(v_leer))
    for x in v_leer:
        print("    " + x)
    print("Koeder 2 (alte Saat v3.9.954) -> %d Verstoesse gemeldet"
          % len(v_duenn))
    for x in v_duenn:
        print("    " + x)
    print("Gegenprobe (volle Saat) -> %d Verstoesse (muss 0 sein)"
          % len(mindestmenge_pruefen(saat())))
    print("\nVerwechslungspaare: %s" % VERWECHSLUNGSPAARE)
    print("Lange Nachnamen:    %s" % LANGE_NAMEN)
    if fehler:
        print("\n🔴 SELBSTPROBE ROT:")
        for f in fehler:
            print("   " + f)
        sys.exit(1)
    print("\nSelbstprobe gruen.")
