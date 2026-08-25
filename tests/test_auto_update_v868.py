# -*- coding: utf-8 -*-
"""
v3.9.868 - Ein Fix, den niemand antippt, kommt nie an.

BEFUND (end-to-end nachgestellt, nicht vermutet): der Update-Weg FUNKTIONIERT.
Alter Stand laeuft mit aktivem Service Worker, ein Deploy passiert, der
Versions-Poll liest die neue APP_VERSION netzfrisch, erkennt den Mismatch und
zeigt den Banner; ein Tipp darauf laedt die neue Fassung. Gemessen:

    laeuft 3.9.866 -> Server hat 3.9.867 -> Banner -> Tipp -> laeuft 3.9.867

Genau da liegt das Problem: er verlangt einen Tipper. Am Bau tippt den keiner.
Monteure liefen auf alten Staenden weiter, waehrend hier Fix um Fix ausgeliefert
wurde und "geht immer noch nicht" zurueckkam.

FIX: Die App wendet ein bereitliegendes Update selbst an - aber nur, wenn
nachweislich nichts verloren gehen kann. ALLE VIER Bedingungen zusammen:
  1. Es liegt wirklich eine neuere Version bereit (der Poll hat sie gelesen).
  2. Die App kommt aus dem Hintergrund zurueck und war >= 2 Minuten weg.
  3. Niemand tippt gerade (kein Eingabefeld hat den Fokus).
  4. NIRGENDWO steht Text in einem Eingabefeld - ein halb ausgefuelltes
     Bautagebuch blockiert den Auto-Reload zuverlaessig.
Im Zweifel passiert nichts und der Banner bleibt: der Rueckfall ist immer der
bisherige, funktionierende Weg.

Diese Tests pinnen jede einzelne Bedingung. Faellt eine weg, kann die App einem
Monteur mitten in der Arbeit den Text wegreissen - deshalb sind es harte Riegel.
"""
import re


def _effekt(index_html):
    """Der Auto-Update-Effekt: vom Marker bis zur doSwUpdate-Deklaration."""
    i = index_html.find("v3.9.868: EIN FIX, DEN NIEMAND ANTIPPT")
    assert i != -1, "Der Auto-Update-Block ist weg."
    j = index_html.find("const doSwUpdate=async()", i)
    assert j != -1, "Ende des Blocks nicht gefunden"
    return index_html[i:j]


# -- Bedingung 1: es liegt wirklich eine neuere Version bereit ---------------

def test_poll_merkt_sich_die_server_version(index_html):
    assert "_neueVerRef.current=_serverVer;setSwUpdate(true);" in index_html, (
        "Der Poll legt die erkannte Server-Version nicht ab - dann weiss der "
        "Auto-Update-Pfad nicht, worauf er aktualisieren soll."
    )


def test_ohne_bereitliegende_version_passiert_nichts(index_html):
    block = _effekt(index_html)
    assert re.search(r"const ziel=_neueVerRef\.current;\s*if\(!ziel\)return;", block), (
        "Ohne gemerkte Zielversion muss der Pfad sofort aussteigen:\n" + block[:400]
    )


# -- Bedingung 2: mindestens 2 Minuten weg gewesen --------------------------

def test_nur_nach_laengerer_abwesenheit(index_html):
    block = _effekt(index_html)
    m = re.search(r"if\(weg<(\d+)\)return;", block)
    assert m, "Keine Mindest-Abwesenheit geprueft:\n" + block[:400]
    ms = int(m.group(1))
    assert ms >= 120000, (
        "Mindest-Abwesenheit ist nur %d ms. Wer die App kurz wegdreht - Foto "
        "machen, Anruf annehmen - steckt womoeglich mitten in einer Eingabe." % ms
    )


def test_versteckt_zeitpunkt_wird_gesetzt(index_html):
    block = _effekt(index_html)
    assert "if(document.visibilityState==='hidden'){_verstecktSeitRef.current=Date.now();return;}" in block, (
        "Der Zeitpunkt des Weglegens wird nicht festgehalten - dann ist die "
        "2-Minuten-Regel wirkungslos."
    )


# -- Bedingung 3: niemand tippt ---------------------------------------------

def test_fokussiertes_eingabefeld_blockiert(index_html):
    block = _effekt(index_html)
    assert "if(_tippt())return;" in block, "Tipp-Pruefung fehlt im Ablauf"
    m = re.search(r"const _tippt=\(\)=>\{.*?\};", block, re.S)
    assert m, "_tippt nicht gefunden"
    assert "INPUT|TEXTAREA|SELECT" in m.group(0), (
        "Die Tipp-Pruefung deckt nicht alle Eingabe-Elemente ab:\n" + m.group(0)
    )


# -- Bedingung 4: nirgendwo ungesicherter Text ------------------------------

def test_text_in_irgendeinem_feld_blockiert(index_html):
    block = _effekt(index_html)
    assert "if(_hatUngesicherteEingabe())return;" in block, (
        "Die harte Sicherung fehlt im Ablauf - ein halb ausgefuelltes "
        "Bautagebuch wuerde beim Auto-Reload verloren gehen."
    )
    m = re.search(r"const _hatUngesicherteEingabe=\(\)=>\{.*?\n    \};", block, re.S)
    assert m, "_hatUngesicherteEingabe nicht gefunden"
    body = m.group(0)
    assert "querySelectorAll('textarea,input')" in body, "prueft nicht alle Felder"
    assert "String(el.value||'').trim()!==''" in body, "prueft nicht auf Inhalt"
    assert "return true" in body, "meldet einen Fund nicht"
    for harmlos in ("checkbox", "radio", "button", "submit", "file", "hidden"):
        assert harmlos in body, (
            "Typ '%s' wird nicht uebersprungen - ein vorbelegtes Kontrollkaestchen "
            "wuerde den Auto-Reload dauerhaft blockieren." % harmlos
        )
    assert "el.disabled||el.readOnly" in body, (
        "Gesperrte/nur-lesbare Felder werden nicht uebersprungen - deren "
        "Inhalt ist nichts, was der Nutzer verlieren koennte."
    )


# -- Schleifen- und Rollen-Schutz -------------------------------------------

def test_pro_sitzung_und_zielversion_nur_ein_versuch(index_html):
    block = _effekt(index_html)
    assert "sessionStorage.getItem(schluessel)" in block and "sessionStorage.setItem(schluessel" in block, (
        "Kein Riegel gegen wiederholte Versuche - ein unlesbarer Server-Stand "
        "koennte eine Reload-Schleife bauen."
    )
    assert "'epk_autoupd_'+ziel" in block, (
        "Der Riegel haengt nicht an der Zielversion - eine spaetere neue "
        "Version wuerde dann nie mehr automatisch angewendet."
    )


def test_kiosk_rollen_bleiben_unberuehrt(index_html):
    block = _effekt(index_html)
    assert "if(_rolle==='lager_display')return;" in block, (
        "Kiosk-Rollen muessen ausgenommen bleiben - die haben mit "
        "_kioskSilentReload ihren eigenen, aelteren Weg."
    )


def test_nutzt_den_bewaehrten_anwende_pfad(index_html):
    """Kein zweiter Reload-Weg: es wird genau das aufgerufen, was auch der
    Banner-Knopf aufruft und was end-to-end nachgewiesen funktioniert."""
    block = _effekt(index_html)
    assert "doSwUpdate();" in block, (
        "Der Auto-Pfad ruft nicht doSwUpdate - zwei getrennte Update-Wege "
        "waeren zwei Fehlerquellen."
    )


def test_banner_bleibt_als_rueckfall(index_html):
    """Der Auto-Pfad ERSETZT den Banner nicht, er ergaenzt ihn."""
    assert "swUpdate&&React.createElement" in index_html, "Update-Banner ist weg"
    assert "Neue Version verf" in index_html, "Banner-Text ist weg"
    assert "onClick: doSwUpdate" in index_html, "Banner-Knopf ruft doSwUpdate nicht mehr"


# -- Umkehrprobe ------------------------------------------------------------

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    ohne_schutz = index_html.replace("      if(_hatUngesicherteEingabe())return;\r\n", "", 1)
    if ohne_schutz == index_html:
        ohne_schutz = index_html.replace("      if(_hatUngesicherteEingabe())return;\n", "", 1)
    assert ohne_schutz != index_html, "Rueckbau griff nicht - Anker veraltet"
    block = _effekt(ohne_schutz)
    assert "if(_hatUngesicherteEingabe())return;" not in block, (
        "Umkehrprobe: der Eingabe-Riegel wuerde nicht anschlagen"
    )

    kurz = re.sub(r"if\(weg<\d+\)return;", "if(weg<1000)return;", index_html, count=1)
    assert kurz != index_html, "Rueckbau der Wartezeit griff nicht"
    m = re.search(r"if\(weg<(\d+)\)return;", _effekt(kurz))
    assert m and int(m.group(1)) < 120000, (
        "Umkehrprobe: der Abwesenheits-Riegel wuerde nicht anschlagen"
    )
