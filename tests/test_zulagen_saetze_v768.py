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
    assert "taggeldAb6h:11.94" not in index_html, "alter Satz 11,94 noch vorhanden"


def test_beleg_im_kommentar(index_html):
    assert "LA 2740" in index_html, "Beleg-Kommentar LA 2740 fehlt"


# ================================================================ Rechnung (node-eval)

def test_entfernungszulage_menge_mal_1171(index_html, tmp_path):
    js = _fn(index_html, "_kvTaggeldTag") + "\n" \
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
    assert "'💶 Entfernungszulage'" in index_html, "Report-Titel nicht umbenannt"
    # v3.9.776: CSV-Export (mit Header 'Entfernungszulage EUR') durch PZE-PDF-Uebergabe ersetzt — Pin entfaellt.
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
    for feld in ("taggeldAb6h", "taggeldAb11h", "taggeldNacht"):
        assert feld in index_html, "Feldname " + feld + " wurde umbenannt — das braeuchte eine Datenmigration"


def test_tote_stufen_markiert(index_html):
    """P2/Punkt 3: Naechtigung bleibt als toter Zweig, ist aber im Admin-UI als ohne Funktion markiert."""
    assert "taggeldNacht:62.04" in index_html, "Naechtigungs-Satz entfernt — sollte stehen bleiben"
    assert index_html.count("ohne Funktion (EP Kolar: keine Nächtigung)") >= 2, \
        "tote Stufen (ab 11h / Nacht) nicht als ohne Funktion gekennzeichnet"


# ================================================================ Vorschau-Warnung

def test_vorschau_hinweis_vorhanden(index_html):
    # v3.9.775 Etappe 3: die Kalender-Vergabe ist jetzt LOHNRELEVANT (eff. Tage bestimmen die abgerechnete
    # Menge), darum ist der alte "keine Abrechnungsgrundlage"-Vermerk bewusst ersetzt.
    assert "Lohnverrechner maßgeblich" in index_html, "Vermerk Lohnverrechner-massgeblich fehlt"
    assert "Entfernungszulage — lohnrelevant" in index_html, "lohnrelevanter Vergabe-Hinweis fehlt"
