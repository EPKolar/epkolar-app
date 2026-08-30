"""Static tests for CSP manifest-src directive (v3.8.48 hotfix).

Verifies the PWA manifest can be loaded via blob: URL without CSP violation.
"""
import re


def test_csp_meta_tag_exists(index_html):
    assert 'http-equiv="Content-Security-Policy"' in index_html, (
        "CSP meta tag must be present"
    )


def test_csp_has_manifest_src(index_html):
    m = re.search(
        r'<meta\s+http-equiv="Content-Security-Policy"\s+content="([^"]+)"',
        index_html,
    )
    assert m, "CSP meta tag content not parseable"
    content = m.group(1)
    assert "manifest-src" in content, (
        "CSP must declare manifest-src directive (was falling back to default-src)"
    )
    assert "manifest-src 'self' blob:" in content, (
        "manifest-src must allow 'self' and blob: for PWA install manifest"
    )


_CSP = r'<meta\s+http-equiv="Content-Security-Policy"\s+content="([^"]+)"'


def test_csp_manifest_src_not_duplicated(index_html):
    """Gezaehlt wird IM CSP-Tag, nicht in der ganzen Datei (30.08.2026).

    Vorher stand hier `index_html.count("manifest-src") == 1` - ein
    Gesamtzaehler ueber 3,55 MB fuer eine Direktive, die in GENAU EINEM
    Meta-Tag lebt. Zwei Richtungen gingen daneben:

      falsch ROT:   ein Erklaerkommentar, der "manifest-src" nennt, hebt die
                    Zahl auf 2 - obwohl die CSP unveraendert ist. Genau das ist
                    im Repo mehrfach passiert (siehe tests/_hilfen.py).
      falsch GRUEN: stuende die Direktive zweimal im Tag und einmal weniger
                    woanders, bliebe die Summe 1.

    Und ausgerechnet dieser Riegel liess sich bis heute NICHT einfach auf
    nur_code() umstellen: nur_code() verschluckte den halben Kopf, weil
    `https://*.tile.openstreetmap.org` als Kommentarbeginn gelesen wurde -
    `nur_code(index_html).count("manifest-src")` war 0. Deshalb hier die
    benannte Stelle statt der Gesamtzahl: sie haengt an keinem der beiden
    Geraete.
    """
    treffer = re.findall(_CSP, index_html)
    assert len(treffer) == 1, (
        "Es gibt %d CSP-Meta-Tags. Bei mehreren gilt im Browser die "
        "SCHNITTMENGE - dann sagt kein einzelnes Tag mehr, was erlaubt ist."
        % len(treffer)
    )
    n = treffer[0].count("manifest-src")
    assert n == 1, (
        "manifest-src steht %d mal IM CSP-Tag. Doppelte Direktiven werden "
        "geschnitten, nicht vereinigt - die zweite kann die erste stillegen."
        % n
    )
