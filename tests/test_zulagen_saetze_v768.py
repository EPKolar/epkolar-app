# -*- coding: utf-8 -*-
"""v3.9.768 — Zulagen-Sätze auf Lohnzettel-Wahrheit + Label „Taggeld" → „Entfernungszulage".

Quelle ist NICHT mehr der KV-Fallback-Schätzwert, sondern der echte Lohnzettel (Lohnverrechner
ist maßgeblich):
  · LA 2740 „Entfernungszl.kl.fr."   11,71 € (steuerfrei §26)  — vorher 11,94 €
  · LA 4060 „Montagezulage pfl."      1,13 €/h (steuerpflichtig) — vorher 1,155 €/h

2027 ist BEWUSST nicht hinterlegt (nichts erfunden) → ein Tag in 2027 fällt über
_kvMontagezulageSatz auf montagezulageStd (1,13) zurück, bis der Lohnverrechner liefert.

Label: alle ANZEIGE-Strings heißen „Entfernungszulage"; die KV_RULES-FELDNAMEN bleiben
`taggeld*` — sie liegen in system_config.kv_rules persistiert, ein Umbenennen bräuchte eine
Migration und würde bei Altbestand still auf die Fallback-Sätze zurückfallen. Genau das pinnt
test_feldnamen_unveraendert.
"""
import re
import subprocess


def _fn(index_html, name):
    m = re.search(r"(?:async )?function " + name + r"\(.*?\n\}", index_html, re.S)
    assert m, name + " nicht gefunden"
    return m.group(0)


def _node(tmp_path, js, name="zul.js"):
    f = tmp_path / name
    f.write_text(js, encoding="utf-8")
    r = subprocess.run(["node", str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    return r.stdout.strip().splitlines()[-1]


# ================================================================ Sätze (statisch)

def test_saetze_im_fallback(index_html):
    assert "taggeldAb6h:11.71," in index_html, "Entfernungszulage-Satz nicht auf 11,71 (Lohnzettel LA 2740)"
    assert "montagezulageStd:1.13," in index_html, "Montagezulage-Fallback nicht auf 1,13 (Lohnzettel LA 4060)"
    assert "montagezulage:{2026:1.13}," in index_html, "Montagezulage-Jahressatz 2026 nicht auf 1,13"
    assert "taggeldAb6h:11.94" not in index_html, "alter Satz 11,94 noch vorhanden"
    assert "montagezulageStd:1.155" not in index_html, "alter Satz 1,155 noch vorhanden"


def test_2027_nicht_erfunden(index_html):
    """Der Lohnzettel belegt nur 2026 — 2027 darf NICHT geraten werden."""
    # Nur der WIRKSAME Block zaehlt. Die APP_VERSION-Kommentarketten nennen die historischen
    # Werte (2026:1.155, 2027:1.178) als Prosa — das ist Changelog, kein aktiver Satz.
    start = index_html.index("const KV_RULES_FALLBACK={")
    block = index_html[start:index_html.index("\n};", start)]
    # Auf den SCHLUESSEL pruefen, nicht auf das Wort — der Erklaertext im Block nennt 2027
    # bewusst als offenen Lohnverrechner-Pruefpunkt.
    assert not re.search(r"2027\s*:", block), \
        "2027 ist als Satz-Schluessel hinterlegt, obwohl der Lohnzettel nur 2026 belegt"
    m = re.search(r"montagezulage:\{([^}]*)\}", block)
    assert m, "montagezulage-Map nicht gefunden"
    assert m.group(1).strip() == "2026:1.13", \
        "Satz-Map ist nicht exakt {2026:1.13} — bekommen: " + m.group(1)


def test_beleg_im_kommentar(index_html):
    assert "LA 2740" in index_html, "Beleg-Kommentar LA 2740 fehlt"
    assert "LA 4060" in index_html, "Beleg-Kommentar LA 4060 fehlt"


# ================================================================ Rechnung (node-eval)

def test_montagezulage_tag_mal_113(index_html, tmp_path):
    js = _fn(index_html, "_kvMontagezulageSatz") + "\n" + _fn(index_html, "_kvMontagezulageTag") + """
var out=[];
out.push(_kvMontagezulageTag(8.5,'2026-06-15',{},true));   // 8,5 x 1,13
out.push(_kvMontagezulageTag(167,'2026-06-15',{},true));   // Lohnzettel-Gegenrechnung
out.push(_kvMontagezulageTag(8.5,'2027-01-15',{},true));   // 2027 unbelegt -> Fallback 1,13
out.push(_kvMontagezulageTag(8.5,'2026-06-15',{},false));  // ohne Flag -> 0
console.log(JSON.stringify(out.map(function(x){return Math.round(x*1000)/1000;})));
"""
    got = _node(tmp_path, js, "mz.js")
    assert got == "[9.605,188.71,9.605,0]", (
        "Montagezulage rechnet nicht Std x 1,13. Erwartet 8,5h=9,605 EUR, 167h=188,71 EUR "
        "(Lohnzettel-Gegenrechnung), 2027=Fallback 9,605, ohne Flag 0. Bekommen: " + got)


def test_entfernungszulage_menge_mal_1171(index_html, tmp_path):
    js = _fn(index_html, "_kvTaggeldTag") + "\n" + _fn(index_html, "_kvMontagezulage") + "\n" \
         + _fn(index_html, "_kvZulagenMonat") + """
var out=[];
out.push(_kvTaggeldTag(7.5,{}));   // >6h  -> 11,71
out.push(_kvTaggeldTag(6.0,{}));   // exakt 6h -> 0 (strikt >6)
out.push(_kvTaggeldTag(0,{}));     // kein Tag -> 0
// Menge x Satz: 16 qualifizierte Tage (Riedmann Juni 2026, real: 16 Tage >6h, kein Tag >11h)
var tage=[];for(var i=0;i<16;i++)tage.push(7.5);
var z=_kvZulagenMonat(tage,0,{});
out.push(Math.round(z.taggeldSum*100)/100);
out.push(z.tage6);
out.push(z.tage11);
console.log(JSON.stringify(out));
"""
    got = _node(tmp_path, js, "ez.js")
    assert got == "[11.71,0,0,187.36,16,0]", (
        "Entfernungszulage rechnet nicht Menge x 11,71. Erwartet Tag=11,71, 6,0h=0, "
        "16 Tage=187,36 EUR (Lohnzettel-Gegenrechnung), tage6=16, tage11=0. Bekommen: " + got)


# ================================================================ Label

def test_anzeige_heisst_entfernungszulage(index_html):
    assert "'💶 Zulagen — Entfernungszulage & Montagezulage'" in index_html, "Report-Titel nicht umbenannt"
    assert "'Entfernungszulage EUR'" in index_html, "CSV-Header nicht umbenannt (geht an den Lohnverrechner)"
    assert "'Monteur','Tage >6h','Tage >11h','Entfernungszulage'" in index_html, "Spaltenkopf nicht umbenannt"
    assert "'Entfernungszulage ab 6h'" in index_html, "Admin-Label nicht umbenannt"


def test_keine_taggeld_anzeige_mehr(index_html):
    """Kein Anzeige-String darf noch 'Taggeld' sagen (Kommentare/Feldnamen sind erlaubt)."""
    zeilen = index_html.split("\n")
    treffer = []
    for i, z in enumerate(zeilen, 1):
        roh = z.strip()
        # APP_VERSION-Kommentarkette per INHALT ausnehmen, nicht per Zeilennummer — die
        # verschiebt sich bei jeder Aenderung oberhalb (ist beim v768-Bump passiert).
        if "const APP_VERSION=" in z or roh.startswith("/*") or roh.startswith("*") or roh.startswith("//"):
            continue  # Kommentare: "Taggeld" als Prosa erlaubt, nur Anzeige-Strings zaehlen
        for m in re.finditer(r"'([^']*Taggeld[^']*)'|\"([^\"]*Taggeld[^\"]*)\"", z):
            treffer.append((i, m.group(0)[:60]))
    assert not treffer, "Anzeige-Strings mit 'Taggeld' uebrig: " + str(treffer[:5])


def test_feldnamen_unveraendert(index_html):
    """Variante B abgelehnt: Feldnamen NICHT umbenennen (sonst Migration + Fallback-Risiko)."""
    for feld in ("taggeldAb6h", "taggeldAb11h", "taggeldNacht", "montagezulageStd"):
        assert feld in index_html, "Feldname " + feld + " wurde umbenannt — das braeuchte eine Datenmigration"


def test_tote_stufen_markiert(index_html):
    """P2/Punkt 3: Naechtigung bleibt als toter Zweig, ist aber im Admin-UI als ohne Funktion markiert."""
    assert "taggeldNacht:62.04" in index_html, "Naechtigungs-Satz entfernt — sollte stehen bleiben"
    assert index_html.count("ohne Funktion (EP Kolar: keine Nächtigung)") >= 2, \
        "tote Stufen (ab 11h / Nacht) nicht als ohne Funktion gekennzeichnet"


# ================================================================ Vorschau-Warnung

def test_vorschau_hinweis_vorhanden(index_html):
    assert "⚠ VORSCHAU — der Lohnverrechner ist maßgeblich" in index_html, \
        "Vorschau-Warnung im Report fehlt"
    assert "167 h vs. Zeiteinträge 158 h" in index_html, \
        "offener Mengen-Pruefpunkt nicht im Hinweis benannt"
    assert index_html.count("⚠ Vorschau — Lohnverrechner maßgeblich") >= 2, \
        "Vorschau-Vermerk fehlt in der Vergabe-UI (mobil + Desktop)"
