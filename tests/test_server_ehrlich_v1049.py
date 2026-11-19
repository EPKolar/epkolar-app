# -*- coding: utf-8 -*-
"""GF 19.11.: tote "Server"-Elemente ehrlich machen.

Befund vorher (v3.9.1047): (1) Abwesenheiten "Auf Firmenserver speichern" rief exportToServer -> API.exportPersonal
(nur GET time_entries) und verwarf das Ergebnis - nichts wurde geschrieben. (2) Projektakte > Export zeigte eine
"Server-Ordnerstruktur" als waere sie angelegt - reine Anzeige.
Jetzt: (1) Knopf + Handler entfernt (beide Render-Stellen). (2) Anzeige bleibt, traegt den Hinweis
"Vorschau der Ablage - es wird derzeit nichts auf den Server geschrieben."
"""
import io
import os

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")
HINWEIS = "Vorschau der Ablage \\u2014 es wird derzeit nichts auf den Server geschrieben."


def _src():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _knopf_weg(src):
    return "exportToServer" not in src and '"Auf Firmenserver speichern"' not in src


def test_firmenserver_knopf_und_handler_weg():
    assert _knopf_weg(_src())


def test_ordner_vorschau_bleibt_und_ist_ehrlich_beschriftet():
    src = _src()
    i = src.index('"Server-Ordnerstruktur" )')
    blk = src[i:i + 2500]
    assert '"Z:\\\\Projekte\\\\", p.nr' in blk, "Pfad-Anzeige unveraendert"
    assert HINWEIS in blk
    assert "srvFolders.map(" in blk, "Ordnerliste bleibt"


def test_excel_export_der_abwesenheiten_bleibt():
    src = _src()
    assert '_btn(exportAbsCsv, V.tx, "transparent", V.bdK, _ik("tabelle",16), "Excel")' in src


def test_umkehrprobe():
    alt = ('const exportToServer=()=>{};\n'
           ', _btn(exportToServer, V.tx, "transparent", V.bdK, _ik("export",16), "Auf Firmenserver speichern")')
    assert not _knopf_weg(alt)
