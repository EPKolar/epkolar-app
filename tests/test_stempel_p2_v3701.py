"""v3.9.701 — die drei P2 aus dem Bug-Hunt (Befund 6, 8, 7).

Enthält den zweiten Kommentar-Gegenbeweis (Hausregel v3.9.699): der Kommentar „im Antrags-Modus
stempelt der Scan NICHT" (Befund 6) war falsch — ein Scan in jedem Zustand außer 'ident' fiel in
den Stempel-Pfad. Der Test unten hält fest, dass jeder nicht-leere amode den Stempel-Pfad blockt.
"""
import re


# ── Befund 6: Scan während des Antrags-Flows stempelt nicht ───────────────────
def test_jeder_antrags_screen_blockt_den_stempel_pfad(index_html):
    """Nach dem ident-Zweig muss ein Guard stehen, der JEDEN nicht-leeren amode abfängt,
    BEVOR der normale Stempel-Pfad (_busy/try) beginnt."""
    m = re.search(r"if\(_amodeRef\.current==='ident'\)\{.*?\}\s*(.*?)if\(_busy\.current\)return;", index_html, re.S)
    assert m, "Struktur um den ident-Guard nicht gefunden"
    zwischen = m.group(1)
    assert "if(_amodeRef.current)return;" in zwischen, \
        "Kein Guard, der typ/datum/confirm/done vom Stempel-Pfad fernhält — der Scan wuerde stempeln"


def test_ident_bleibt_der_einzige_konsumierende_zweig(index_html):
    """'ident' identifiziert (setAmode('typ')); jeder andere amode ignoriert den Scan."""
    assert "if(_amodeRef.current==='ident'){" in index_html
    assert "setAmode('typ')" in index_html


# ── Befund 8: FinkZeit-Kachel-Rahmen nicht mehr rot ───────────────────────────
def test_kachel_rahmen_nicht_mehr_rot_bei_differenz(index_html):
    """Die dritte, in v3.9.697 übersehene Stelle: der borderLeft der Monatsabrechnungs-Kachel."""
    assert 'borderLeft:"4px solid "+(finkStats.diffWarn>0?COLORS.ERROR' not in index_html, \
        "Der Kachel-Rahmen färbt sich bei einer Projektzeit/Anwesenheit-Differenz weiterhin rot"
    assert 'borderLeft:"4px solid "+(finkStats.offen>0?COLORS.WARNING:"#8b5cf6")' in index_html


def test_kein_diffwarn_error_mehr_in_der_finkzeit_kachel(index_html):
    """Gesamtprobe: In der Monatsabrechnungs-Kachel darf diffWarn NIRGENDS mehr COLORS.ERROR triggern
    (Alert war schon v3.9.697 neutral, Zahl+Label auch — jetzt auch der Rahmen)."""
    # Der komplette Kachel-Block rund um abgeglichen/total darf kein diffWarn>0?COLORS.ERROR mehr haben.
    m = re.search(r"Monatsabrechnung.{0,1200}?finkStats\.abgeglichen.{0,600}", index_html, re.S)
    assert m, "Monatsabrechnungs-Kachel nicht gefunden"
    assert "diffWarn>0?COLORS.ERROR" not in m.group(0)


# ── Befund 7: Anlern-Button für Terminal-Rolle ausgeblendet ───────────────────
def test_anlern_button_haengt_am_terminal_flag(index_html):
    assert "!props.terminal?h('button',{onClick:()=>{setAnlern(v=>!v)" in index_html, \
        "Der Anlern-Button ist nicht mehr an props.terminal gekoppelt"


def test_stempeltafel_bekommt_das_terminal_flag(index_html):
    assert "React.createElement(StempelTafel,{monteure:monteure,onLogout:logout,terminal:_isStempelTerminal})" in index_html
