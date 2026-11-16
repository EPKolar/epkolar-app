# -*- coding: utf-8 -*-
"""v3.9.1006 (Sebastian): color-scheme folgt dem AKTIVEN App-Thema - "only light" / "only dark".

Samsung Internet faerbt eine Seite mit seinem Zwangs-Dunkel um, wenn sie ihr Schema nicht
erklaert; am A55 lief die App laut Speicher HELL und erschien trotzdem dunkel (v3.9.1005).
Das Meta wird darum (1) frueh im Kopf aus epk_theme gesetzt, bevor gerendert wird, und
(2) bei jedem Wechsel in applyTheme mitgezogen. Desktop-Bilder zeigen den Fehler nicht -
die Wirkung wird am Geraet geprueft.
"""
import pathlib
import shutil
import subprocess

import pytest

SRC = (pathlib.Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


def test_frueh_skript_steht_direkt_hinter_dem_meta_vor_allem_anderen():
    i = SRC.find('<meta name="color-scheme"')
    j = SRC.find("<script>", i)
    assert 0 < i < j and j - i < 80, "das Frueh-Skript muss unmittelbar nach dem Meta stehen"
    k = SRC.find("</script>", j)
    early = SRC[j:k]
    assert 'localStorage.getItem("epk_theme")' in early
    assert '"only dark":"only light"' in early
    assert 'setAttribute("content",cs)' in early
    assert "setItem" not in early, "das Frueh-Skript darf nichts schreiben"


def test_applyTheme_zieht_das_meta_mit():
    i = SRC.find('document.documentElement.style.colorScheme=dark?"only dark":"only light";')
    assert i > 0
    nach = SRC[i:i + 300]
    assert 'querySelector("meta[name=color-scheme]")' in nach
    assert '_csm.setAttribute("content",dark?"only dark":"only light")' in nach


@pytest.mark.skipif(shutil.which("node") is None, reason="node fehlt")
@pytest.mark.parametrize("gespeichert,system_dunkel,erwartet", [
    ("light", True, "only light"),   # der A55-Fall: App hell, System dunkel
    ("dark", False, "only dark"),
    # v3.9.1016 GF-Entscheidung: die App ignoriert die Betriebssystem-Einstellung -
    # ohne Wahl (oder mit altem "system") ist es hell, auch bei dunklem System.
    (None, True, "only light"),
    ("system", True, "only light"),
    (None, False, "only light"),
])
def test_frueh_skript_rechnet_richtig(gespeichert, system_dunkel, erwartet):
    j = SRC.find("<script>", SRC.find('<meta name="color-scheme"')) + len("<script>")
    early = SRC[j:SRC.find("</script>", j)]
    js = (
        "var meta={c:'light dark',setAttribute:function(k,v){this.c=v;}};"
        "var document={querySelector:function(){return meta;},documentElement:{style:{}}};"
        "var localStorage={getItem:function(){return %s;}};"
        "var window={matchMedia:function(){return {matches:%s};}};"
        % ("null" if gespeichert is None else "'%s'" % gespeichert, "true" if system_dunkel else "false")
        + early
        + ";console.log(meta.c+'|'+document.documentElement.style.colorScheme);"
    )
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == erwartet + "|" + erwartet
