"""v3.9.481 — Projekt-Form: Baustellen-Straße zur Adresse (Straße+PLZ+Ort) relokalisiert."""
import pathlib

SRC = pathlib.Path(__file__).resolve().parent.parent / "index.html"
HTML = SRC.read_text(encoding="utf-8")


def test_strasse_field_in_address_block():
    # neues kombiniertes Straße/Hausnr.-Feld, an form.strasse gebunden
    assert '"Straße / Hausnr."' in HTML, "Straße/Hausnr.-Feld fehlt in der Adress-Zeile"
    assert "Baustellen-Straße zur Adresse gezogen" in HTML


def test_no_duplicate_bare_strasse_input_for_form_strasse():
    # Es darf nur EIN form.strasse-Input geben (jetzt "Straße / Hausnr." bei der Adresse);
    # die alte bare-Label-"Straße"-Variante, die form.strasse band, wurde entfernt → kein Doppel-Binding.
    # (Die "Straße" im Arbeitsschein-Formular bindet form.kundStr, nicht form.strasse → unberührt.)
    assert '"Straße"), React.createElement(\'input\', { value: form.strasse' not in HTML, \
        "alte Kundenkontakt-Straße (bare Label, form.strasse) noch vorhanden → Doppel-Binding"
    assert HTML.count("value: form.strasse") == 1, "es darf genau ein form.strasse-Eingabefeld geben"


def test_strasse_still_persisted_in_state():
    # strasse bleibt Teil von emptyProj + editProject (wird via body:form gespeichert)
    assert 'strasse:""' in HTML, "strasse nicht mehr im emptyProj-State"
    assert "strasse:p.strasse||" in HTML, "editProject lädt strasse nicht mehr"
