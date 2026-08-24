"""
v3.9.865 — DAS war der gemeldete Wisch-Fehler: eine Zeitschranke.

Der User meldete ueber mehrere Versionen hinweg "wischen geht nicht". v825/834/836
haben je eine echte Ursache behoben, den gemeldeten Fall aber nicht getroffen.
Grund fuer das dreimalige Danebenliegen: gemessen wurde immer mit synthetischen
`dispatchEvent`-Gesten. Die beweisen die VERDRAHTUNG, nie die GESTE — der
Playwright-Kontext hatte `hasTouch=false`, es konnte gar keine echte Geste
entstehen.

Mit echter Touch-Eingabe (CDP Input.dispatchTouchEvent im hasTouch-Kontext,
390px Hochformat, Live-Stand) faellt es sofort auf. Eine kerzengerade Geste,
dx=-150 dy=0, also weit genug und schnurgerade:

    dt = 602 ms  -> zaehlt
    dt = 833 ms  -> VERWORFEN
    dt = 917 ms  -> VERWORFEN
    dt = 1242 ms -> VERWORFEN

Auf ALLEN 18 Tabs identisch: "zuegig 200px/300ms" geht ueberall, "langsam
120px/650ms" geht nirgends. Also kein Seiten- und kein Skip-Listen-Problem,
sondern die Schranke selbst. Wer bedaechtig wischt — Handschuhe, Baustelle,
Handy einhaendig — braucht 0,8 bis 1,5 s.

Fix: dt-Schranke 800 -> 2500 ms; Richtungs-Toleranz 0.6 -> 1.0 fuer den
natuerlichen Daumenbogen (horizontale Dominanz bleibt gefordert);
Mindestweg |dx| >= 70 UNVERAENDERT — der trennt Wisch von Tap.

Die Dauer ist ohnehin das schwaechste der drei Kriterien: was eine Wisch-Geste
ausmacht, sind Weg und Richtung, nicht Tempo.
"""
import re


def _schranke(index_html):
    m = re.search(r"if\(dt>(\d+)\|\|Math\.abs\(dx\)<(\d+)\|\|"
                  r"Math\.abs\(dy\)>Math\.abs\(dx\)\*([\d.]+)\)return;", index_html)
    assert m, "Die Wisch-Schranke in useSwipe.onTouchEnd ist nicht mehr auffindbar"
    return {"dt": int(m.group(1)), "dx": int(m.group(2)), "ratio": float(m.group(3))}


def test_dauer_schranke_laesst_bedaechtige_gesten_zu(index_html):
    s = _schranke(index_html)
    assert s["dt"] >= 2000, (
        f"dt-Schranke ist {s['dt']} ms. Real gemessene, kerzengerade Gesten "
        f"brauchten 833/917/1242 ms und wurden bei 800 ms alle verworfen. "
        f"Unter ~2000 ms faellt der bedaechtige Wisch wieder durch."
    )


def test_die_real_gemessenen_gesten_wuerden_jetzt_zaehlen(index_html):
    """Die vier echt gemessenen Gesten gegen die Schranke rechnen — der Test
    prueft die WIRKUNG, nicht nur die Zahl."""
    s = _schranke(index_html)
    gemessen = [
        {"name": "zuegig", "dx": -200, "dy": 0, "dt": 602},
        {"name": "mittel", "dx": -150, "dy": 0, "dt": 833},
        {"name": "langsam", "dx": -120, "dy": 0, "dt": 917},
        {"name": "sehr langsam", "dx": -150, "dy": 0, "dt": 1242},
    ]
    for g in gemessen:
        verworfen = (g["dt"] > s["dt"]
                     or abs(g["dx"]) < s["dx"]
                     or abs(g["dy"]) > abs(g["dx"]) * s["ratio"])
        assert not verworfen, (
            f"Die real gemessene Geste '{g['name']}' (dx={g['dx']}, dy={g['dy']}, "
            f"dt={g['dt']}) wuerde wieder verworfen."
        )


def test_daumenbogen_wird_akzeptiert(index_html):
    """Ein echter Daumen zieht einen Bogen. Bei 0.6 fiel dy=60 auf dx=-130
    knapp durch (60 > 78? nein — aber dy=90 waere durchgefallen); mit 1.0 ist
    verlangt, dass die Bewegung horizontal DOMINIERT, nicht dass sie gerade ist."""
    s = _schranke(index_html)
    assert s["ratio"] >= 1.0, (
        f"Richtungs-Toleranz ist {s['ratio']} — der natuerliche Daumenbogen "
        f"faellt damit teilweise durch."
    )
    dx, dy = -130, 90
    assert not (abs(dy) > abs(dx) * s["ratio"]), "Bogen dy=90 auf dx=-130 faellt durch"


def test_mindestweg_bleibt_scharf(index_html):
    """|dx|>=70 ist der Riegel zwischen Wisch und Tap/Wackler — der darf durch
    die Lockerung NICHT mitaufgeweicht werden."""
    s = _schranke(index_html)
    assert s["dx"] == 70, f"Mindestweg ist {s['dx']} statt 70"
    assert abs(-55) < s["dx"], "Ein 55px-Wackler wuerde als Wisch zaehlen"


def test_vertikales_scrollen_gilt_weiter_nicht_als_wisch(index_html):
    """Gegenprobe zur gelockerten Toleranz: eine ueberwiegend vertikale
    Bewegung darf keinen Tab wechseln, sonst wechselt Scrollen die Seite."""
    s = _schranke(index_html)
    for dx, dy in [(-80, 200), (-100, 140), (-20, 300)]:
        verworfen = (abs(dx) < s["dx"] or abs(dy) > abs(dx) * s["ratio"])
        assert verworfen, (
            f"Vertikale Bewegung dx={dx}, dy={dy} wuerde einen Tab-Wechsel "
            f"ausloesen — Scrollen wuerde die Seite wechseln."
        )


def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    """Umkehrprobe: alte Schranke rekonstruieren, die Riegel muessen ROT werden."""
    alt = re.sub(r"if\(dt>\d+\|\|Math\.abs\(dx\)<70\|\|Math\.abs\(dy\)>Math\.abs\(dx\)\*[\d.]+\)return;",
                 "if(dt>800||Math.abs(dx)<70||Math.abs(dy)>Math.abs(dx)*0.6)return;",
                 index_html, count=1)
    assert alt != index_html, "Rueckbau griff nicht — Anker veraltet"
    s = _schranke(alt)
    assert s["dt"] == 800 and s["ratio"] == 0.6, "Umkehrprobe: Rueckbau unvollstaendig"
    # und die real gemessene 917ms-Geste faellt damit wieder durch:
    assert 917 > s["dt"], "Umkehrprobe: der Dauer-Riegel wuerde nicht anschlagen"
    assert 90 > 130 * s["ratio"], "Umkehrprobe: der Bogen-Riegel wuerde nicht anschlagen"
