"""v3.9.109 — Regression: AbsView TDZ-Crash (Urlaub-Tab lud nicht).

v3.9.107 machte absTabIds von isAdmin abhängig, aber isAdmin wurde ERST DANACH deklariert →
"Cannot access 'isAdmin' before initialization" → AbsView (Urlaub-Tab) crashte beim Rendern.
Statische Tests rendern AbsView nicht, daher schlüpfte es durch. Dieser Guard prüft die
Deklarations-Reihenfolge: jede const, die isAdmin/absTabIds nutzt, muss NACH deren Deklaration stehen.
"""


def _absview(index_html):
    start = index_html.index("function AbsView(")
    # bis zur nächsten Top-Level-Funktion grob begrenzen
    end = index_html.index("\nfunction ", start + 10)
    return index_html[start:end], start


def test_isadmin_declared_before_abstabids(index_html):
    body, _ = _absview(index_html)
    i_admin = body.index("const isAdmin=")
    i_tab = body.index("const absTabIds=")
    assert i_admin < i_tab, (
        "AbsView: const isAdmin MUSS vor const absTabIds stehen (absTabIds nutzt isAdmin → sonst TDZ-Crash)"
    )


def test_single_isadmin_in_absview(index_html):
    body, _ = _absview(index_html)
    assert body.count("const isAdmin=") == 1, (
        "AbsView darf isAdmin nur EINMAL deklarieren (Doppel-Deklaration = SyntaxError)"
    )


def test_abstabids_uses_isadmin(index_html):
    body, _ = _absview(index_html)
    assert 'const absTabIds=isAdmin?' in body, "absTabIds-Clamp (isAdmin-gated) muss erhalten bleiben"
