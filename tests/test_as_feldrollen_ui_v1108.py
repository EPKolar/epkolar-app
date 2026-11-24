# -*- coding: utf-8 -*-
"""v3.9.1108 Arbeitsscheine: die zwei Luecken der Feldrollen-Sperre aus 1105 (GF 24.11.: "alles vier ausblenden").

Gefunden bei der Messung fuer Paket 3 (C:/repos/epk-paket3-arbeitsscheine-report.md):
- das Status-Auswahlfeld (Liste und Formular) bot "storniert" allen Rollen an,
- "Termin verschieben" (aendert terminBestaetigt) war fuer Monteure sichtbar.
Beides jetzt nur fuer isAdmin (admin, projektleiter, buero). Ein bereits stornierter Schein zeigt seinen Wert weiter.
"""
import io
import os
import re

HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")


def _av():
    s = io.open(HTML, encoding="utf-8", newline="").read()
    i = s.index("function ArbeitsscheinView(")
    # Ende = naechste Komponente (Grossbuchstabe); ein schlichtes "\nfunction " endet schon bei sharePdf im Drucktext
    return s[i:re.compile(r"\nfunction [A-Z]").search(s, i + 10).start()]


def _luecken(av):
    f = []
    if av.count('.filter(([k])=>isAdmin||k!=="storniert"||k===(a.scheinstatus||"aufgenommen"))') != 1:
        f.append("Status Liste")
    if av.count('.filter(([k])=>isAdmin||k!=="storniert"||k===(form.scheinstatus||"aufgenommen"))') != 1:
        f.append("Status Formular")
    # genau eine ungefilterte Liste bleibt erlaubt: das Filter-Feld "Nach Status filtern" (aendert nichts)
    if av.count("Object.entries(AS_STATUS).map(([k,v])=>React.createElement('option'") != 1:
        f.append("ungefilterte Status-Auswahl")
    if not re.search(r", editId&&isAdmin/\*[^*]*\*/&&!_asMtLocked/\* v3\.9\.547 TASK C: Termin verschieben", av):
        f.append("Termin verschieben")
    return f


def test_feldrollen_luecken_zu():
    assert _luecken(_av()) == []


def test_umkehrprobe_altstand_waere_rot():
    av = _av()
    alt = re.sub(r"\.filter\(\(\[k\]\)=>isAdmin\|\|k!==\"storniert\"\|\|k===\((a|form)\.scheinstatus\|\|\"aufgenommen\"\)\)(/\*[^*]*\*/)?", "", av)
    alt = re.sub(r", editId&&isAdmin/\*[^*]*\*/&&!_asMtLocked", ", editId&&!_asMtLocked", alt)
    assert alt != av
    assert set(_luecken(alt)) == {"Status Liste", "Status Formular", "ungefilterte Status-Auswahl", "Termin verschieben"}
