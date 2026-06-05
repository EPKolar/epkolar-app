"""v3.9.139 — FIX: Plan-Viewer leer ('geht gar nix'). Auto-Select erster Plan + geteilte Toolbar."""


def test_autoselect_first_plan(index_html):
    # Kern-Fix: kein Plan ausgewählt → leerer Viewer. Jetzt Auto-Select des ersten Plans.
    assert "if(plans && plans.length && (!selPlan || !plans.find(pl=>pl.id===selPlan.id))) setSelPlan(plans[0]);" in index_html
    assert "},[plans, selPlan]);" in index_html


def test_shared_filter_applies_to_plan_and_list(index_html):
    # Geteilte Toolbar: EIN gefilterter Satz für Plan-Pins UND Liste
    assert "const _vpFiltered=_react.useMemo.call(void 0, ()=>{const _q=(filterSearch||\"\").trim().toLowerCase();" in index_html
    assert "tickets: _vpFiltered" in index_html  # Plan-Pins respektieren Filter
    assert "_vpFiltered.map((t,i)=>{" in index_html  # Liste nutzt denselben Satz
