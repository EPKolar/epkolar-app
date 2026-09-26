"""Regression-Tests fuer Bug-Hunt-Befunde 2026-06-12 (v3.9.325-328).

Verhindert dass die Modal-Migration-Luecken erneut entstehen — gerade die
destruktiven Handler haben sich offenbar seit v3.9.11 (Round-3) durch Refactors
unbemerkt zurueck-mutiert.
"""
import re


# v3.9.325 — Wochenplanung clearRow + delRow ---------------------------------

def test_wochenplanung_clearRow_uses_confirmModal(index_html):
    """clearRow muss async sein + _confirmModal-Aufruf enthalten."""
    m = re.search(
        r"const\s+clearRow\s*=\s*async\s*\(id\)\s*=>\s*\{[\s\S]{0,200}?_confirmModal\(",
        index_html,
    )
    assert m, "clearRow ohne async/_confirmModal — Bug-Regression v3.9.325"


def test_wochenplanung_delRow_uses_confirmModal_danger(index_html):
    """delRow muss async + _confirmModal mit danger-Variant."""
    m = re.search(
        r"const\s+delRow\s*=\s*async\s*\(id\)\s*=>\s*\{[\s\S]{0,200}?_confirmModal\(",
        index_html,
    )
    assert m, "delRow ohne async/_confirmModal — Bug-Regression v3.9.325"
    # Block fuer die n-Zeichen nach delRow grep
    blob = index_html[m.start():m.start()+400]
    assert 'variant:"danger"' in blob, "delRow _confirmModal sollte danger-Variant haben"


# v3.9.326 — Urlaubsplanung approve + reject ---------------------------------

def test_urlaub_approve_has_admin_guard_and_modal(index_html):
    """approve(m,d) muss async sein + isAdmin-Handler-Guard + _confirmModal."""
    m = re.search(
        r"const\s+approve\s*=\s*async\s*\(m,\s*d\)\s*=>\s*\{[\s\S]{0,400}?_confirmModal\(",
        index_html,
    )
    assert m, "approve ohne async/_confirmModal — Bug-Regression v3.9.326"
    blob = index_html[m.start():m.start()+400]
    assert "if(!isAdmin)return" in blob, "approve braucht Handler-Eingangs-Guard if(!isAdmin)return"


def test_urlaub_reject_has_admin_guard_and_modal_danger(index_html):
    """reject(m,d) muss async + isAdmin-Guard + _confirmModal mit danger."""
    m = re.search(
        r"const\s+reject\s*=\s*async\s*\(m,\s*d\)\s*=>\s*\{[\s\S]{0,400}?_confirmModal\(",
        index_html,
    )
    assert m, "reject ohne async/_confirmModal — Bug-Regression v3.9.326"
    blob = index_html[m.start():m.start()+500]
    assert "if(!isAdmin)return" in blob, "reject braucht Handler-Eingangs-Guard"
    assert 'variant:"danger"' in blob, "reject _confirmModal sollte danger-Variant haben"


# v3.9.327 — Notifs deleteNotif + Alle-loeschen ------------------------------

def test_deleteNotif_uses_confirmModal(index_html):
    """deleteNotif muss async sein + _confirmModal mit danger."""
    m = re.search(
        r"const\s+deleteNotif\s*=\s*async\s+id\s*=>\s*\{[\s\S]{0,200}?_confirmModal\(",
        index_html,
    )
    assert m, "deleteNotif ohne async/_confirmModal — Bug-Regression v3.9.327"
    blob = index_html[m.start():m.start()+400]
    assert 'variant:"danger"' in blob, "deleteNotif sollte danger-Variant haben"


def test_notifs_clear_all_button_uses_confirmModal(index_html):
    """Inline-onClick fuer 'Alle Benachrichtigungen löschen' muss _confirmModal nutzen.

    Pattern: title:'Alle Benachrichtigungen löschen' → onClick: async ()=>{... _confirmModal ...}
    """
    # Suche das Inline-onClick mit "notifications/clear" — dort muss _confirmModal davor stehen
    m = re.search(
        r"onClick:\s*async\s*\(\)\s*=>\s*\{\s*if\(!await\s+_confirmModal\([\s\S]{0,700}?notifications/clear",
        index_html,
    )
    assert m, "Alle-loeschen-Notifs-Button ohne _confirmModal — Bug-Regression v3.9.327"


# v3.9.328 — Material deleteSuppOrd + deleteCatalog --------------------------

# v3.9.958 — WARUM DIE ZWEI RENDER-MUSTER GELOCKERT WURDEN
# ────────────────────────────────────────────────────────
# Sie verlangten `{` UNMITTELBAR gefolgt von `onClick:`. In v3.9.958 haben beide
# Knoepfe ein `title` und ein `aria-label` bekommen — sie trugen als ganzen
# Inhalt ein 🗑 und hatten fuer eine Vorlesehilfe keinen Namen. Damit steht
# zwischen `{` und `onClick:` jetzt etwas, und beide Riegel wurden rot, OBWOHL
# die geschuetzte Eigenschaft unveraendert ist:
#
#   canDo("material_delete",curUser)&&React.createElement('button',
#     { title: "Bestellung löschen", 'aria-label': …, onClick: ()=>deleteSuppOrd(…
#
# Sie haben also die REIHENFOLGE DER EIGENSCHAFTEN gemessen, nicht die
# Rechtepruefung. Gelockert wird genau so weit, dass andere Eigenschaften
# davorstehen duerfen — und nicht weiter:
#   * hoechstens 300 Zeichen zwischen `{` und `onClick`
#   * KEIN `createElement` darin. Ohne diese Schranke koennte das Muster die
#     Pruefung des einen Knopfes mit dem onClick eines ANDEREN verbinden und
#     waere gruen, waehrend der Loeschknopf offensteht.
# `test_die_gelockerten_rechtemuster_unterscheiden_noch` belegt, dass beide
# nach der Lockerung rot werden, wenn die Rechtepruefung fehlt. Ohne diesen
# Beleg waere das hier "eine Pruefung anpassen, damit sie gruen wird".
_MAT_GATE = (r'canDo\("material_delete",curUser\)\s*&&React\.createElement'
             r"\('button',\s*\{(?:(?!createElement)[\s\S]){0,300}?"
             r"onClick:\s*\(\)=>%s")


def test_deleteSuppOrd_render_has_canDo_guard(index_html):
    """deleteSuppOrd-Render-Button muss canDo('material_delete')-gated sein."""
    m = re.search(_MAT_GATE % "deleteSuppOrd", index_html)
    assert m, "deleteSuppOrd-Render ohne canDo-Guard — Bug-Regression v3.9.328"


def test_deleteCatalog_handler_has_canDo_guard(index_html):
    """deleteCatalog-Handler muss als ERSTES canDo('material_delete') pruefen."""
    m = re.search(
        r'const\s+deleteCatalog\s*=\s*async\s*\(catId\)\s*=>\s*\{[\s\S]{0,300}?if\(!canDo\("material_delete",curUser\)\)',
        index_html,
    )
    assert m, "deleteCatalog-Handler ohne canDo-Eingangs-Guard — Bug-Regression v3.9.328"


def test_deleteCatalog_render_has_canDo_guard(index_html):
    """deleteCatalog-Render-Button muss canDo-gated sein."""
    m = re.search(_MAT_GATE % "deleteCatalog", index_html)
    assert m, "deleteCatalog-Render ohne canDo-Guard — Bug-Regression v3.9.328"


def test_die_gelockerten_rechtemuster_unterscheiden_noch(index_html):
    """SELBSTPROBE zur Lockerung oben.

    Ein Muster, das nach einer Lockerung auf alles passt, meldet gruen und
    misst nichts mehr — und bei einer RECHTEPRUEFUNG heisst das: der
    Loeschknopf steht offen und niemand erfaehrt es. Also wird jedes der zwei
    Muster gegen eine absichtlich kaputte Fassung gefahren, in der die
    Rechtepruefung entfernt ist. Es MUSS dort ins Leere greifen.

    Zwei Mutationen je Knopf:
      (a) `canDo(...)&&` faellt weg          -> Knopf ohne Pruefung
      (b) ein createElement dazwischen       -> die Pruefung gehoert zu einem
                                                ANDEREN Element
    """
    for name in ("deleteSuppOrd", "deleteCatalog"):
        muster = _MAT_GATE % name
        assert re.search(muster, index_html), (
            "%s: das Muster findet den heilen Stand nicht — dann ist die "
            "Aussage unten wertlos." % name)

        # (a) Rechtepruefung entfernen
        kaputt_a = re.sub(
            r'canDo\("material_delete",curUser\)\s*&&(React\.createElement'
            r"\('button',\s*\{(?:(?!createElement)[\s\S]){0,300}?"
            r"onClick:\s*\(\)=>" + name + r")",
            r"\1", index_html, count=1)
        assert kaputt_a != index_html, (
            "%s: die Mutation (a) hat nichts geaendert — der Koeder greift "
            "nicht." % name)
        assert not re.search(muster, kaputt_a), (
            "%s: OHNE canDo-Pruefung meldet das Muster weiter einen Treffer. "
            "Die Lockerung in v3.9.958 hat ihm die Unterscheidungskraft "
            "genommen, und dieser Riegel wuerde einen offenen Loeschknopf "
            "durchlassen." % name)

        # (b) ein fremdes Element zwischen Pruefung und onClick
        kaputt_b = re.sub(
            r"(canDo\(\"material_delete\",curUser\)\s*&&React\.createElement"
            r"\('button',\s*\{)",
            r"\1 x:React.createElement('span',null,'y'),", index_html, count=1)
        assert kaputt_b != index_html, (
            "%s: die Mutation (b) hat nichts geaendert." % name)
        # Fuer den ERSTEN Treffer im Text muss das Muster jetzt scheitern.
        erster = re.search(
            r"canDo\(\"material_delete\",curUser\)\s*&&React\.createElement"
            r"\('button',\s*\{[\s\S]{0,400}", kaputt_b)
        assert erster and not re.search(
            r"^" + _MAT_GATE % r"\w+", erster.group(0)), (
            "Die Schranke \"kein createElement dazwischen\" greift nicht. "
            "Dann kann das Muster die Pruefung eines Knopfes mit dem onClick "
            "eines anderen verbinden.")


# Hygiene: Logout-Warning + AS-Duplikat sind dokumentierte legacy native-confirm-Stellen.
# Werden bewusst NICHT durch Heuristik geguarded (BUGHUNT_ALT_2026-06-12.md fuer Detail).
