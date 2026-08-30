"""v3.9.109 — Regression: AbsView TDZ-Crash (Urlaub-Tab lud nicht).

v3.9.107 machte absTabIds von isAdmin abhängig, aber isAdmin wurde ERST DANACH deklariert →
"Cannot access 'isAdmin' before initialization" → AbsView (Urlaub-Tab) crashte beim Rendern.
Statische Tests rendern AbsView nicht, daher schlüpfte es durch. Dieser Guard prüft die
Deklarations-Reihenfolge: jede const, die isAdmin/absTabIds nutzt, muss NACH deren Deklaration stehen.
"""


from _hilfen import nur_code


def _absview(index_html):
    # KOMMENTARBLIND seit v3.9.913: geschnitten und gezaehlt wird auf nur_code().
    # Grund: unten steht eine ZAHL. Ein erklaerender Kommentar in AbsView, der
    # "const isAdmin=" zitiert, haette sie auf 2 gehoben (falsch rot) - und
    # umgekehrt bliebe sie 1, wenn die echte Deklaration verschwindet und nur
    # der Kommentar stehenbleibt (falsch gruen). Beides ist im Repo passiert.
    code = nur_code(index_html)
    start = code.index("function AbsView(")
    # bis zur nächsten Top-Level-Funktion grob begrenzen
    end = code.index("\nfunction ", start + 10)
    return code[start:end], start


def test_isadmin_declared_before_abstabids(index_html):
    body, _ = _absview(index_html)
    i_admin = body.index("const isAdmin=")
    i_tab = body.index("const absTabIds=")
    assert i_admin < i_tab, (
        "AbsView: const isAdmin MUSS vor const absTabIds stehen (absTabIds nutzt isAdmin → sonst TDZ-Crash)"
    )


def test_single_isadmin_in_absview(index_html):
    body, _ = _absview(index_html)
    # DIE ZAHL BLEIBT: hier IST sie die Aussage. "Genau eine Deklaration" laesst
    # sich nicht durch benannte Stellen ersetzen - wo eine zweite auftaucht,
    # weiss man vorher nicht, und genau das soll der Riegel finden.
    # Gemessen kommentarblind (v3.9.913): 1 - unveraendert gegenueber vorher,
    # weil heute kein Kommentar in AbsView den Text zitiert. Der Umbau ist hier
    # Vorsorge, keine Korrektur.
    assert body.count("const isAdmin=") == 1, (
        "AbsView darf isAdmin nur EINMAL deklarieren (Doppel-Deklaration = SyntaxError)"
    )


def test_abstabids_uses_isadmin(index_html):
    body, _ = _absview(index_html)
    assert 'const absTabIds=isAdmin?' in body, "absTabIds-Clamp (isAdmin-gated) muss erhalten bleiben"
