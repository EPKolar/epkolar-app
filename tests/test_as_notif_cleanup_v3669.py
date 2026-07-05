"""v3.9.669 AS-Notif-Cleanup (Bug-Hunt-Subagent).

Eskalations-/Reminder-Notifs (as_eskalation/as_new) blieben nach Erledigung/Storno des
Scheins in der Glocke haengen. Jetzt im selben Notif-Pass entfernt — Mirror der
Material-Cleanup (setNotifications-Filter + ODB.save + SQ DELETE, Name-Match per
Titel-Suffix, offene Kunden ausgenommen), da die Notif-id ein Hash ist (keine schein-id).
"""


def test_cleanup_block_present(index_html):
    assert "Cleanup erledigter AS-Notifs" in index_html


def test_open_and_resolved_name_sets(index_html):
    assert "const _asOpenNames=new Set(_arbeitsscheine.filter(a=>AS_GRP_OFFEN.includes(a.scheinstatus)).map(a=>(a.kundName||\"\").trim()).filter(Boolean));" in index_html
    assert "const _asResolvedNames=_arbeitsscheine.filter(a=>!AS_GRP_OFFEN.includes(a.scheinstatus)).map(a=>(a.kundName||\"\").trim()).filter(Boolean);" in index_html


def test_types_and_persisted_delete(index_html):
    assert 'const _asTypes=new Set(["as_eskalation","as_new"]);' in index_html
    # der Cleanup-Block loescht persistent (Server-DELETE), nicht nur re-fire-skip
    seg = index_html.split('const _asTypes=new Set(["as_eskalation","as_new"]);')[1][:600]
    assert 'ODB.save("notifications",_keep)' in seg
    assert 'method:"DELETE"' in seg


def test_open_customer_excluded(index_html):
    assert "(n.title||\"\").endsWith(\": \"+rn)&&!_asOpenNames.has(rn)" in index_html
