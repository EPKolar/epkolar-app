# -*- coding: utf-8 -*-
"""
v3.9.866 - Ausgetretene Mitarbeiter verschwinden aus dem Alltagsbild.

AUFTRAG: Ehemalige sollen nicht mehr in Liste, Suche und Zaehlern auftauchen.
Sie werden NICHT geloescht und nicht anders behandelt - an ihnen haengen
Zeiteintraege, Abwesenheiten und Scheine, die Worker-Zeile ist die einzige
Namensaufloesung.

BEFUND ZUR AUFTRAGS-PRAEMISSE (selbst geprueft, nicht uebernommen):
Die Annahme "Nicht-Staff sehen die MA-Liste inkl. Sektion Ehemalige" trifft
NICHT zu. MitarbeiterView kehrt bei `!isAdmin` frueh mit der Self-Service-
Ansicht "Mein Profil" zurueck; die Liste dahinter ist fuer monteur / helfer /
techniker / obermonteur unerreichbar - samt Sektion, KPIs und Detail-Panel.
Real war nur die GLOBALE SUCHE: die filterte Ausgetretene nicht und lief fuer
jede Rolle mit hasPerm(mitarbeiter) - laut ROLES also jede Rolle ausser viewer.
Genau die ist jetzt zu.

Diese Tests pinnen beides: den frueh-return (damit die Annahme nicht still
kippt) und die tatsaechlichen Aenderungen.
"""
import re


# -- Das Praedikat: EINE Quelle, inhaltlich unveraendert ---------------------

def test_praedikat_liegt_auf_modulebene(index_html):
    m = re.search(r"function _maIstEhemalig\(m,heute\)\{.*?\n\}", index_html, re.S)
    assert m, "_maIstEhemalig fehlt"
    body = m.group(0)
    assert "String(m.austritt).slice(0,10)<h" in body, (
        "Datumsvergleich weicht vom bisherigen Praedikat ab:\n" + body
    )
    assert "_ezHeuteISO()" in body, "Wiener Datum via _ezHeuteISO fehlt:\n" + body


def test_mitarbeiterview_erfindet_das_praedikat_nicht_neu(index_html):
    assert "const _maEhemalig=m=>_maIstEhemalig(m,_hkMV);" in index_html, (
        "MitarbeiterView rechnet wieder selbst statt zu delegieren - zwei "
        "Quellen fuer dieselbe Frage."
    )


def test_staff_rolle_liegt_auf_modulebene_und_wird_delegiert(index_html):
    m = re.search(r"function _maStaffRolle\(u\)\{.*?\n\}", index_html, re.S)
    assert m, "_maStaffRolle fehlt"
    for rolle in ("admin", "projektleiter", "buero"):
        assert rolle in m.group(0), "Rolle %s fehlt in _maStaffRolle" % rolle
    assert "const isAdmin=_maStaffRolle(curUser);" in index_html, (
        "MitarbeiterView.isAdmin delegiert nicht - Rollenmenge droht "
        "auseinanderzulaufen."
    )


# -- (1) Rolle monteur: kein Ehemaligen-Element, kein Suchtreffer ------------

def test_nicht_staff_erreicht_die_liste_gar_nicht(index_html):
    """Der frueh-return ist der Grund, warum Teil A fuer Liste/KPIs/Detail
    gegenstandslos ist. Kippt er, muss dieser Test rot werden."""
    assert "if(!isAdmin || (profilMode && _canSeeProfil)){" in index_html, (
        "Der Self-Service-Zweig fuer Nicht-Staff ist weg oder umformuliert - "
        "dann sehen monteur/helfer/techniker die MA-Liste, und Teil A des "
        "Auftrags wird ploetzlich relevant."
    )


def test_globale_suche_filtert_ehemalige_fuer_nicht_staff(index_html):
    assert "monteure.filter(m=>(_maStaffRolle(curUser)||!_maIstEhemalig(m))&&" in index_html, (
        "Die globale Suche filtert Ausgetretene nicht mehr nach Rolle - "
        "Nicht-Staff bekaemen ihre Namen wieder als Treffer."
    )


def test_keine_sektion_ehemalige_mehr(index_html):
    assert '"_ehemalige"' not in index_html, (
        "Die eigene Ehemaligen-Sektion ist zurueck. Sie war zwar zugeklappt, "
        "die Kopfzeile mit dem Namens-Zaehler stand aber sichtbar in der Liste."
    )
    assert '" Ehemalige ("' not in index_html, "Sektions-Kopfzeile ist zurueck"


# -- (2)/(3) Rolle admin: Schalter default aus, eingeschaltet sichtbar -------

def test_schalter_existiert_mit_beiden_beschriftungen(index_html):
    assert 'showEhem?"Auch Ehemalige":"Nur Aktive"' in index_html, (
        "Der Schalter 'Nur Aktive' <-> 'Auch Ehemalige' fehlt."
    )
    assert "onClick: ()=>setShowEhem(!showEhem)" in index_html, "Schalter schaltet nicht"


def test_schalter_default_ist_nur_aktive(index_html):
    assert "const [showEhem,setShowEhem]=_react.useState.call(void 0, false);" in index_html, (
        "Default ist nicht mehr 'Nur Aktive' - Ehemalige waeren wieder im "
        "Alltagsbild."
    )


def test_schalter_wird_nicht_persistiert(index_html):
    """Auftrag: Schalter-State lokal, NICHT persistieren."""
    m = re.search(r"const \[showEhem,setShowEhem\].*?const _sichtbareMA", index_html, re.S)
    assert m, "Bereich um den Schalter-State nicht gefunden"
    assert "localStorage" not in m.group(0), (
        "showEhem wird persistiert - der Auftrag verlangt ausdruecklich lokal."
    )


def test_liste_zeigt_nur_die_sichtbare_menge(index_html):
    assert "const _out=_sichtbareMA.map(_row);" in index_html, (
        "Die Liste rendert nicht mehr die sichtbare Menge."
    )
    assert "const _sichtbareMA=_react.useMemo.call(void 0, ()=>showEhem?monteure:monteure.filter(m=>!_maIstEhemalig(m,_hkMV))" in index_html, (
        "Die sichtbare Menge folgt dem Schalter nicht."
    )


def test_badge_ausgetreten_bleibt(index_html):
    """Eingeschaltet sollen Ehemalige MIT dem bestehenden Badge erscheinen."""
    assert "const _maBadge=m=>_maEhemalig(m)?React.createElement" in index_html, "_maBadge ist weg"
    assert '"Ausgetreten "+fdt(m.austritt)' in index_html, "Badge-Text geaendert"
    assert "_maBadge(m)" in index_html, "Badge wird in der Zeile nicht mehr gerendert"


# -- Zahlen passen zur sichtbaren Liste -------------------------------------

def test_kpis_zaehlen_die_sichtbare_menge(index_html):
    assert "_sichtbareMA.filter(m=>g.roles.includes(m.r)).length" in index_html, (
        "Die Rollen-KPIs zaehlen wieder alle - die Kacheln zeigen dann Zahlen, "
        "zu denen es keine sichtbaren Zeilen gibt."
    )
    assert 'label: "Mitarbeiter", value: _sichtbareMA.length' in index_html, (
        "Die Kachel 'Mitarbeiter' zaehlt wieder alle."
    )
    assert '"Mitarbeiter (" , _sichtbareMA.length, ")"' in index_html, (
        "Der Listen-Kopfzaehler zaehlt wieder alle."
    )


def test_detail_panel_nur_aus_der_sichtbaren_menge(index_html):
    assert "const selM=_sichtbareMA.find(m=>m.id===sel);" in index_html, (
        "selM loest wieder aus der Gesamtmenge auf - ein alter sel-State oder "
        "Deep-Link auf einen Ausgetretenen zeigt dann ein Detail-Panel zu einer "
        "Zeile, die es in der Liste nicht gibt."
    )


def test_selM_steht_nach_der_sichtbaren_menge(index_html):
    """TDZ-Schutz (Fehlerklasse v3.9.672): selM greift auf _sichtbareMA zu,
    muss also DAHINTER deklariert sein - sonst 'Cannot access before
    initialization' beim Render, und die Ansicht ist tot."""
    i_set = index_html.find("const _sichtbareMA=")
    i_sel = index_html.find("const selM=_sichtbareMA.find")
    assert i_set != -1 and i_sel != -1, "Anker nicht gefunden"
    assert i_set < i_sel, (
        "selM steht VOR _sichtbareMA - Temporal-Dead-Zone, die MA-Ansicht "
        "wuerde beim Render werfen."
    )


# -- Tabu: nichts geloescht, keine Daten angefasst --------------------------

def test_kein_loeschen_dazugekommen(index_html):
    """Der Auftrag verbietet Loeschen/Hard-Delete/Aendern von workers-Daten."""
    m = re.search(r"const _sichtbareMA=.*?const selM=_sichtbareMA", index_html, re.S)
    assert m, "Bereich nicht gefunden"
    block = m.group(0)
    for verboten in ("setMonteure", "DELETE", "_sbDelete"):
        assert verboten not in block, (
            "Im neuen Sichtbarkeits-Code steht '%s' - hier wird nur gefiltert, "
            "nie geschrieben." % verboten
        )


# -- Umkehrprobe ------------------------------------------------------------

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    kaputt = index_html.replace("const _out=_sichtbareMA.map(_row);",
                                "const _out=monteure.map(_row);", 1)
    assert kaputt != index_html, "Rueckbau griff nicht"
    assert "const _out=_sichtbareMA.map(_row);" not in kaputt, (
        "Umkehrprobe: der Listen-Riegel wuerde nicht anschlagen"
    )
    ohne_filter = index_html.replace("(_maStaffRolle(curUser)||!_maIstEhemalig(m))&&", "", 1)
    assert ohne_filter != index_html, "Rueckbau der Suche griff nicht"
    assert "monteure.filter(m=>(_maStaffRolle(curUser)" not in ohne_filter, (
        "Umkehrprobe: der Such-Riegel wuerde nicht anschlagen"
    )
