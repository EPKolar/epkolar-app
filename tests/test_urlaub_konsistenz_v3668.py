"""v3.9.668 Urlaub-Anzeige-Konsistenz (Bug-Hunt-Subagent, autonom triagiert).

- _yearStK: abgelehnter Urlaub zaehlt nicht mehr in urlaubStd (= Gen+Ausstehend, wie
  _resturlaubK) → Mirror/Kalender/Export/Guenther-Card konsistent; Legacy-Kurzformen
  krank/za auf kanonische AT_T-Keys normalisiert (sonst still gedroppt).
- _krankRows: Legacy "krank" mit aufgenommen; Std-Fallback via _stdVonTagK wie Bilanz.
- MitarbeiterView bekommt approvals-Prop → _absStats filtert auch approvals-Map-Ablehnungen.
"""


def test_yearstk_legacy_normalize(index_html):
    assert 'let t=v.type;if(t==="krank")t="krankenstand";else if(t==="za")t="zeitausgleich";' in index_html


def test_yearstk_urlaubstd_excl_rejected(index_html):
    assert 'const _appr=(t==="urlaub")?_resolveApprK(abs,approvals,key):null;if(r[t]!==undefined&&!(t==="urlaub"&&_appr==="abgelehnt")){r[t]++;r[t+"Std"]+=h;}' in index_html
    # alte unbedingte Zaehlung weg
    assert 'const t=v.type;if(r[t]!==undefined){r[t]++;r[t+"Std"]+=h;}if(t==="urlaub"){const _appr=_resolveApprK' not in index_html


def test_krankrows_legacy_and_fallback(index_html):
    assert '(v.type!=="krankenstand"&&v.type!=="krank")||!key.startsWith(m.n+"_")' in index_html
    assert 'hours:(parseFloat(v.hours)||_stdVonTagK(new Date(String(date).slice(0,10)+"T00:00:00"),_wocheOfK(_kontFor,m.n)))' in index_html


def test_mitarbeiterview_approvals_prop(index_html):
    # v3.9.703: Signatur um users,setUsers erweitert (automatische Login-Anlage) — approvals bleibt.
    assert "function MitarbeiterView({monteure,setMonteure,monteurProjekte,setMonteurProjekte,ww,curUser,projects,fahrzeuge,abs,approvals,entries,arbeitsscheine,onNav,users,setUsers}){" in index_html
    assert "abs: abs, approvals: absApprovals, entries: entries" in index_html


def test_absstats_uses_approvals(index_html):
    assert 'if(v.type==="urlaub"&&_resolveApprK(abs,approvals,k)==="abgelehnt")return;' in index_html
    assert '_resolveApprK(abs,null,k)' not in index_html
