"""Zeiterfassung - Handy-Befunde 14.11.2026 (Samsung A55, Admin, KW 46).

Z4  Admin/PL starten in der Monteur-Uebersicht statt in der eigenen leeren Woche.
Z6  Uebersicht: Wochensumme direkt nach dem Namen; vergangene Werktage ohne
    Buchung werden als "fehlt" markiert und oben gezaehlt; genehmigte
    Abwesenheiten und Feiertage zaehlen nicht.
Z7  Exportknoepfe sind bei einer leeren Woche gesperrt.
Z9  Anzeige mit Dezimalkomma - die EXPORTE bleiben beim Punkt-Formatierer _n.
Z1  Fussleiste: aktiver Zeiterfassungs-Reiter heisst "Zeit" wie inaktiv.

Die Riegel halten Eigenschaften, keine Zeichenfenster: abgegrenzt wird bis zur
naechsten Funktion bzw. Deklaration derselben Ebene.
"""
import re


def _ze(index_html):
    st = index_html.index("function ZeiterfassungView({")
    en = index_html.find("\nfunction ", st + 10)
    assert en > st, "KOEDER STUMM: Ende von ZeiterfassungView nicht gefunden."
    return index_html[st:en]


def _const_block(body, name):
    """Von `const name=` bis zur naechsten `  const ` auf Komponentenebene."""
    i = body.index("  const " + name + "=")
    j = body.find("\n  const ", i + 10)
    return body[i:j]


# ── Z4 ────────────────────────────────────────────────────────────────────────

def test_z4_startansicht_haengt_am_uebersichtsrecht(index_html):
    b = _ze(index_html)
    assert "const [viewAll,setViewAll]=_react.useState.call(void 0, false);" not in b, (
        "viewAll startet wieder hart auf false - der Admin landet in seiner leeren Woche.")
    m = re.search(r"const \[viewAll,setViewAll\]=_react\.useState\.call\(void 0, \(\)=>\{(.*?)\}\);", b)
    assert m, "KOEDER STUMM: die viewAll-Vorbelegung wurde nicht gefunden."
    init = m.group(1)
    # Monteure (kein Uebersichtsrecht) bleiben in der Einzelansicht.
    assert init.startswith("if(!isAdmin)return false;"), init
    # Speicherzugriff faellt bei Ausnahme auf die Uebersicht zurueck, nie auf einen Absturz.
    assert "try{" in init and "catch(_){return true;}" in init, init
    # Das Tor ist dasselbe wie beim Umschaltknopf.
    assert "isAdmin&&React.createElement('button',{onClick:()=>{const _nv=!viewAll;setViewAll(_nv);_zeAnsichtMerken(_nv);}" in b


def test_z4_merken_nur_am_knopf_nicht_beim_zeilenklick(index_html):
    b = _ze(index_html)
    assert b.count("_zeAnsichtMerken(") == 1, "genau ein Aufruf: der Umschaltknopf"
    # Zeilenklick in der Uebersicht ist ein Drill-down und merkt nichts.
    assert "onClick:()=>{setSelWorker(m.id);setViewAll(false);}" in b


# ── Z6 ────────────────────────────────────────────────────────────────────────

def _uebersicht(b):
    i = b.index("Monteur-Übersicht KW ")
    j = b.index("DAY-CENTRIC WEEK GRID", i)
    return b[i:j]


def test_z6_summe_steht_vor_den_tagen(index_html):
    u = _uebersicht(_ze(index_html))
    kopf = u[u.index("React.createElement('thead'"):u.index("React.createElement('tbody'")]
    assert kopf.index('"Σ Woche"') < kopf.index("DAYS.map("), (
        "Die Wochensumme steht wieder hinter den Tagen - auf 412 px nur per Querwischen erreichbar.")
    rumpf = u[u.index("React.createElement('tbody'"):u.index("React.createElement('tfoot'")]
    assert rumpf.index("m.total>0?_hK(m.total,2)") < rumpf.index("DAYS.map("), rumpf[:400]
    fuss = u[u.index("React.createElement('tfoot'"):]
    assert fuss.index("_hK(_gesZE,2)") < fuss.index("DAYS.map(")


def test_z6_excel_export_behaelt_seine_spaltenfolge(index_html):
    b = _ze(index_html)
    exp = _const_block(b, "exportAllXls")
    assert 'const hdrs=["Nr","Mitarbeiter",...DAYS.map((d,i)=>d+" "+dateFmt(i)),"Summe"];' in exp


def test_z6_fehltage_regel(index_html):
    b = _ze(index_html)
    ov = _const_block(b, "loadAllOverview")
    # genehmigte Abwesenheit kommt aus der bestehenden PUREN Autoritaet, kein eigener Statusvergleich
    assert "_ezAbsSet(abs||{},approvals,m.n||\"\")" in ov
    # Werktag = Tagesnorm > 0 (Wochenende und Feiertag fallen raus)
    assert "_kvTagesnorm(_dd.getDay(),_isATFeiertag(_dd))>0" in ov
    # nur Tage VOR heute (Wiener Datum), heute selbst ist nicht "vorbei"
    assert "const _heuteUe=_ezHeuteISO();" in ov and "if(!(iso<_heuteUe))return;" in ov
    # ein Tag mit Stunden ist nie ein Fehltag - die Pruefung steht VOR allem anderen
    rumpf = ov[ov.index("DAYS.forEach((d,i)=>{if(dayTotals[d]>0)return;"):]
    assert rumpf.index("if(dayTotals[d]>0)return;") < rumpf.index("_absSet[iso]") < rumpf.index("fehlt[d]=true")
    # Eintritt/Austritt begrenzen
    assert "iso<String(m.eintritt).slice(0,10)" in ov and "_maIstEhemalig(m,iso)" in ov
    # die bisherigen Summen bleiben unveraendert
    assert "const total=Object.values(dayTotals).reduce((s,v)=>s+v,0);" in ov
    # Effekt reagiert auf neue Abwesenheiten
    assert "[viewAll,kw,entries,abs,approvals]" in b


def test_z6_hinweis_und_zelle_sind_da(index_html):
    u = _uebersicht(_ze(index_html))
    assert "allData.filter(m=>m.fehlTage>0)" in u
    assert '" von "+allData.length+" Mitarbeitern"' in u
    assert '"fehlt");' in u
    # Zeilen mit Fehltagen werden nicht mehr ausgegraut
    assert "opacity:(hasHours||m.fehlTage>0)?1:0.5" in u


# ── Z7 ────────────────────────────────────────────────────────────────────────

def test_z7_exportknoepfe_bei_leerer_woche_gesperrt(index_html):
    b = _ze(index_html)
    assert "React.createElement('button',{onClick:exportWochenStz,disabled:!(weekTotal>0)" in b
    assert "React.createElement('button',{onClick:exportXls,disabled:!_nEintrZE" in b
    assert "React.createElement('button',{onClick:exportAllXls,disabled:!(_gesZE>0)" in b
    # jeder ungesperrte Exportknopf der Ansicht waere ein Rueckfall - alle tragen disabled
    for name in ("exportWochenStz", "exportXls", "exportAllXls"):
        for m in re.finditer(r"\{onClick:" + name + r",([^}]*)", b):
            assert m.group(1).startswith("disabled:"), (name, m.group(0)[:120])
    # die Waechter in den Funktionen bleiben als zweite Linie
    assert "if(!(weekTotal>0)){if(window.__toast)" in _const_block(b, "exportWochenStz")
    assert "if(!reviewRows.length){" in _const_block(b, "exportXls")


# ── Z9 ────────────────────────────────────────────────────────────────────────

def test_z9_formatierer_setzt_komma(index_html):
    b = _ze(index_html)
    assert 'const _hK=(v,d)=>String(_n(v,d)).replace(".",",");' in b


def test_z9_exporte_bleiben_beim_punkt(index_html):
    """Positivprobe zuerst: die Exporte benutzen _n wirklich - sonst waere das
    'kein _hK darin' trivial wahr."""
    b = _ze(index_html)
    for name in ("exportWochenStz", "exportTagesStz", "exportBauwochenbericht", "exportXls", "exportAllXls"):
        blk = _const_block(b, name)
        assert "_n(" in blk, "KOEDER STUMM: %s nutzt _n nicht mehr" % name
        assert "_hK(" not in blk, "%s schreibt jetzt Komma-Zahlen in Excel/Blatt" % name


def test_z9_anzeige_hat_keinen_punkt_formatierer_mehr(index_html):
    b = _ze(index_html)
    render = b[b.index("/* Header */"):]
    # Positivprobe: der Renderteil enthaelt die Komma-Anzeigen
    assert render.count("_hK(") >= 8
    roh = [m.group(0) for m in re.finditer(r"_n\((weekTotal|dt|m\.total|t|_h),1\)", render)]
    assert not roh, roh


# ── Z1 ────────────────────────────────────────────────────────────────────────

def test_z1_fussleiste_zeigt_zeit_title_bleibt_voll(index_html):
    # v3.9.1004 Merge mit der Huelle (A2/C1): sichtbar steht IMMER die Slot-Beschriftung gr.l -
    # der Zeit-Slot heisst damit immer "Zeit", nie "Zeiterfass..." (Z1 bleibt erfuellt, allgemeiner geloest).
    assert ", gr.l/* Handy-Befund A2/C1" in index_html
    # der volle Name bleibt im title (Riegel v3.9.946)
    assert "title: (isActive&&gr.g<4&&tabs[safeKat]?tabs[safeKat].l:gr.l)" in index_html
    # die Gruppe heisst weiterhin "Zeit" und zielt auf die Zeiterfassung
    # v3.9.1010: Ikonen-Schluessel statt Emoji
    assert '{ik:"uhr",l:"Zeit",g:2,c:"#3b82f6",ziel:"zeiterfassung"}' in index_html
