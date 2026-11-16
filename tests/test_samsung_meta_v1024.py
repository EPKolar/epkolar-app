# -*- coding: utf-8 -*-
"""v3.9.1024 Samsung-Hell, zweiter Anlauf.

Gemessen am A55 (16.11.): App "Hell" + Handy-Nachtmodus -> Hintergrund 28,30,28. Bis v1023 stand
im color-scheme-Meta und an der Wurzel "only light" - ohne Wirkung. Samsung Internet laesst laut
Samsung-Forum nur Seiten unangetastet, die per color-scheme-META eigenes Dunkel erklaeren.

Jetzt: das Meta bleibt STATISCH "light dark" (Signal an Samsung), die Wurzel traegt weiter
only light/only dark (Darstellung = allein die App-Wahl). Dazu ein Hinweis in Einstellungen >
Darstellung, nur in Samsung Internet und nur bei Wahl Hell - die Zwangsabdunkelung ist per Skript
nicht messbar (sie passiert beim Zeichnen).
"""
import re
import shutil
import subprocess

import pytest

from _hilfen import nur_code

META = '<meta name="color-scheme" content="light dark">'


def _kopf_skript(src):
    j = src.find("<script>", src.find(META)) + len("<script>")
    return src[j:src.find("</script>", j)]


def _meta_schreiber(code):
    return re.findall(r'meta\[name=color-scheme\]"\)[^;]*;\s*if\([^)]*\)[^;]*setAttribute\(', code)


def test_meta_steht_statisch_und_einmal(index_html):
    assert index_html.count(META) == 1
    assert index_html.index(META) < index_html.index("<script")


def test_niemand_schreibt_das_meta_um(index_html):
    code = nur_code(index_html)
    assert _meta_schreiber(code) == []
    # Umkehrprobe: der alte v1023-Schreiber wird erkannt
    alt = code + ';var _csm=document.querySelector("meta[name=color-scheme]");if(_csm)_csm.setAttribute("content","only light");'
    assert len(_meta_schreiber(alt)) == 1


def test_wurzel_folgt_weiter_der_app_wahl(index_html):
    kopf = _kopf_skript(index_html)
    assert 'var cs=d?"only dark":"only light";' in kopf
    assert "document.documentElement.style.colorScheme=cs;" in kopf
    assert 'document.documentElement.style.colorScheme=dark?"only dark":"only light";' in index_html


@pytest.mark.skipif(shutil.which("node") is None, reason="node fehlt")
@pytest.mark.parametrize("gespeichert,erwartet", [
    (None, "only light"), ("light", "only light"), ("system", "only light"), ("dark", "only dark"),
])
def test_kopfskript_meta_bleibt_wurzel_folgt(index_html, gespeichert, erwartet):
    js = (
        "var meta={c:'light dark',setAttribute:function(k,v){this.c=v;}};"
        "var document={querySelector:function(){return meta;},documentElement:{style:{},setAttribute:function(){}}};"
        "var localStorage={getItem:function(){return %s;}};"
        "var window={matchMedia:function(){return {matches:true};}};"
        % ("null" if gespeichert is None else "'%s'" % gespeichert)
        + _kopf_skript(index_html)
        + ";console.log(meta.c+'|'+document.documentElement.style.colorScheme);"
    )
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "light dark|" + erwartet


def _hinweis(code):
    i = code.find('className: "epk-samsung-hinweis"')
    assert i > 0, "Samsung-Hinweis fehlt"
    return code[i - 200:i + 900]


def test_hinweis_nur_samsung_nur_hell_mit_pfad(index_html):
    code = nur_code(index_html)
    assert code.count('className: "epk-samsung-hinweis"') == 1
    h = _hinweis(code)
    assert '!isDark&&/SamsungBrowser/.test(navigator.userAgent||"")&&' in h
    assert "Webseitenansicht und Bildlauf" in h and "Dark Mode für Webinhalt erzwingen" in h  # v3.9.1030: am A55 (Samsung Internet 30.0.5.27) abgelesener Wortlaut
    # der Hinweis liest nie die Geraete-Einstellung
    assert "prefers-color-scheme" not in h and "matchMedia" not in h
    # Umkehrprobe: ohne Bedingung waere er fuer alle sichtbar
    roh = code.replace('!isDark&&/SamsungBrowser/.test(navigator.userAgent||"")&&', "", 1)
    assert '!isDark&&/SamsungBrowser/' not in _hinweis(roh)


def test_hinweis_sitzt_in_der_darstellungs_karte(index_html):
    i = index_html.index('"Darstellung" )')
    j = index_html.index('"Offline-Fotosync"', i)
    assert i < index_html.index('className: "epk-samsung-hinweis"') < j
