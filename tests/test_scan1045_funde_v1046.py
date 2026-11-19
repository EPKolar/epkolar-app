# -*- coding: utf-8 -*-
"""v3.9.1046 - Funde aus dem Scan 1045 (390 px hell/dunkel, 1200 px Tablet).

Reine Anzeige: Kontrast (weisse Schrift auf Statusflaechen, Statusschrift auf
getoenten Chips), Linien-Ikonen statt Zeichen (Pfeile, Warnzeichen, Vollbild),
Namen fuer drei Felder ohne Beschriftung, zwei Zeilen statt Ellipse.

Die Riegel unten pruefen den NEUEN Code positiv (Token, Ikone, Name) und
rechnen die Kontraste der eingesetzten Farben nach - eine Farbe, die jemand
spaeter "nur ein bisschen heller" macht, faellt hier auf.
"""
import re

import pytest


def _lum(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])


def _kontrast(a, b):
    x, y = sorted((_lum(a), _lum(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def _colors(index_html):
    m = re.search(r"const COLORS=\{([^}]+)\}", index_html)
    assert m, "const COLORS fehlt"
    return dict(re.findall(r'([A-Z_]+):"(#[0-9a-fA-F]{6})"', m.group(1)))


# ── Token ────────────────────────────────────────────────────────────────

def test_fill_token_tragen_weisse_schrift(index_html):
    c = _colors(index_html)
    for k in ("ERROR_FILL", "WARNING_FILL", "INFO_FILL"):
        assert k in c, "COLORS.%s fehlt" % k
        assert _kontrast("#ffffff", c[k]) >= 4.5, (k, c[k])
    # Die Grundtoene bleiben (Punkte/Raender) - sie sind KEINE Schriftflaeche.
    assert c["WARNING"] == "#f97316" and c["ERROR"] == "#ef4444"


# ── 1 / 15 Sync-Leiste, Zaehler, Statuswort ──────────────────────────────

def test_sync_leiste_nimmt_fill_token(index_html):
    assert ('background:online?(failedCount>0?COLORS.ERROR_FILL:syncing?COLORS.INFO_FILL:'
            'COLORS.WARNING_FILL):COLORS.ERROR_FILL,color:"#fff"') in index_html
    # "Jetzt sync" liegt ohne weissen Schleier auf der Flaeche
    assert ('background:"transparent"/* Scan 1045: ein weisser Schleier hellte die Flaeche unter '
            'der weissen Schrift auf (2,31:1) */,color:"#fff"') in index_html
    assert 'right:-4,background:COLORS.WARNING_FILL,color:"#fff"' in index_html
    assert 'background:!syncStatus.connected?COLORS.ERROR_FILL:COLORS.WARNING_FILL,color:"#fff"' in index_html
    assert '"linear-gradient(90deg,"+COLORS.WARNING_FILL+",#9a3412)"' in index_html
    assert index_html.count('{background:"rgba(0,0,0,.18)",borderRadius:10,padding:"2px 8px"') == 2


def test_kein_server_lesbar(index_html):
    assert 'V.dm):(_dark?COLORS.ERROR_DARK:COLORS.ERROR_FILL)}}, syncStatus.syncing?"Sync...":' in index_html


# ── 2 / 18 Arbeitsschein-Knoepfe ─────────────────────────────────────────

def test_storno_und_bearbeiten(index_html):
    assert index_html.count('storno(a.id);}, style: {background:COLORS.ERROR_FILL,color:"#fff",') == 2
    assert 'openEdit(a);}, style: {...bpS,border:"none",borderRadius:4,padding:"4px 7px",minHeight:0,' in index_html
    assert 'openEdit(a);}, style: {background:"#3b82f6"' not in index_html


# ── 3 Projektakte > Zeiterfassung ────────────────────────────────────────

def test_rollen_flaeche(index_html):
    m = re.search(r"const _ROLE_FILL_MAP=\{([^}]+)\}", index_html)
    assert m, "_ROLE_FILL_MAP fehlt"
    werte = re.findall(r'"([^"]+)":"(#[0-9a-fA-F]{6})"', m.group(1))
    assert len(werte) >= 12
    for rolle, h in werte:
        assert _kontrast("#ffffff", h) >= 4.5, (rolle, h)
    assert 'const _ROLE_FILL=r=>_ROLE_FILL_MAP[r]||"#4b5563";' in index_html
    assert 'background:_ROLE_FILL((wk||{}).r),color:"#fff"' in index_html


def test_loeschkreuz_und_taetigkeit(index_html):
    assert ('color:_dark?COLORS.ERROR_DARK:COLORS.ERROR_FILL,padding:isMob?"6px 9px":"2px 4px"'
            in index_html)
    assert 'touchAction:"manipulation"}},_ik("kreuz",14)))' in index_html
    assert ('{title:entry.taetigkeit||entry.task,style:{fontSize:12,color:V.tx,overflow:"hidden",'
            'textOverflow:"ellipsis",..._zweiZeilen,marginTop:2}}') in index_html


# ── 4 / 5 Projektakte-Texte ──────────────────────────────────────────────

def test_status_und_fortschritt_lesbar(index_html):
    assert index_html.count('background:sc.bg,color:_lesbar(sc.c,true),display:"inline-flex"') == 2
    assert "React.createElement('b', { style: {color:_lesbar(sc.c)}}, p.fortschritt, \"%\")" in index_html
    assert '{fontFamily:mono,fontSize:16,fontWeight:700,color:_lesbar(sc.c)}}, p.fortschritt, "%")' in index_html
    assert "color:sc.c" not in index_html


def test_graue_und_rote_texte(index_html):
    assert '{fontSize:13,fontWeight:700,color:V.dm}}, "Personal")' in index_html
    assert '{fontSize:13,fontWeight:700,color:V.dm}}, "Material")' in index_html
    assert "{fontSize:14,fontWeight:600,color:V.dm}}, search?('Keine Treffer" in index_html
    assert 'borderColor:_lesbar("#ef4444"),color:_lesbar("#ef4444")}}, _ikVw("dokument","PDF-Report")' in index_html


# ── 6 / 16 Dispo ─────────────────────────────────────────────────────────

def _panel(index_html):
    a = index_html.index("function DispoPanel({")
    return index_html[a:index_html.index("function ArbeitsscheinView({", a)]


def test_dispo_ikonen_und_farben(index_html):
    p = _panel(index_html)
    assert '_dpIkTxt("⚠","war "+o.ueberfaelligVon.slice(8,10)' in p
    assert '_dpIkTxt("⚠","überschneidet "+o.konflikt)' in p
    assert '_dpIkTxt("⚠","Nicht eingeplant ("+' in p
    assert 'color:_dark?"#fdba74":"#9a3412",cursor:"pointer",fontFamily:"inherit"}},_zpIk("abnahme","Übernehmen",12))' in p
    assert 'color:isFix?V.tx:(_dark?"#fdba74":"#9a3412")' in p
    assert 'whiteSpace:"nowrap",display:"inline-flex",alignItems:"center"}},_zpIk("drehen","Neu berechnen",14))' in p
    assert 'background:active?COLORS.WARNING_FILL:"transparent",color:active?"#fff":V.tx' in p
    assert "opacity:active?1:.85}},\"Auslastung \"" in p
    assert '\'aria-label\':"Vorherige Woche"},_ik("links",18))' in p
    assert '\'aria-label\':"Nächste Woche"},_ik("rechts",18))' in p
    # Kontraste der eingesetzten Schriftfarben auf dem Chipgrund (#f2eee7 gemessen)
    for h in ("#9a3412", "#b91c1c"):
        assert _kontrast(h, "#f2eee7") >= 4.5, h


# ── 7 Zeiterfassung ──────────────────────────────────────────────────────

def test_zeiterfassung_blau_lesbar(index_html):
    assert 'dt>0?_lesbar("#3b82f6"):V.mt}},dt>0?_hK(dt,2)+"h":"—")' in index_html
    assert 'm.total>0?_lesbar("#3b82f6"):V.mt}},m.total>0?_hK(m.total,2):"—")' in index_html


# ── 9 / 11 Pfeile und Team-Timeline ──────────────────────────────────────

def test_team_timeline(index_html):
    assert "const nameW=isMob?96:104;" in index_html
    assert "{ title: m, style: {overflow:\"hidden\",textOverflow:\"ellipsis\",..._zweiZeilen,minWidth:0," in index_html
    assert '_zpIk("links","Zurück",14))' in index_html
    assert '"Vor", _ik("rechts",14)))' in index_html


@pytest.mark.parametrize("neu", [
    'title: "Zurück", style: {...bsS(),padding:isMob?"8px 14px":"5px 10px",minHeight:isMob?44:0,minWidth:44,',
    "onClick:()=>_shiftYm(-1),style:{...bsS(),padding:'6px 10px',minHeight:isMob?44:0,minWidth:44,",
    'React.createElement(\'span\', { \'aria-hidden\': "true", style: {display:"inline-flex",flex:"0 0 auto"}}, _ik("links",16)), React.createElement(\'span\', { className: "sb-text"}, "Alle Projekte")',
    ', _ik("links",22))\n            , React.createElement(\'span\', { style: {fontSize:isMob?12:13,fontWeight:700,color:V.acTx,flexShrink:0}}, p.nr)',
    'title: "Vorherige KW", style: {...bsS(),padding:isMob?"8px 12px":"4px 8px",fontSize:isMob?13:12,minHeight:isMob?44:0,minWidth:44,',
    'onClick: ()=>setKw(k=>Math.max(1,k-1)), style: {...bsS(),padding:"6px 10px",minWidth:44,',
    '_zpIk("links","Zurück zur Liste",14))',
    'onClick: ()=>setMo(Math.max(0,mo-1)), style: {...bsS(),padding:"5px 10px",minWidth:44,',
    'setSelMonat(m);setSelJahr(y);}, style: {...bsS(),padding:"6px 14px",fontSize:16,lineHeight:1,minWidth:44,',
    'onClick:()=>switchKw(kw-1),style:{...bsS(),padding:"5px 10px",minWidth:44,',
])
def test_pfeile_sind_linien_ikonen(index_html, neu):
    assert neu in index_html


def test_keine_dreieck_pfeile_als_knopfinhalt_mehr(index_html):
    """Die Blaetterknoepfe dieser Version - ihr Inhalt war genau "◀"/"▶" hinter dem Stilblock."""
    for alt in ('touchAction:"manipulation"}}, "◀")', 'touchAction:"manipulation"}}, "▶")',
                'padding:"6px 10px"}}, "◀")', 'padding:"5px 10px"}}, "◀")', 'padding:"5px 10px"}},"◀")',
                "minHeight:isMob?38:0}},'◀')", '"◀ Zurück zur Liste"', '"◀ Zurück")', '"Vor ▶")'):
        assert alt not in index_html, alt


# ── 12 Flotte ────────────────────────────────────────────────────────────

def test_flotte_vollbild_ikone(index_html):
    assert 'verkleinern:["M8 3v3a2 2 0 0 1-2 2H3"' in index_html
    assert "_ik(props.maximized?'verkleinern':'vollbild',16))" in index_html
    assert "'aria-label':props.maximized?'Verkleinern':'Fahrtenbuch maximieren'" in index_html
    assert "'⛶')" not in index_html


# ── 13 Felder mit Namen ──────────────────────────────────────────────────

def test_felder_haben_namen(index_html):
    assert "{ value: srvUrl, readOnly: true, 'aria-label': \"Supabase URL\"," in index_html
    assert "{ value: userSortBy, 'aria-label': \"Sortierung\"," in index_html
    assert "{ value: capCat, 'aria-label': \"Foto-Kategorie\"," in index_html


# ── 17 Fahrzeug-Plaketten ────────────────────────────────────────────────

def test_fahrzeug_plaketten(index_html):
    # v1049 Fahrzeuge-UX: die farbigen Plaketten der Liste sind einer Fristzeile gewichen (_fzFristZeile).
    # Farbe nur bei Faelligkeit, als Schrift ueber _lesbar auf den *_FILL-Toenen (>= 4,5:1 gemessen in v1046).
    assert 'const rot=_lesbar(COLORS.ERROR_FILL),orange=_lesbar(COLORS.WARNING_FILL);' in index_html
    assert "const farbe=st==='overdue'?rot:(st==='toleranz'||st==='warn')?orange:null;" in index_html
    assert 'background:"#fee2e2",color:"#dc2626"' not in index_html
    for fg, bg in (("#b91c1c", "#fee2e2"), ("#92400e", "#fef3c7"), ("#0369a1", "#e0f2fe")):
        assert _kontrast(fg, bg) >= 4.5, (fg, bg)
