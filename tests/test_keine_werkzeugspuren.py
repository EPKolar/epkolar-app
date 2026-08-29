# -*- coding: utf-8 -*-
"""index.html darf keine Spuren der Werkzeuge enthalten, die sie bearbeiten.

Ohne Versionsnummer im Namen: dieser Riegel sichert die ARBEITSWEISE, keine
App-Version.

WARUM ES DAS GIBT (29.08.2026)
──────────────────────────────
An einem Nachmittag ist ZWEIMAL dasselbe passiert. Ein Skript, das
Anker/Ersatz-Paare aus einer Textdatei anwendet, hat die TRENNZEILE zwischen
zwei Abschnitten der Paardatei mit in die Ersetzung gezogen:

    , React.createElement('button', { onClick: ()=>{doSync();}, ...
    # ============================ OPTION A ============================
    )

Mitten im React-Render. Die Datei parst damit nicht mehr - **die App startet
gar nicht.** Beim ersten Mal hiess die Zeile "OPTION B", beim zweiten "OPTION A";
derselbe Fehler, derselbe Anwender, eine Stunde auseinander.

WAS DABEI GRUEN BLIEB - und das ist der eigentliche Grund fuer diesen Riegel:

    node_check.py         gruen (prueft anders zusammengesetzt)
    _bracket_check.py     gruen - die Bilanz stimmte ZUFAELLIG, weil der
                          Changelog-Text eine Klammer beisteuerte, die die
                          fehlende ausglich

Gefangen hat es beide Male nur `test_integration_smoke`, das jeden
inline-Skriptblock EINZELN durch `node --check` schickt. Das ist gut, aber es
meldet einen Syntaxfehler irgendwo - nicht die Ursache.

Dieser Riegel nennt die Ursache. Er kostet nichts und ist trennscharf: in einer
HTML-Datei mit JavaScript beginnt **keine** gueltige Zeile mit `#`. Gemessen:
null Vorkommen im gesunden Stand.

Er faengt damit nicht nur Trennzeilen, sondern jede eingeschleppte Shell-,
Python- oder Markdown-Zeile - also die ganze Klasse "das Werkzeug hat sich
selbst mit hineingeschrieben".
"""
import re


def test_keine_zeile_beginnt_mit_einer_raute(index_html):
    treffer = [(i + 1, z[:90]) for i, z in enumerate(index_html.split(chr(10)))
               if re.match(r"^#", z)]
    assert not treffer, (
        "In index.html beginnen Zeilen mit '#'. In dieser Datei gibt es keine "
        "gueltige Zeile dieser Form - das ist mit hoher Wahrscheinlichkeit eine "
        "Trennzeile oder ein Kommentar, den ein Bearbeitungs-Skript "
        "hineingezogen hat. Die Datei parst dann nicht, und die App startet "
        "nicht:" + chr(10)
        + chr(10).join("   Zeile %d: %s" % t for t in treffer[:5])
    )


def test_keine_konfliktmarken(index_html):
    """Dieselbe Familie: Merge-Marken sind ebenfalls nie gueltig und wuerden
    still eine kaputte Datei erzeugen."""
    for marke in ("<<<<<<< ", "=======" + chr(10) + ">>>>>>> ", ">>>>>>> "):
        assert marke not in index_html, (
            "Konfliktmarke %r steht in index.html." % marke[:9]
        )


def test_umkehrprobe_der_riegel_kann_rot_werden(index_html):
    """Ohne diese Probe waere oben ein Riegel, der nur bezeugt, dass die Datei
    heute sauber ist - und der bei einer kaputten Regex still gruen bliebe."""
    # `</body>` steht MITTEN in einer Zeile (...</script></body></html>) - die
    # Marke muss deshalb mit einem eigenen Umbruch davor eingeschleust werden,
    # sonst landet sie nicht am Zeilenanfang. Diese Probe hat den Fehler in
    # sich selbst gefunden, bevor sie den Riegel bestaetigen konnte.
    kaputt = index_html.replace(
        "</body>",
        chr(10)
        + "# ============================ OPTION A ============================"
        + chr(10) + "</body>", 1)
    assert kaputt != index_html, "Rueckbau griff nicht"
    treffer = [i for i, z in enumerate(kaputt.split(chr(10))) if re.match(r"^#", z)]
    assert len(treffer) == 1, (
        "Die eingeschleppte Trennzeile wird nicht erkannt - dann misst der "
        "Riegel oben nichts."
    )
