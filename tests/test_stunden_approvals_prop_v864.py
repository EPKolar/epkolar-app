"""
v3.9.864 — Monatsabrechnung riss die GANZE App in die Fehlerseite.

BUG (reproduziert 24.08.2026 im eingeloggten UI): ein Klick auf den Tab
"Monatsabrechnung" ersetzte die komplette Oberflaeche durch
"App-Fehler aufgetreten · approvals is not defined". Nicht nur die Ansicht —
die ganze App, bis zum Reload.

ROOT CAUSE: die Callsite von StundenzettelView reichte `approvals: approvals`
durch. Eine Bindung dieses Namens gibt es in der App nirgends; der State heisst
`absApprovals`. Die drei Nachbar-Callsites (urlaub / mitarbeiter / bueroexport)
machen es laengst richtig.

Warum es so laut knallte: der ReferenceError entsteht beim Auswerten des
Props-Objekts, also im RENDER VON App — nicht im Render der View. Die
_ViewBoundary um die View kann ihn deshalb gar nicht fangen; er laeuft bis zur
aeusseren Boundary durch und nimmt die ganze App mit.

Warum kein Gate ihn fand: `&&`-Kurzschluss. Der Ausdruck wird nur ausgewertet,
wenn genau dieser Tab aktiv ist — node_check parst nur, pytest ist statisch, und
kein Test hatte den Tab je geoeffnet. FINKZEIT_ENABLED ist true, der Tab war
also fuer alle live.

Invariante: auf App-Ebene heisst der Genehmigungs-State `absApprovals`. Ein
nacktes `approvals` ist dort ein nicht existierender Name.
"""
import re


def _main_pad_block(index_html):
    """Der Render-Block der Haupt-Tabs: von `className: "main-pad"` bis zum
    Beginn des Mobile-Mehr-Popups dahinter. Dort stehen alle View-Callsites
    der App-Ebene."""
    start = index_html.find('className: "main-pad"')
    assert start != -1, 'main-pad-Block nicht gefunden'
    end = index_html.find("MOBILE MEHR POPUP", start)
    assert end != -1, 'Ende des main-pad-Blocks nicht gefunden'
    return index_html[start:end]


def test_stunden_callsite_reicht_absApprovals_durch(index_html):
    block = _main_pad_block(index_html)
    m = re.search(r'React\.createElement\(StundenzettelView, \{[^}]*\}', block)
    assert m, 'StundenzettelView-Callsite nicht gefunden'
    call = m.group(0)
    assert "approvals: absApprovals" in call, (
        "StundenzettelView bekommt approvals nicht aus absApprovals — beim "
        "Oeffnen von 'Monatsabrechnung' faellt die GANZE App auf die "
        "Fehlerseite:\n" + call
    )


def test_keine_view_callsite_auf_app_ebene_nutzt_nacktes_approvals(index_html):
    """Generalisiert den Einzelfall: im App-Render existiert kein `approvals`.
    Jede Callsite dort muss absApprovals durchreichen."""
    block = _main_pad_block(index_html)
    treffer = re.findall(r"approvals: approvals\b", block)
    assert not treffer, (
        f"{len(treffer)}x `approvals: approvals` im App-Render — dieser Name "
        f"existiert dort nicht (State ist absApprovals, :7348). Genau diese "
        f"Zeile riss v3.9.863 die App beim Tab 'Monatsabrechnung' um."
    )


def test_alle_approvals_props_im_app_render_kommen_aus_absApprovals(index_html):
    block = _main_pad_block(index_html)
    werte = set(re.findall(r"approvals: ([A-Za-z_$][\w$]*)", block))
    assert werte, "keine approvals-Props im App-Render gefunden — Anker veraltet?"
    assert werte == {"absApprovals"}, (
        f"Unerwartete Quelle fuer approvals im App-Render: {sorted(werte)}. "
        f"Erlaubt ist nur absApprovals."
    )


def test_absApprovals_state_existiert(index_html):
    """Wenn der State jemals umbenannt wird, sollen die Riegel oben nicht
    stillschweigend gruen bleiben, waehrend sie auf einen toten Namen zeigen."""
    assert "const [absApprovals,setAbsApprovals]=" in index_html, (
        "absApprovals-State nicht mehr da — die Riegel oben pruefen dann gegen "
        "einen Namen, den es nicht gibt."
    )


def test_vbueroexport_darf_approvals_weiterreichen(index_html):
    """Gegenprobe zur Abgrenzung: INNERHALB von VBueroExport ist `approvals` ein
    destrukturierter Parameter — dort ist `approvals: approvals` korrekt und
    darf vom Riegel oben nicht miterschlagen werden."""
    assert re.search(
        r"function VBueroExport\(\{[^}]*\bapprovals\b[^}]*\}\)", index_html
    ), "VBueroExport destrukturiert approvals nicht mehr — Abgrenzung pruefen"


def test_selbsttest_riegel_schlagen_bei_rueckbau_an(index_html):
    """Umkehrprobe: alten Stand rekonstruieren, Riegel muessen ROT werden.
    Rueckgebaut wird gezielt IN der StundenzettelView-Callsite, damit die Probe
    nicht versehentlich eine der gesunden Nachbar-Callsites trifft."""
    block_ok = _main_pad_block(index_html)
    m_ok = re.search(r"React\.createElement\(StundenzettelView, \{[^}]*\}", block_ok)
    assert m_ok, "StundenzettelView-Callsite nicht gefunden"
    call_ok = m_ok.group(0)
    call_kaputt = call_ok.replace("approvals: absApprovals", "approvals: approvals")
    assert call_kaputt != call_ok, "Rueckbau griff nicht — Anker veraltet"
    kaputt = index_html.replace(call_ok, call_kaputt, 1)

    block = _main_pad_block(kaputt)
    assert re.findall(r"approvals: approvals\b", block), (
        "Umkehrprobe: der Riegel gegen nacktes approvals wuerde nicht anschlagen"
    )
    m = re.search(r'React\.createElement\(StundenzettelView, \{[^}]*\}', block)
    assert m and "approvals: absApprovals" not in m.group(0), (
        "Umkehrprobe: der Stunden-Riegel wuerde nicht anschlagen"
    )
    werte = set(re.findall(r"approvals: ([A-Za-z_$][\w$]*)", block))
    assert werte != {"absApprovals"}, (
        "Umkehrprobe: der Quellen-Riegel wuerde nicht anschlagen"
    )
