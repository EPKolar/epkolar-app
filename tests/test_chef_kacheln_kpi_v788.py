# -*- coding: utf-8 -*-
"""v3.9.788 — Chef-Portal Zaehler-Kacheln auf die schlanke Kpi-Komponente vereinheitlicht (Sebastian 21.07.).

Die ChefDashboard-ueberblick-Kacheln waren bespoke (4px-Left-Border, padding 12) und wirkten "zu dick".
Referenz = Administration/Kpi (3px farbige OBERKANTE). Fix: rendern via Kpi (EIN Stil), Kpi minimal um ein
optionales trend-Prop erweitert. Zahlen + Deep-Links byte-identisch, keine Datenlogik.
"""


def test_kpi_hat_trend_prop(index_html):
    """Kpi minimal erweitert um optionales trend={color,text} — der Trend-Pfeil neben dem Wert bleibt."""
    assert "function Kpi({label,value,sub,color,onClick,i,title,trend}){" in index_html
    # der Wert-Div rendert das trend-Prop optional (ohne trend unveraendert)
    assert "trend?React.createElement('span',{style:{fontSize:14,color:trend.color,fontWeight:700}},trend.text):null" in index_html


def test_chef_kacheln_via_kpi(index_html):
    """Die ChefDashboard-ueberblick-Kacheln rendern jetzt via Kpi (nicht mehr bespoke borderLeft-Karte)."""
    # neue Render-Zeile: Kpi mit label/value/sub/color/onClick/trend aus dem k-Array
    assert "return React.createElement(Kpi,{key:i,label:k.l,value:k.v,sub:k.sub+(tr?' · vs. Vorwoche':''),color:k.color,onClick:k.click,i:i,trend:tr?{color:tr.color,text:tr.icon" in index_html, \
        "Chef-Kacheln muessen via Kpi rendern"
    # die alte bespoke Karte (fetter 4px-Left-Border + colored mono-Wert) darf im ueberblick-Map nicht mehr stehen
    assert "borderLeft:'4px solid '+k.color,cursor:'pointer'}}" not in index_html, "alte bespoke Chef-Kachel muss weg sein"


def test_deep_links_und_zaehler_unveraendert(index_html):
    """Deep-Links (onNav/__asFilter/__asOpenId) + Zaehler-Quellen byte-identisch — nur die Optik wechselt."""
    # die k-Array-Definition (Zahlen + Klick-Ziele) bleibt unveraendert
    assert "{l:'Aktive Projekte',v:aktivProj,sub:projects.length+' gesamt',color:V.acTx,click:function(){onNav('projekte');}}" in index_html
    assert "window.__asFilter='offen_bearb';onNav('arbeitsscheine');" in index_html
    assert "window.__asOpenId=_ueberfaelligeArr[0].id;" in index_html
