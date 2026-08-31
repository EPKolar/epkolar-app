# -*- coding: utf-8 -*-
"""v3.9.926 - Punkt 32: die Mobil-Ansicht, zusammenhaengend gemessen.

ROT, SOLANGE DIE ANKER/ERSATZ-PAARE NICHT ANGEWENDET SIND. Diese Datei
beschreibt den Zustand NACH der Aenderung; vorher schlagen die Riegel
ordnungsgemaess fehl. Das ist beabsichtigt und kein Defekt.

WAS GEMESSEN WURDE, BEVOR ETWAS GEAENDERT WURDE
───────────────────────────────────────────────
Mit `scripts/mob_ansicht_messen.py` (neu) auf VIER Geraetegroessen und DREI
Browserleisten-Faellen, mit einer Saat aus echten Faellen (sechs Kunden mit
Namen wie "Wohnungseigentuemergemeinschaft Krems-Stein, Steiner Landstrasse
42-46", mehrzeilige Arbeitsanweisungen, drei Monteure mit oesterreichischen
Namen). Netz aus, wie auf einer Baustelle.

  Geraet     Leiste  nutzbar  erste AS-Karte   rollen bis sichtbar
  360x740      0       686        y = 907           222 px
  360x740     56       630        y = 907           278 px
  360x740    100       586        y = 907           322 px
  390x844      0       786        y = 911           126 px
  390x844    100       686        y = 911           226 px
  390x900      0       842        y = 911            70 px
  390x900    100       742        y = 911           170 px
  414x896      0       838        y = 891            54 px
  414x896    100       738        y = 891           154 px

"nutzbar" ist NICHT die Fensterhoehe. Zwei Dinge gehen ab:
  * die Browserleiste (0 im Vollbild, 56 bei Chrome/Android, 100 bei
    Safari/iOS mit oberer Leiste und unterer Tableiste),
  * die eigene Fussleiste der App (.bottom-nav, position:fixed, GEMESSEN
    54-58 px). #root traegt padding-bottom 70px, das verhindert nur, dass
    der Inhalt UNTER ihr endet - die Bildflaeche gibt es nicht zurueck.

Auf KEINER der vier Groessen ist der erste Arbeitsschein ohne Rollen zu
sehen. v3.9.924 hatte 858 von 900 gemessen und ausdruecklich notiert: "auf
einem Geraet mit Browserleiste wieder nicht". Diese Messung sagt: auch OHNE
Browserleiste nicht, sobald das Geraet offline ist - die zwei Hinweisbalken
("2 Aenderungen warten auf Sync", "Server nicht erreichbar") kosten
zusammen 109 px, und offline ist auf einer Baustelle der Normalfall.

WOHIN DIE 907 PIXEL GEHEN (gemessen, 360x740, Netz aus)
───────────────────────────────────────────────────────
   56 px  Sync-Balken
   91 px  Kopfzeile
   53 px  Offline-Balken
  110 px  Ueberschrift + OFFA-Knoepfe
  259 px  KACHELBLOCK  <- der groesste einzelne Block
   48 px  Reiterzeile (Liste / QR / Kalender / Dispo)
   48 px  Schnellfilter-Chips
   94 px  Suche + Filter-Aufklapper
   18 px  Zaehlzeile
   44 px  Sortierzeile

Der Kachelblock ist mit Abstand der groesste Posten und der einzige, der
gemessen NICHTS enthaelt, was nicht drei Zeilen tiefer noch einmal stuende:
v3.9.924 hat per Klickprobe belegt, dass die elf Kacheln genau die elf Werte
setzen, die das Status-Auswahlfeld ohnehin anbietet.

DIE AENDERUNG
─────────────
Am Telefon steht der Kachelblock in EINER quer rollbaren Zeile statt in vier
untereinander. Keine Kachel weniger, keine Zahl weniger, kein Klick weniger,
kein Tastaturzugang weniger - nur die Geometrie. Dieselbe Bauart wie
.epk-ruhig (v918), .epk-flach (v920), .epk-leiste (v924).

Das Quer-Rollen ist kein neuer Einfall: die Schnellfilter-Leiste unmittelbar
darunter macht das seit v3.5.74 (overflowX auto, WebkitOverflowScrolling
touch). Der Vorschlag uebernimmt das Hausmuster.

GEMESSEN NACHHER (dieselbe Saat, dieselben Schirme)
───────────────────────────────────────────────────
  Kachelblock 259 -> 64 px auf allen vier Groessen.

  Geraet     Leiste  nutzbar  erste AS-Karte   rollen
  360x740      0       686        y = 712        27 px
  360x740    100       586        y = 712       127 px
  390x844      0       786        y = 716         0 px   sichtbar
  390x844    100       686        y = 716        31 px
  390x900    100       742        y = 716         0 px   sichtbar
  414x896    100       738        y = 697         0 px   sichtbar

Auf drei der vier Geraete ist der erste Arbeitsschein danach OHNE ROLLEN
sichtbar, auch im schlechtesten Browserleisten-Fall.

Gemessen wurde das an einer KOPIE mit angewendeten Paaren, nicht an der ins
Fenster eingespielten Fassung. Der Unterschied war diesmal der ganze Punkt:
die eingespielte Fassung meldete ebenfalls 64 px, die wirklich geaenderte
Datei zuerst 166 - siehe
test_die_kacheln_werden_nicht_als_platzhalter_gerechnet.

WAS DIE AENDERUNG NICHT LOEST - ausdruecklich
─────────────────────────────────────────────
Auf 360x740 (verbreitetes Android) bleiben im Safari-Fall 127 px zu rollen.
Der Rest des Vorbaus besteht aus Bedienelementen und aus zwei Hinweisbalken,
die etwas Wahres sagen. Wer dort weiter will, muss WEGNEHMEN.

EIN NEBENBEFUND, DER MITGEHT
────────────────────────────
Auf 360 px breit schneidet der Kachelblock HEUTE schon Text ab, lautlos:
Kachel 11 ("Fertig (alle)") ist dort 111 px breit, ihre Unterzeile
"erledigt+abgerechnet" laeuft aus dem Kasten (die Kachel traegt
overflow:hidden - die Lehre aus v3.9.115). Mit der festen Mindestbreite von
118 px verschwindet der Beschnitt; nachgemessen mit allen Werten auf
"12.345", also der groessten Zahl, die in diesem Haus je in einer AS-Kachel
stehen kann: null Beschnitt auf allen vier Groessen.

WAS GEMESSEN UND DESHALB NICHT ANGEFASST WURDE
──────────────────────────────────────────────
  * TIPPZIELE. Am Rechner waren 22 px gemessen worden. Am Telefon ist das
    KEIN Problem: das Stylesheet traegt bei max-width 600 drei Regeln -
    button {min-height:44px} (:261), input/select/textarea {min-height:44px}
    (:265) und [role="button"] {min-height:44px;min-width:44px} (:218).
    Gemessen: 68 Tippziele in der Arbeitsschein-Liste, 46 in der
    Zeiterfassung, davon KEINES unter 24 px und genau EINES unter 44
    (der Knopf "OFFA Excel", 36-40 px hoch, aus .header-row .mob-stack
    button {min-height:40px}). Auch die winzig aussehenden Griffe der
    Zeiterfassung (Bearbeiten/Loeschen, Polsterung 2px 4px, Schrift 10 px)
    messen 44x44 - die role-Regel deckt sie.
  * UEBERBREITE. html und body tragen bei <=600px overflow-x:hidden
    (:254). Was rechts hinausragt, waere weg und nicht errollbar. Gemessen:
    null Stellen auf allen vier Groessen, in beiden Ansichten. Die Null ist
    durch eine Positivprobe gedeckt (ein absichtlich 200 px zu breiter
    Kasten wird gefunden).
  * ZEILENKLAMMERN in der Arbeitsschein-Karte: 16-17 geklammerte Stellen,
    davon kappt keine. Auch diese Null ist durch eine Positivprobe gedeckt.

ZWEI BEFUNDE, DIE HIER NUR NOTIERT UND NICHT GEAENDERT WERDEN
─────────────────────────────────────────────────────────────
Beide gehoeren nicht zur Geometrie und haetten diese Aenderung vermischt.

  1. DIE ZEITERFASSUNG ZEIGT BEI 401 EINE LEERE WOCHE, OBWOHL DIE STUNDEN
     IM GERAET LIEGEN. Gemessen 390x900: fuenf Eintraege fuer M1 in dieser
     Woche im Zwischenspeicher, auf dem Schirm null. Mit abgebrochenem Netz
     erscheinen sie. Der Grund steht im Quelltext: _sbGet gibt bei 401/403
     ein leeres Array im ERFOLGSPFAD zurueck (:2071, v3.9.910 haengt ihm
     einen Grund an). loadWeek (:25132) nimmt dieses leere Array als
     Antwort; sein eigener Auffangzweig auf den Zwischenspeicher liegt im
     .catch und wird nur erreicht, wenn fetch WIRFT. Ein abgelaufener Zugang
     bei gutem Empfang sieht damit aus wie eine Woche ohne Stunden.
  2. IN DER MOBIL-KARTE FEHLEN SACHBEARBEITER UND PROJEKTNUMMER. Gemessen
     an allen sechs gesaeten Scheinen: am Rechner stehen beide in der Zeile,
     am Telefon in keiner Karte. Die Bedienelemente ebenso: Zeile 4 select
     und 2 input, Karte 0 und 0 (die vier Knoepfe bleiben). Das ist die
     Bestaetigung des v3.9.918-Befundes auf allen vier Geraetegroessen.
     Nicht bestaetigt hat sich dagegen die Vermutung, die Karte verliere
     mehr Text als die Zeile: die Arbeitsanweisung wird an BEIDEN Stellen
     nach der ersten Zeile abgeschnitten (gemessen 54-102 von 178-254
     Zeichen, Karte und Zeile jeweils gleich).
"""
import re

from _hilfen import nur_code

BLOCK_START = 'className: "kpi-grid epk-leiste'
BLOCK_ENDE = 'className: "tab-bar"'


def _kachelblock(index_html):
    i = index_html.find(BLOCK_START)
    assert i != -1, "Der Kachelblock der Arbeitsschein-Liste fehlt."
    j = index_html.find(BLOCK_ENDE, i)
    assert j != -1, "Die Reiterzeile hinter dem Kachelblock fehlt."
    return index_html[i:j]


# ══ Die Klasse selbst ═══════════════════════════════════════════════════════

def test_die_klasse_gibt_es_und_sie_haengt_an_kpi_grid(index_html):
    """Der Vorsatz .kpi-grid ist keine Zierde, sondern der Grund, warum die
    Regeln ueberhaupt greifen: .kpi-grid wird an elf Stellen der App benutzt,
    und mehrere Breiten-Regeln setzen dafuer !important. Ohne Vorsatz haetten
    die neuen Regeln dieselbe Spezifitaet und wuerden dort verlieren -
    lautlos, und nur auf manchen Schirmbreiten. Genau diesen Riegel traegt
    .epk-leiste seit v924; er gilt hier woertlich weiter."""
    treffer = re.findall(r"[^\s,{]*\.epk-kachelband", index_html)
    assert treffer, "Die Klasse .epk-kachelband steht nirgends im CSS."
    ohne = [t for t in treffer if not t.startswith(".kpi-grid")]
    assert not ohne, (
        "Diese .epk-kachelband-Regeln stehen ohne den Vorsatz .kpi-grid: %s. "
        "Sie verlieren dann gegen die !important-Regeln der Breiten-Bloecke."
        % ohne
    )


def test_die_klasse_wird_genau_einmal_angewendet(index_html):
    """GEGENPROBE gegen das Ueberlaufen. Es gibt elf kpi-grid-Bloecke in der
    App (Projekte, Fahrzeuge, Plaene, Chef-Portal ...). Gemessen wurde genau
    einer. Eine zweite Anwendung waere eine Aenderung an einem Reiter, fuer
    den kein einziger y-Wert vorliegt."""
    n = nur_code(index_html).count("epk-kachelband\"")
    assert n == 1, (
        "epk-kachelband ist %d mal angewendet, erwartet wird genau einmal "
        "(die Arbeitsschein-Liste)." % n
    )


def _umgebender_kopf(css, pos):
    """Der Kopf des Blocks, in dem `pos` steht - per Klammerzaehlung.

    ERSTER ANLAUF WAR FALSCH und schlug sofort an: er nahm einfach die
    letzte '}' und das letzte '@media' vor der Stelle. Die geschweiften
    Klammern der Regeln DAZWISCHEN hat er dabei mitgezaehlt, also war das
    Urteil vom Zufall abhaengig, wieviele Regeln im Block ueber der
    gesuchten stehen. Jetzt wird rueckwaerts gezaehlt, bis eine oeffnende
    Klammer ohne Partner kommt - das ist der Block, in dem die Regel liegt.
    """
    tiefe = 0
    i = pos
    while i > 0:
        i -= 1
        if css[i] == "}":
            tiefe += 1
        elif css[i] == "{":
            if tiefe == 0:
                start = css.rfind("}", 0, i)
                return css[start + 1:i].strip()
            tiefe -= 1
    return None


def test_die_klasse_wirkt_nur_am_telefon(index_html):
    """DIE ABGRENZUNG. Am Rechner ist der Kachelblock 161 px hoch und die
    erste Zeile steht bei y=722 - das ist die gemessene Lage aus v924, und
    sie wurde hier nicht neu gemessen. Was man nicht gemessen hat, aendert
    man nicht. Die Regeln muessen deshalb IN einem max-width-600px-Block
    stehen."""
    # Kommentare raus, bevor Klammern gezaehlt werden - ein '{' in einem
    # Erklaertext wuerde die Zaehlung sonst verschieben, und der Riegel
    # waere ab dem naechsten Kommentar zufaellig.
    css = re.sub(r"/\*.*?\*/", "", index_html, flags=re.S)
    stellen = list(re.finditer(r"\.kpi-grid\.epk-kachelband", css))
    assert stellen, "Keine .epk-kachelband-Regel gefunden."
    for regel in stellen:
        kopf = _umgebender_kopf(css, regel.start())
        assert kopf is not None, (
            "Eine .epk-kachelband-Regel steht in keinem Block und wuerde "
            "damit auch am Rechner wirken."
        )
        assert kopf.startswith("@media"), (
            "Eine .epk-kachelband-Regel steht in '%s' statt in einem "
            "@media-Block - sie wuerde auch am Rechner wirken." % kopf[:60]
        )
        assert "max-width" in kopf and "600px" in kopf, (
            "Eine .epk-kachelband-Regel steht in '%s' statt in einem "
            "max-width-600px-Block. Sie wuerde Schirme aendern, fuer die "
            "hier nichts gemessen wurde." % kopf[:60]
        )


def test_die_klasse_verbirgt_nichts(index_html):
    """DIE LEITREGEL, unveraendert aus v924: eine Kachel auf 0 ist eine
    Aussage ("da liegt nichts"), und wer sie verbirgt, nimmt die Aussage
    zurueck. Der billige Weg waere gewesen, am Telefon die Haelfte der
    Kacheln auszublenden - er ist hier ausdruecklich nicht gegangen worden."""
    regeln = re.findall(r"\.kpi-grid\.epk-kachelband[^{}]*\{[^{}]*\}",
                        index_html)
    assert len(regeln) >= 2, (
        "Nur %d epk-kachelband-Regeln gefunden - dann misst dieser Riegel "
        "womoeglich gar nichts." % len(regeln)
    )
    versteckt = [r for r in regeln if "display" in r and "none" in r]
    assert not versteckt, (
        "Eine epk-kachelband-Regel blendet etwas aus: %s. Der Vorbau sollte "
        "kuerzer werden, nicht luegen." % versteckt
    )


def test_der_block_rollt_quer_statt_umzubrechen(index_html):
    """Die eigentliche Geometrie. Ohne overflow-x waeren die elf Kacheln in
    einer nicht rollbaren Zeile - und die hinteren acht waeren weg, weil
    html/body bei <=600px overflow-x:hidden tragen (:254). Das waere kein
    Aufraeumen, sondern Datenverlust."""
    regel = re.search(
        r"\.kpi-grid\.epk-kachelband\s*\{([^{}]*)\}", index_html)
    assert regel, "Die Grundregel fuer .kpi-grid.epk-kachelband fehlt."
    inhalt = regel.group(1)
    assert "display: flex" in inhalt or "display:flex" in inhalt, (
        "Der Kachelblock steht nicht auf display:flex - dann bleibt das "
        "vierzeilige Raster und die Messung von 259 -> 64 px gilt nicht."
    )
    assert "nowrap" in inhalt, (
        "Ohne flex-wrap:nowrap bricht die Zeile wieder um und der Block ist "
        "so hoch wie vorher."
    )
    assert "overflow-x: auto" in inhalt or "overflow-x:auto" in inhalt, (
        "Ohne overflow-x:auto sind die hinteren Kacheln nicht erreichbar - "
        "html/body tragen bei <=600px overflow-x:hidden."
    )


def test_die_kacheln_haben_eine_mindestbreite(index_html):
    """DIE LEHRE AUS v3.9.115, hier zum zweiten Mal. Die Kachel traegt
    overflow:hidden. Ohne feste Mindestbreite schrumpfen die Flex-Kinder auf
    ihren Inhalt und schneiden Beschriftungen ab - lautlos.

    Gemessen wurde: 118 px reichen fuer alle elf Kacheln, auch mit allen
    Werten auf '12.345', auf allen vier Geraetegroessen. 111 px (das ist die
    Breite, die das heutige Drei-Spalten-Raster auf 360 px liefert) reichen
    NICHT - dort laeuft 'erledigt+abgerechnet' schon jetzt aus dem Kasten."""
    regel = re.search(
        r"\.kpi-grid\.epk-kachelband > div\s*\{([^{}]*)\}", index_html)
    assert regel, "Die Regel fuer die einzelne Kachel fehlt."
    inhalt = regel.group(1)
    m = re.search(r"min-width:\s*(\d+)px", inhalt)
    assert m, (
        "Die Kachel hat keine Mindestbreite. Als Flex-Kind schrumpft sie "
        "dann auf ihren Inhalt und schneidet Beschriftungen ab - genau der "
        "Fehler aus v3.9.115, und er waere lautlos."
    )
    assert int(m.group(1)) >= 112, (
        "Die Mindestbreite ist %s px. Gemessen wurde, dass 111 px auf einem "
        "360-px-Schirm 'erledigt+abgerechnet' abschneiden." % m.group(1)
    )
    assert "flex: 0 0 auto" in inhalt or "flex:0 0 auto" in inhalt, (
        "Ohne flex:0 0 auto darf die Kachel schrumpfen und die "
        "Mindestbreite ist wirkungslos."
    )


def test_die_kacheln_werden_nicht_als_platzhalter_gerechnet(index_html):
    """DER FUND, DER DIESE AENDERUNG FAST WERTLOS GEMACHT HAETTE.

    Die App traegt fuer JEDES div[role="button"][aria-label] in .main-pad die
    Regel content-visibility:auto mit contain-intrinsic-size auto 148px
    (:6203). Gedacht ist sie fuer die lange Arbeitsschein-Kartenliste. Die elf
    Kacheln sind aber ebenfalls div[role="button"][aria-label] und fallen
    darunter.

    Stehen sie nebeneinander, liegen die hinteren ausserhalb des Bildes,
    werden nie gerendert und melden ihre Platzhalterhoehe von 148 px. Ueber
    align-items:stretch zieht das ALLE Kacheln auf 162 px hoch - der Block
    waere dann 166 statt 64 px hoch, also SCHLECHTER als das heutige Raster
    mit 259 px es waere, wenn man die 64 erwartet.

    GEFUNDEN NUR, WEIL GEGEN DIE WIRKLICH GEAENDERTE DATEI NACHGEMESSEN
    WURDE. Die Fassung, die das Messgeraet mit --nachher in den Browser
    einspielt, meldete 64 px: dort waren die Kacheln vorher als Raster
    gerendert worden und behielten ihre echten Masse. Diesen Zustand gibt es
    beim Laden der Seite nie. Eine saubere Zahl aus einem Aufbau, den es in
    Wirklichkeit nicht gibt - genau die Krankheit dieser Woche, diesmal im
    eigenen Werkzeug."""
    regel = re.search(
        r"\.kpi-grid\.epk-kachelband > div\s*\{([^{}]*)\}", index_html)
    assert regel, "Die Regel fuer die einzelne Kachel fehlt."
    assert "content-visibility: visible" in regel.group(1), (
        "Die Kacheln behalten content-visibility:auto aus :6203. Die hinteren "
        "melden dann 148 px Platzhalterhoehe, align-items:stretch zieht alle "
        "mit, und der Block ist 166 statt 64 px hoch - im Browser gemessen."
    )
    # GEGENPROBE: die Regel, gegen die hier geschuetzt wird, muss es geben.
    # Verschwindet sie, ist dieser Riegel ein Denkmal und misst nichts mehr.
    assert ('.main-pad div[role="button"][aria-label]{content-visibility:auto'
            in index_html), (
        "Die Regel :6203 mit content-visibility:auto gibt es nicht mehr. Dann "
        "schuetzt dieser Riegel gegen nichts - pruefen, ob die Zeile "
        "content-visibility:visible noch gebraucht wird."
    )


def test_kpi_grid_selbst_bleibt_unangetastet(index_html):
    """GEGENPROBE zur Abgrenzung: zehn andere Reiter haengen an derselben
    Grundregel. Wer sie anfasst, aendert Bildschirme, die niemand gemessen
    hat."""
    assert (".kpi-grid { display: grid; grid-template-columns: repeat(4,1fr);"
            " gap: 12px; }" in index_html), (
        "Die Grundregel .kpi-grid wurde veraendert. Sie gilt fuer elf "
        "Bloecke in der App; gemessen wurde einer."
    )


def test_die_rechner_geometrie_aus_v924_bleibt_stehen(index_html):
    """Die neue Klasse tritt NEBEN .epk-leiste, nicht an ihre Stelle. Am
    Rechner darf sich nichts aendern; dort gilt weiter die Messung 405 ->
    161 px aus v924."""
    assert 'className: "kpi-grid epk-leiste epk-kachelband"' in index_html, (
        "Der Kachelblock traegt nicht beide Klassen. Faellt epk-leiste weg, "
        "ist der Rechner-Vorbau wieder 405 px hoch."
    )
    assert (".kpi-grid.epk-leiste { grid-template-columns: repeat(6,1fr)"
            in index_html), (
        "Die Sechs-Spalten-Regel vom Rechner aus v924 ist verschwunden."
    )


# ══ Die elf Kacheln bleiben, was sie sind ═══════════════════════════════════

def test_alle_elf_kacheln_behalten_ihren_klick(index_html):
    """DIE EIGENTLICHE EIGENSCHAFT, uebernommen aus v924. Der Befund war: die
    Kacheln SIND Bedienelemente, keine Dekoration - jede setzt filterStatus.
    Genau deshalb duerfen sie bleiben. Verlieren sie den Klick, waeren 64 px
    Dekoration uebrig, und die ganze Begruendung faellt.

    Im Browser nachgemessen: 11 von 11 Kacheln tragen role=button UND
    tabindex=0, vor wie nach der Aenderung."""
    block = _kachelblock(index_html)
    n = block.count("onClick: ()=>_scrollToScheinListe(")
    assert n == 4, (
        "Im Kachelblock haengen %d Klick-Zuweisungen, erwartet werden vier "
        "(Gesamt, Offen alle, die Schleife ueber AS_KPI_KACHELN, Fertig "
        "alle)." % n
    )


def test_es_sind_weiterhin_elf_kacheln(index_html):
    """Diese Version nimmt keine einzige weg - sie legt sie nebeneinander."""
    block = _kachelblock(index_html)
    assert block.count("React.createElement(Kpi, {") == 4, (
        "Im Kachelblock stehen nicht mehr vier Kpi-Aufrufe (drei feste plus "
        "einer in der Schleife)."
    )
    assert block.count("AS_KPI_KACHELN.map(") == 1, (
        "Die Status-Kacheln kommen nicht mehr genau einmal aus "
        "AS_KPI_KACHELN."
    )


def test_das_status_auswahlfeld_bleibt_der_zweite_weg(index_html):
    """Die Bedingung, unter der eine quer rollbare Zeile billig ist: wer eine
    Kachel nicht findet, muss denselben Wert anders erreichen. Das
    Auswahlfeld liest AS_STATUS, nicht AS_KPI_KACHELN - es bietet also weiter
    jeden Status an."""
    marke = '{ value: "offen_bearb"}'
    assert index_html.count(marke) == 1, (
        "Der Anker fuers Status-Auswahlfeld ist nicht mehr eindeutig "
        "(%d Treffer)." % index_html.count(marke)
    )
    i = index_html.find(marke)
    feld = index_html[i - 320:i + 520]
    assert "value: filterStatus, onChange:" in feld
    assert "Object.entries(AS_STATUS).map(" in feld, (
        "Das Status-Auswahlfeld liest nicht mehr AS_STATUS."
    )


# ══ Umkehrprobe ═════════════════════════════════════════════════════════════

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    """Sechs Rueckbauten, sechs Riegel. Ein Riegel, der seinen eigenen
    Rueckbau nicht bemerkt, ist im Bestand dieses Repos mehrfach gruen
    gewesen und hat nichts gemessen."""
    # 1. Klasse wieder abgenommen
    z1 = index_html.replace(' epk-kachelband"', '"', 1)
    assert z1 != index_html, "Rueckbau 1 griff nicht"
    assert nur_code(z1).count("epk-kachelband\"") == 0, (
        "Umkehrprobe: eine abgenommene Klasse bliebe unbemerkt"
    )

    # 2. Klasse ein zweites Mal angewendet
    z2 = index_html.replace('className: "kpi-grid", style: {marginBottom:16}',
                            'className: "kpi-grid epk-kachelband", '
                            'style: {marginBottom:16}', 1)
    assert z2 != index_html, "Rueckbau 2 griff nicht"
    assert nur_code(z2).count("epk-kachelband\"") == 2, (
        "Umkehrprobe: eine zweite Anwendung bliebe unbemerkt"
    )

    # 3. Mindestbreite entfernt - der lautlose Beschnitt aus v3.9.115
    z3 = re.sub(r"(\.kpi-grid\.epk-kachelband > div \{[^{}]*?)"
                r"min-width: \d+px !important; ", r"\1", index_html, count=1)
    assert z3 != index_html, "Rueckbau 3 griff nicht"
    r3 = re.search(r"\.kpi-grid\.epk-kachelband > div\s*\{([^{}]*)\}", z3)
    assert r3 and not re.search(r"min-width:\s*\d+px", r3.group(1)), (
        "Umkehrprobe: eine fehlende Mindestbreite bliebe unbemerkt"
    )

    # 4. Quer-Rollen entfernt - die hinteren acht Kacheln waeren weg
    z4 = index_html.replace("overflow-x: auto !important;", "", 1)
    assert z4 != index_html, "Rueckbau 4 griff nicht"
    r4 = re.search(r"\.kpi-grid\.epk-kachelband\s*\{([^{}]*)\}", z4)
    assert r4 and "overflow-x" not in r4.group(1), (
        "Umkehrprobe: ein fehlendes overflow-x bliebe unbemerkt"
    )

    # 5. content-visibility zurueckgenommen - der Block waere 166 statt 64 px
    z5b = index_html.replace("content-visibility: visible !important; ", "", 1)
    assert z5b != index_html, "Rueckbau 5 griff nicht"
    r5 = re.search(r"\.kpi-grid\.epk-kachelband > div\s*\{([^{}]*)\}", z5b)
    assert r5 and "content-visibility" not in r5.group(1), (
        "Umkehrprobe: ein fehlendes content-visibility bliebe unbemerkt - "
        "und genau das war der Fehler im ersten Entwurf"
    )

    # 6. Einer Kachel den Klick genommen
    z6 = index_html.replace(
        'sub: "zu erledigen" , color: "#eab308", i: 1, '
        'onClick: ()=>_scrollToScheinListe("offen_bearb")',
        'sub: "zu erledigen" , color: "#eab308", i: 1', 1)
    assert z6 != index_html, "Rueckbau 6 griff nicht"
    assert _kachelblock(z6).count(
        "onClick: ()=>_scrollToScheinListe(") == 3, (
        "Umkehrprobe: eine Kachel ohne Klick bliebe unbemerkt"
    )
