"""TIME-Konstanten (v3.8.44 S1.3).

Verifiziert dass TIME_* Millisekunden-Konstanten existieren und
die Magic-Numbers 3600000 / 86400000 im Code eliminiert sind.
"""
from _hilfen import nur_code
import re


def test_time_second_defined(index_html):
    assert re.search(r"const TIME_SECOND\s*=\s*1000", index_html)


def test_time_minute_defined(index_html):
    assert re.search(r"const TIME_MINUTE\s*=\s*60\s*\*\s*TIME_SECOND", index_html)


def test_time_hour_defined(index_html):
    assert re.search(r"const TIME_HOUR\s*=\s*60\s*\*\s*TIME_MINUTE", index_html)


def test_time_day_defined(index_html):
    assert re.search(r"const TIME_DAY\s*=\s*24\s*\*\s*TIME_HOUR", index_html)


def test_time_week_defined(index_html):
    assert re.search(r"const TIME_WEEK\s*=\s*7\s*\*\s*TIME_DAY", index_html)


def test_magic_3600000_eliminated(index_html):
    """Regression-Guard: keine hardgecodete Stunden-ms mehr."""
    assert "3600000" not in index_html, (
        "3600000 (1h in ms) sollte durch TIME_HOUR ersetzt sein"
    )


def test_magic_86400000_eliminated(index_html):
    """Regression-Guard: keine hardgecodete Tag-ms mehr IM CODE.

    v3.9.909 NACHGEZOGEN - kommentarblind. Vorher stand hier
        assert "86400000" not in index_html
    also gegen die ROHE Datei. Damit schlug der Riegel an, sobald ein
    Erklaerkommentar die Zahl NENNT - und genau das ist passiert: der Kommentar
    zur Zeitumstellungs-Reparatur beschreibt, dass das Fenster frueher auf
    "bis-Mitternacht plus 86400000 Millisekunden" endete. Er dokumentiert also
    die Beseitigung der Zahl und wurde dafuer bestraft.

    Zaehlung zum Zeitpunkt der Umstellung: 1x roh, 0x im Code.

    Dieselbe Falle wie in diesem Repo mehrfach zuvor - ein Riegel, der auf
    Wortlaut prueft, misst frueher oder spaeter den Kommentar mit. Die Aussage
    ist unveraendert und sogar schaerfer: die Zahl darf im CODE nicht vorkommen,
    im Erklaertext sehr wohl."""
    code = nur_code(index_html)
    assert "86400000" not in code, (
        "86400000 (1d in ms) steht wieder im Code - es gibt TIME_DAY. "
        "Und Vorsicht: ein Tag ist nicht immer 86400000 ms lang; ueber die "
        "Zeitumstellung gehoert kalendarisch gerechnet (siehe v3.9.909)."
    )


def test_time_hour_used(index_html):
    """Mind. 1 Nutzung von TIME_HOUR im Code."""
    # Suche außerhalb der Definition
    matches = re.findall(r"TIME_HOUR", index_html)
    assert len(matches) >= 2, f"TIME_HOUR kaum genutzt: {len(matches)} Treffer"


def test_time_day_used(index_html):
    matches = re.findall(r"TIME_DAY", index_html)
    assert len(matches) >= 2, f"TIME_DAY kaum genutzt: {len(matches)} Treffer"
