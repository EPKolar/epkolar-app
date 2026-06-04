"""v3.9.115 — Mobile-Polish: Projekt-Sidebar erreichbar, Kacheln-Schrift passt, Header-Name lesbar.

MCP-Befunde @360/390px (live vermessen + Fixes per Injection validiert):
- .mob-shell-nav (Projekt-Bottom-Nav): 13 Icons, 572px Inhalt in 360px, overflow visible →
  hintere Icons (Material/Dokumente/OFFA/Export) UNERREICHBAR. Fix: flex-wrap (2 Reihen, alle sichtbar).
- Kpi-Wert fontSize:24 fix + overflow:hidden → "€ 232.638,00" wurde in 2-spaltigen Kacheln
  (380-599px) abgeschnitten. Fix: gestufte Schriftgröße nach Wertlänge.
- Chef "Kritisch überfällige AS"-Zeile lief @360 21px über. Fix: kundName ellipsis.
- Projekt-Header: Name auf 62px gequetscht. Fix: minWidth 170 (mobile) → rechte Gruppe bricht um.
"""


def test_mob_shell_nav_wraps(index_html):
    assert ".mob-shell-nav{display:flex;flex-wrap:wrap;" in index_html, (
        "mob-shell-nav braucht flex-wrap — sonst sind hintere Projekt-Nav-Icons auf Mobile unerreichbar"
    )
    assert 'flex:"1 1 44px"' in index_html, "Bottom-Nav-Buttons brauchen flex-basis 44px für sauberes Wrapping"
    assert 'padding:isMob?"10px 8px 110px":"20px"' in index_html, (
        "Shell-Content braucht 110px Bottom-Padding (2-reihige Bottom-Nav ~94px)"
    )


def test_kpi_value_font_scales_with_length(index_html):
    assert 'fontSize:(String(value==null?"—":value).length>12?16:String(value==null?"—":value).length>9?19:24)' in index_html, (
        "Kpi-Wert muss gestufte Schriftgröße haben (lange Werte liefen aus der Kachel)"
    )


def test_chef_kritisch_row_ellipsis(index_html):
    # v3.9.118: minWidth 110 (nicht 0 — sonst schrumpfte der Name auf 28px statt zu wrappen)
    assert "{flex:1,fontWeight:600,minWidth:110,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}},a.kundName||'—')" in index_html, (
        "Chef kritisch-überfällig: kundName muss ellipsen mit minWidth:110"
    )


def test_project_header_name_min_width(index_html):
    # 230 (nicht 170): ◀36 + PA-Nr 70 + gaps ließen dem Namen bei 170 wieder nur 62px.
    assert 'gap:6,minWidth:isMob?230:0,flex:1}}' in index_html, (
        "Projekt-Header: linke Gruppe braucht minWidth 230 auf Mobile (Name war auf 62px gequetscht)"
    )


def test_chef_kritisch_row_wraps(index_html):
    # v3.9.117: Zeile wrappt — Kundenname wurde sonst @360 auf 28px gequetscht (ellipsis allein reichte nicht)
    assert "cursor:'pointer',alignItems:'center',flexWrap:'wrap'}}" in index_html, (
        "Chef kritisch-AS-Zeile muss flexWrap haben"
    )


def test_admin_subtabs_no_shrink(index_html):
    # v3.9.117: Sub-Tab-Buttons dürfen nicht schrumpfen (Labels wurden geclippt statt Leiste zu scrollen)
    assert 'whiteSpace:"nowrap",flexShrink:0,fontFamily:"inherit",transition:"all .15s"}}, t.l)))' in index_html, (
        "Admin-Sub-Tab-Buttons brauchen flexShrink:0"
    )


def test_urlaub_ma_pills_compact_mobile(index_html):
    # v3.9.117: kompakteres Padding — Pills clippten 4px @360
    assert 'padding:isMob?"5px 7px":"8px 14px"' in index_html, "Urlaub-MA-Pills mobile padding 5px 7px"


def test_mobile_mehr_shows_all_tabs(index_html):
    # v3.9.118 KERN-FIX: Auf Mobile zeigt "Mehr" ALLE Tabs — die Top-Leiste scrollt quer und
    # schnitt Arbeitsscheine/Zeiterfassung/Werkzeuge unsichtbar ab → Tabs "fehlten".
    assert "const moreTabs=isMob?tabs:tabs.filter(t=>t.g>=4);" in index_html, (
        "moreTabs muss auf Mobile ALLE Tabs enthalten"
    )
    assert "const moreActive=tabs.filter(t=>t.g>=4).some(t=>tabs.indexOf(t)===safeKat);" in index_html, (
        "moreActive bleibt auf g>=4 bezogen (sonst dauerhaft markiert)"
    )
    # beide Mehr-Dropdowns brauchen maxHeight+Scroll für 14 Einträge
    assert index_html.count('overflowY:"auto"}}/* v3.9.118') == 2, "beide Mehr-Dropdowns brauchen maxHeight+scroll"


def test_chef_kundname_min_width(index_html):
    # v3.9.118: minWidth 110 statt 0 — mit 0 schrumpfte der Name auf 28px statt zu wrappen.
    assert "{flex:1,fontWeight:600,minWidth:110,overflow:'hidden'" in index_html, (
        "Chef kundName braucht minWidth:110 (sonst 28px-Quetschung)"
    )
