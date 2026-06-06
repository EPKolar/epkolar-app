"""v3.9.153 — Agententeam-Welle-5 (Zeiterfassung): KW-DST-Fix + hidden-worker-Summen."""


def test_kwfromdate_utc_iso(index_html):
    # P1: UTC-ISO-Woche statt ms-Division (vorher KW-1 nach Frühjahrs-DST)
    assert "const u=new Date(Date.UTC(dt.getFullYear(),dt.getMonth(),dt.getDate()));const day=u.getUTCDay()||7;u.setUTCDate(u.getUTCDate()+4-day);" in index_html
    # alte ms-Division weg
    assert "const diff=Math.floor((dt-firstMon)/(7*864e5));return Math.max(1,diff+1);" not in index_html


def test_bwb_hidden_worker_excluded(index_html):
    # P2: KW-Summen nur über sichtbare Monteure
    assert "const _visIds=new Set(workers.map(w=>w.id));" in index_html
    assert index_html.count("_kwFromDate(d)===kw&&_visIds.has(e.monteur)") == 2
