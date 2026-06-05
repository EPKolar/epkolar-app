"""v3.9.146 — Phase 4: Plan-Bild-Export mit Pin-Overlay (PNG)."""


def test_export_function(index_html):
    assert "const exportPlanImage = () => {" in index_html
    # Pin an x/y(%) auf Offscreen-Canvas, Zwei-Stufen-Farben
    assert "const px = (Number(t.x)/100) * out.width;" in index_html
    assert "const fill = t.color || (_hs ? TICKET_STATUS[t.status].c : \"#ffffff\");" in index_html
    assert "const border = t.assignee ? \"#22c55e\" : \"#9ca3af\";" in index_html
    assert "a.href = out.toDataURL('image/png');" in index_html


def test_export_button(index_html):
    assert 'onClick: exportPlanImage, title: "Plan mit Pins als Bild (PNG) exportieren"' in index_html
