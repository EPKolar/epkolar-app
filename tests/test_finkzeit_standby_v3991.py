"""v3.9.114 — FINKZEIT STANDBY (Sebastian-Entscheidung 04.06.2026).

Alles FinkZeit-bezogene im Frontend hinter EINEM zentralen Flag geparkt (Code NICHT gelöscht).
Reaktivierung: FINKZEIT_ENABLED = true. DB/Schema unberührt. hasPerm('stunden') unverändert.

!!! WARNMARKE - DIESE DATEI ZAEHLT BEWUSST ROH (v3.9.922) !!!
Der Begriff "FINKZEIT STANDBY" steht 9x in KOMMENTAREN und 0x im Code.
Wer diese Datei bei einem Kommentarblind-Durchgang mitnimmt, misst 0 - und
darf die Erwartung dann NICHT "nachziehen": eine auf 0 nachgezogene Zahl
misst gar nichts mehr. Die Marke IST Dokumentation, sie gehoert in den
Rohtext. `test_standby_marken_stehen_an_ihren_flaechen` haelt das fest und
prueft die 0 im Code ausdruecklich mit.
"""
import re

from conftest import _extract_fn
from _hilfen import nur_code


def test_flag_exists_and_enabled(index_html):
    # v3.9.204: Monatsabrechnung reaktiviert (Chef-Entscheidung 09.06.2026) — Flag jetzt true.
    assert "const FINKZEIT_ENABLED=true;" in index_html, (
        "Zentrales Flag FINKZEIT_ENABLED muss existieren und true sein (reaktiviert v3.9.204)"
    )


def test_flag_gates_all_surfaces(index_html):
    # Jede FinkZeit-Frontend-Fläche muss das Flag referenzieren:
    gates = [
        # Tab Monatsabrechnung (Tab-Definition spread-conditional)
        '...(FINKZEIT_ENABLED?[{l:"Monatsabrechnung"',
        # mobile _navIds
        '...(FINKZEIT_ENABLED?["stunden"]:[])',
        # Dashboard finkStats-Fetch
        "if(!FINKZEIT_ENABLED)return;",
        # Dashboard-Alerts
        "if(FINKZEIT_ENABLED&&finkStats.offen>0",
        "if(FINKZEIT_ENABLED&&finkStats.diffWarn>0",
        # Dashboard-Card
        'FINKZEIT_ENABLED&&hasPerm(curUser,"stunden")&&',
        # Audit-Filter-Option
        'FINKZEIT_ENABLED&&React.createElement(\'option\', { value: "approve_finkzeit"}',
        # Rechteverwaltung: stunden-Toggle ausgeblendet
        'filter(([_pdm])=>FINKZEIT_ENABLED||_pdm!=="stunden")',
        # Chef-Hinweis
        "if(!FINKZEIT_ENABLED){if(alive)setFinkOpen([]);return;}",
    ]
    for g in gates:
        assert g in index_html, f"FinkZeit-Gate fehlt: {g}"


def test_code_parked_not_deleted(index_html):
    # Die Handler/Logik bleiben im Code erhalten (parken, nicht löschen):
    for kept in ['"/api/finkzeit"', "pdf_data", "function StundenzettelView(",
                 'stunden:"Monatsabrechnung einsehen & freigeben"']:
        assert kept in index_html, f"Geparkter FinkZeit-Code darf NICHT gelöscht sein: {kept}"


def test_hasperm_stunden_still_clean(index_html):
    # 'stunden' bleibt in den ROLES-Modulen (hasPerm liefert weiter sauber true/false)
    m = re.search(r'admin:\{l:"Administrator"[^\n]*?modules:\[([^\]]*)\]', index_html)
    assert m and '"stunden"' in m.group(1), "ROLES.admin.modules muss 'stunden' behalten (hasPerm unverändert)"


# ---------------------------------------------------------------------------
# BENANNTE FLAECHEN STATT GESAMTZAHL (v3.9.922)
#
# Vorher: `index_html.count("FINKZEIT STANDBY") >= 6`, ROH. Der Riegel hat
# gemessen, wie oft ein ERKLAERTEXT ein Wort nennt - eine Zahl ueber die ganze
# Datei, die beim Tausch gruen bleibt: verschwinden die Marken aus dem
# ChefDashboard und kommen dafuer zwei neue in einem einzigen Kommentarblock
# dazu, aendert sich an der 9 nichts.
#
# Jetzt benannt: JEDE geparkte FinkZeit-Flaeche traegt IHRE eigene Marke.
# Gemessen 30.08.2026 - 9 Marken roh, davon 6 in vier Komponenten-Rumpfen
# (AdminPanel 2, HomeView 2, StundenzettelView 1, ChefDashboard 1); die
# restlichen drei haengen an top-level-Definitionen (Datei-Kopf, mobile
# _navIds, Tab-Eintrag), die `test_flag_gates_all_surfaces` oben schon
# NAMENTLICH pinnt - sie brauchen hier keine zweite Rechnung.
#
# Geprueft wird "mindestens EINE Marke je Flaeche", nicht die genaue Zahl je
# Flaeche: es ist Dokumentation, und ein Riegel, der die Zahl der Kommentare
# festschreibt, misst die Schreibweise (tests/_hilfen.py).
# ---------------------------------------------------------------------------
_MARKE = "FINKZEIT STANDBY"
_GEMARKTE_FLAECHEN = ("AdminPanel", "HomeView", "StundenzettelView", "ChefDashboard")


def _marken_mangel(roh):
    """Flaechen ohne Standby-Marke. Leere Liste = gruen."""
    aus = []
    for flaeche in _GEMARKTE_FLAECHEN:
        region = _extract_fn(roh, flaeche)
        if not region:
            aus.append("Flaeche %s nicht gefunden" % flaeche)
        elif region.count(_MARKE) < 1:
            aus.append("%s traegt keine %r-Marke mehr" % (flaeche, _MARKE))
    return aus


def test_standby_marken_stehen_an_ihren_flaechen(index_html):
    assert _marken_mangel(index_html) == []
    # DIE WARNMARKE ALS RIEGEL: die Marke ist Dokumentation und steht 0x im
    # Code. Wer diesen Riegel kommentarblind machen will, sieht hier, dass 0
    # der ERWARTETE Wert ist - und zieht oben nichts "nach".
    assert nur_code(index_html).count(_MARKE) == 0, (
        "%r steht jetzt im CODE. Dann ist es keine Standby-Marke mehr, "
        "sondern ein Bezeichner - und dieser Riegel misst etwas anderes "
        "als er soll." % (_MARKE,)
    )


def test_umkehrprobe_marke_faellt_weg_wird_rot(index_html):
    """DER GRUND DER UMSTELLUNG. Die Marke verschwindet NUR im ChefDashboard:
    roh bleiben 8 Vorkommen, das alte `>= 6` WAERE gruen geblieben."""
    region = _extract_fn(index_html, "ChefDashboard")
    kaputt = index_html.replace(region, region.replace(_MARKE, "(entfernt)"), 1)
    assert kaputt.count(_MARKE) >= 6, (
        "Vorbedingung der Probe: die alte Zahl MUSS erreicht bleiben - sonst "
        "zeigt die Probe nicht, was sie zeigen soll"
    )
    assert any(s.startswith("ChefDashboard") for s in _marken_mangel(kaputt)), \
        "Der Wegfall im ChefDashboard bleibt unbemerkt"


def test_umkehrprobe_tausch_wird_rot(index_html):
    """Tausch: die Marken des AdminPanel wandern in einen einzigen neuen
    Kommentarblock am Dateiende. Gesamtzahl unveraendert - trotzdem rot."""
    region = _extract_fn(index_html, "AdminPanel")
    ohne = region.replace(_MARKE, "(entfernt)")
    kaputt = (index_html.replace(region, ohne, 1) + chr(10)
              + "/* %s %s */" % (_MARKE, _MARKE))
    assert kaputt.count(_MARKE) == index_html.count(_MARKE), \
        "Vorbedingung: die Gesamtzahl MUSS beim Tausch gleich bleiben"
    assert any(s.startswith("AdminPanel") for s in _marken_mangel(kaputt)), \
        "Der Tausch wird nicht bemerkt - der Riegel zaehlt wieder nur Woerter"

