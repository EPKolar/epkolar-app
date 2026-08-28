# -*- coding: utf-8 -*-
"""v3.9.875 - Der Dokumente-Tab verlor nach jedem Neuladen seine Kategorien.

BEFUND: Zwei Namenskonventionen fuer dieselben zwei Felder.

    _mapDocFromServer  lieferte   kat  / fileName
    die Oberflaeche    liest      cat  / filename   (so legt auch der Upload an)

Folge - jedes Mal, wenn ein Dokument vom Server kam statt frisch hochgeladen zu sein:
  * Kategorie fiel auf "Sonstiges" zurueck
  * das Endungs-Abzeichen zeigte "?"
  * die Suche fand Server-Dokumente NIE
  * der Download speicherte die Datei ohne Endung

Warum das so lange unbemerkt blieb: frisch Hochgeladenes war korrekt. Der Fehler
zeigte sich erst nach dem Neuladen - und da sah es nach "die Kategorie war wohl nie
gesetzt" aus statt nach einem Fehler.

FIX-ENTSCHEIDUNG: Der Mapper setzt BEIDE Namen. Nicht aus Bequemlichkeit, sondern
weil zwei Lesestellen (Kundenportal, openDoc) nur fileName kannten - ein reines
Umbenennen haette dort den Dateinamen zerstoert. Die beiden Lesestellen sind
zusaetzlich tolerant gemacht, sodass der Alias spaeter gefahrlos entfallen kann.
"""
import re


def _mapper(index_html):
    i = index_html.find("function _mapDocFromServer")
    assert i != -1, "_mapDocFromServer nicht gefunden"
    j = index_html.find("\n}", i)
    return index_html[i:j]


def test_mapper_liefert_den_namen_den_die_oberflaeche_liest(index_html):
    body = _mapper(index_html)
    assert "cat:d.category||" in body, (
        "Der Mapper setzt kein 'cat' - die Oberflaeche liest d.cat, also faellt die "
        "Kategorie nach jedem Neuladen auf 'Sonstiges':\n" + body[:400]
    )
    assert "filename:d.file_name||" in body, (
        "Der Mapper setzt kein 'filename' - dann zeigt das Endungs-Abzeichen '?' und "
        "der Download speichert ohne Dateiendung:\n" + body[:400]
    )


def test_alte_namen_bleiben_als_alias(index_html):
    """Bewusste Grenze: kat/fileName bleiben, solange noch jemand sie lesen koennte."""
    body = _mapper(index_html)
    assert "kat:d.category||" in body and "fileName:d.file_name||" in body, (
        "Die Alias-Felder wurden entfernt. Das ist erst erlaubt, wenn KEINE Lesestelle "
        "mehr d.kat oder d.fileName ohne Fallback verwendet - sonst verschwindet der "
        "Dateiname im Kundenportal."
    )


def test_beide_namen_kommen_aus_derselben_quelle(index_html):
    """Zwei Felder, ein Wert - sonst driften sie auseinander."""
    body = _mapper(index_html)
    assert body.count("d.category||") == 2, (
        "cat und kat kommen nicht beide aus d.category:\n" + body[:400]
    )
    # Nicht zaehlen: es gibt eine dritte, voellig legitime d.file_name-Stelle
    # (die Bild-Erkennung isImage). Deshalb die beiden Zuweisungen woertlich pruefen.
    assert "filename:d.file_name||\"\",fileName:d.file_name||\"\"," in body, (
        "filename und fileName stehen nicht als Paar aus derselben Quelle - dann "
        "koennen sie auseinanderdriften:\n" + body[:400]
    )


def test_lesestellen_sind_tolerant(index_html):
    """Die zwei Stellen, die frueher NUR fileName kannten, muessen beide Namen nehmen."""
    assert "const openDoc=d=>{_openFileUrl(d.dataUrl||d.fileUrl,d.filename||d.fileName||d.name);};" in index_html, (
        "openDoc liest nicht beide Namen - oeffnet man ein frisch hochgeladenes "
        "Dokument, faellt der Name sonst auf d.name zurueck."
    )
    assert "_openFileUrl(d.dataUrl,d.filename||d.fileName||d.name)" in index_html, (
        "Die Kundenportal-Lesestelle liest nicht beide Namen."
    )


def test_keine_lesestelle_ohne_fallback(index_html):
    """Riegel gegen Rueckfall: d.fileName / d.kat duerfen nirgends allein stehen."""
    for treffer in re.finditer(r"d\.fileName", index_html):
        umfeld = index_html[max(0, treffer.start() - 30):treffer.end() + 30]
        assert "d.filename||d.fileName" in umfeld or "fileName:d.file_name" in umfeld, (
            "d.fileName wird ohne d.filename-Fallback gelesen - genau der Fehler, "
            "der hier behoben wurde:\n" + umfeld
        )


def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    zurueck = index_html.replace("cat:d.category||\"\",kat:d.category||\"\",",
                                 "kat:d.category||\"\",", 1)
    assert zurueck != index_html, "Rueckbau griff nicht - Anker veraltet"
    assert "cat:d.category||" not in _mapper(zurueck), (
        "Umkehrprobe: der Kategorie-Riegel wuerde nicht anschlagen"
    )

    zurueck2 = index_html.replace("filename:d.file_name||\"\",fileName:d.file_name||\"\",",
                                  "fileName:d.file_name||\"\",", 1)
    assert zurueck2 != index_html, "Rueckbau 2 griff nicht - Anker veraltet"
    assert "filename:d.file_name||" not in _mapper(zurueck2), (
        "Umkehrprobe: der Dateinamen-Riegel wuerde nicht anschlagen"
    )
