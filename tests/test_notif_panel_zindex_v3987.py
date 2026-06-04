"""v3.9.123 — Glocken-Panel: Backdrop lag ÜBER dem Panel und schluckte alle Klicks.

Sebastian: "Glocke geht nicht mehr, kann nichts anklicken von den Push-Nachrichten".
elementFromPoint-Befund: leeres DIV z-index:200 über jedem Eintrag. Panel (zIndex:200) und
Backdrop (zIndex:200) waren gleich hoch, Backdrop später im DOM → gewinnt das Stacking.
"""
import re


def test_backdrop_below_panel(index_html):
    # Panel = zIndex:200 (showNotifPanel-Container)
    assert re.search(r'showNotifPanel&&\(React\.createElement\(\'div\', \{ style: \{zIndex:200,position:"fixed"', index_html), (
        "Notification-Panel muss zIndex:200 behalten"
    )
    # Backdrop = zIndex:199 (unter dem Panel)
    assert 'setShowNotifPanel(false);}}, style: {position:"fixed",inset:0,background:"rgba(0,0,0,.3)",zIndex:199}}' in index_html, (
        "Notification-Backdrop muss zIndex:199 haben (unter dem Panel — sonst schluckt er alle Klicks)"
    )
