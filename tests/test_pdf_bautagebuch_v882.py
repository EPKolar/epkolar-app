# -*- coding: utf-8 -*-
"""
v3.9.882 - Das Bautagebuch ist kein Nachweis, sondern ein Bildschirmfoto.

BEFUND (Code-Read 2026-08-28 gegen main c234235 / v3.9.878, alle Stellen
belegt, nichts geraten):

  1) Der Knopf "PDF" im Bautagebuch (index.html:19031) ist ein nacktes
     window.print() auf die LISTENANSICHT. Kein Briefkopf, keine Firma,
     kein Projekt, keine Seitenzahl, kein Unterschriftsfeld.
     Die SignaturePad-Komponente existiert seit langem (index.html:6208)
     und wird in Checklisten (:16084/:16085), Regieberichten (:11188/:11189)
     und PZE (:22749) benutzt - im Bautagebuch kommt sie nicht vor.

  2) window.print() liefert im DUNKELMODUS ein LEERES BLATT.
     .app-shell traegt inline color:V.tx (index.html:8996), im Dunkelmodus
     #f0f0f2. Die Druckregel (index.html:5899) setzt zwar
     body{background:#fff!important} - aber color:#1a1a1a OHNE !important,
     und der Inline-Stil des Kindes gewinnt ohnehin. Hintergruende druckt
     der Browser per Default nicht (kein print-color-adjust). Ergebnis:
     fast weisse Schrift auf weissem Papier. Default ist dunkel
     (let _dark=true, index.html:4713).

  3) window.print() druckt HOECHSTENS EINEN BILDSCHIRM.
     Die Projekt-Huelle ist inline height:100dvh + overflow:hidden, der
     Inhalt darin overflow-y:auto. Fuer die Hauptansichten dasselbe per
     @media(max-width:1199px){.app-shell{height:100dvh;overflow:hidden}
     .main-pad{overflow-y:auto}} - die Regel greift beim Drucken mit, weil
     die A4-Druckflaeche schmaler als 1199px ist. Keine Print-Ausnahme.
     Betrifft ALLE 13 window.print()-Knoepfe der App.

  4) Die Druckregel pflegt einen Selektor #print-stz (6x in index.html:5899)
     fuer ein Element, das es NIRGENDS gibt. Ein Druck-Stylesheet, das auf
     nichts zeigt - gruen und misst nichts.

  5) Das Wetter ist auf Kirchberg am Wagram hart verdrahtet
     (index.html:18862: const lat=48.46;const lon=15.74). Jede Baustelle in
     ganz Niederoesterreich bekommt dasselbe Wetter. Die Projekte tragen
     plz und ort (emptyProj :14941, Eingabefeld :15015), und der Geo-Weg
     existiert bereits: Tabelle plz_geo (sql/PLZ_GEO_v1.sql), Client-Load
     _sbGet("plz_geo") (:10212), Nominatim-Nachzieher (:4921).

  6) Geholt werden nur temperature_2m + weather_code (:18865/:18866) - also
     genau die zwei Werte, die fuer einen Verzugsnachweis NICHT reichen.
     Niederschlag und Wind fehlen. Die Temperatur wird zudem als gerundeter
     Tagesmittelwert aus max/min gespeichert (:18873) - der Frostwert, auf
     den es ankommt, wird dabei weggerechnet.

  7) Das Wetter wird beim WECHSEL DES DATUMS nicht neu geholt.
     autoFillWeather laeuft in startNewEntry mit dem HEUTIGEN Datum
     (:18888); das Datumsfeld (:18985) setzt nur form.datum. Ein
     nachgetragener Bericht traegt damit das Wetter von heute.

  8) Kein Riegel: ein halbjahresalter Eintrag ist heute noch frei
     ueberschreibbar. Es gibt keine Freigabe, keine Sperre, keine
     Aenderungshistorie (grep freigabe/gesperrt/locked im VBautag: 0), und
     das Loeschen ist ein echtes DELETE gegen PostgREST (:18942 -> :2742).
     Ins activity_log wird bei Bautagebuch-Schreibvorgaengen nichts
     geschrieben (activity_log-POSTs nur login/juprowa/error/view_boundary).

WAS DIESE DATEI PRUEFT
  Die Riegel 1-9 sind ROT, solange der Patch fehlt - das ist beabsichtigt
  und hier ausdruecklich vermerkt. Sie werden gruen, wenn
    - _genBautagPdf existiert und der Knopf ihn statt window.print() ruft,
    - das PDF Briefkopf (COMPANY_FOOTER), zwei Unterschriftsfelder und
      "Seite x von y" traegt,
    - das Wetter aus der Baustellen-PLZ kommt und Niederschlag + Wind holt,
    - das Datumsfeld das Wetter nachzieht,
    - die Druckregel Schriftfarbe erzwingt und die Scroll-Klammer loest,
    - der tote #print-stz-Selektor entweder ein Ziel hat oder weg ist.

  Die Riegel 10-13 sind heute GRUEN. Sie halten die BELEGE fest, auf denen
  die Befunde stehen (SignaturePad vorhanden, plz_geo-Weg vorhanden,
  Projekte tragen PLZ/Ort, Checklisten-PDF als Vorbild) - kippt einer davon,
  ist der Vorschlag hinfaellig und man merkt es hier.

  Ganz unten steht die UMKEHRPROBE: sie fuettert die Pruefkerne mit einem
  synthetischen guten und einem synthetischen kaputten Text und belegt,
  dass die Riegel ueberhaupt anschlagen koennen - sonst waere ein spaeteres
  Gruen wertlos.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import _extract_fn  # noqa: E402


# ══════════════════════════════════════════════════════════════════════════
# Pruefkerne - reine Funktionen ueber Text, damit die Umkehrprobe sie
# unabhaengig vom Repo-Stand fuettern kann.
# ══════════════════════════════════════════════════════════════════════════

def _k_pdf_hat_briefkopf(fn_text):
    """Traegt das PDF die Firmendaten aus der einen Quelle COMPANY_FOOTER?"""
    return "COMPANY_FOOTER" in fn_text


def _k_pdf_hat_zwei_unterschriften(fn_text):
    """Zwei Unterschriftsfelder - Auftragnehmer und Auftraggeber/OEBA."""
    return len(re.findall(r"Unterschrift|sig_|sigMA|sigKunde", fn_text)) >= 2


def _k_pdf_zaehlt_seiten(fn_text):
    return "getNumberOfPages" in fn_text


def _k_wetter_url_vollstaendig(text):
    """Fuer einen Verzugsnachweis zaehlen Niederschlag und Wind."""
    return ("precipitation" in text) and ("wind_speed" in text or "windspeed" in text)


def _k_druckregel_erzwingt_schrift(css_regel):
    """Der Inline-Stil auf .app-shell (color:V.tx) muss ueberstimmt werden.
    Das geht nur mit einem Selektor, der die Kinder von #root trifft, plus
    !important."""
    return bool(re.search(r"#root[^{]*\*[^{]*\{[^}]*color:[^;}]*!important", css_regel))


def _k_druckregel_loest_scrollklammer(css_regel):
    """height:100dvh + overflow:hidden muessen fuer den Druck aufgehoben sein."""
    hat_shell = ".app-shell" in css_regel
    hat_auto = "height:auto!important" in css_regel.replace(" ", "")
    hat_visible = "overflow:visible!important" in css_regel.replace(" ", "")
    return hat_shell and hat_auto and hat_visible


# ══════════════════════════════════════════════════════════════════════════
# Hilfen
# ══════════════════════════════════════════════════════════════════════════

_PRINT_REGEL = re.compile(r"@media print\{body>\*:not\(#root\)[^\n]*", re.S)

_PDF_KNOPF_ALT = (
    'btEntries.length>0&&React.createElement(\'button\', { onClick: ()=>window.print(), '
    'style: xBtn("pdf"), title: "Drucken / als PDF speichern"}'
)


def _print_regel(index_html):
    m = _PRINT_REGEL.search(index_html)
    assert m, "Die globale @media-print-Regel ist verschwunden - dann ist JEDER Druck ungeprueft."
    return m.group(0)


def _vbautag(index_html):
    fn = _extract_fn(index_html, "VBautag")
    assert fn, "function VBautag nicht gefunden - Anker veraltet, alle Aussagen unten sind wertlos."
    return fn


# ══════════════════════════════════════════════════════════════════════════
# ROT bis Patch - Beweiskraft
# ══════════════════════════════════════════════════════════════════════════

def test_1_bautagebuch_hat_ein_eigenes_pdf_statt_window_print(index_html):
    """P0. Das Bautagebuch ist das Beweisdokument im Bauverzugsstreit.
    Ein Bildschirmfoto der Liste ist keines."""
    assert _PDF_KNOPF_ALT not in index_html, (
        "Der PDF-Knopf des Bautagebuchs ist weiterhin ein nacktes window.print() "
        "auf die Listenansicht (index.html:19031). Kein Briefkopf, keine "
        "Unterschrift, kein Projekt, keine Seitenzahl."
    )
    assert "_genBautagPdf" in index_html, (
        "Es gibt keine Funktion _genBautagPdf. Vorbild steht mit _genChecklistPdf "
        "(index.html:16756) bereits im Repo."
    )


def test_2_bautagebuch_pdf_traegt_den_briefkopf(index_html):
    """P0. Ohne Firma auf dem Blatt ist nicht belegt, WER das behauptet."""
    fn = _extract_fn(index_html, "_genBautagPdf")
    assert fn, "_genBautagPdf fehlt (siehe Riegel 1)."
    assert _k_pdf_hat_briefkopf(fn), (
        "Das Bautagebuch-PDF nimmt die Firmendaten nicht aus COMPANY_FOOTER "
        "(index.html:5759). Genau das ist der Grund, warum die Konstante "
        "angelegt wurde - kein jsPDF-Erzeuger benutzt sie bis heute."
    )


def test_3_bautagebuch_pdf_hat_zwei_unterschriftsfelder(index_html):
    """P0. Ein Bautagesbericht ohne Gegenzeichnung der oertlichen Bauaufsicht
    ist eine einseitige Behauptung."""
    fn = _extract_fn(index_html, "_genBautagPdf")
    assert fn, "_genBautagPdf fehlt (siehe Riegel 1)."
    assert _k_pdf_hat_zwei_unterschriften(fn), (
        "Im Bautagebuch-PDF fehlen die zwei Unterschriftsfelder. Das Muster "
        "steht in _genChecklistPdf (index.html:16787/16788) und in printForm "
        "(index.html:15687/15688)."
    )


def test_4_bautagebuch_pdf_nummeriert_seiten(index_html):
    """P0-Nachbar. 'Seite x von y' ist der Beleg dafuer, dass nichts fehlt."""
    fn = _extract_fn(index_html, "_genBautagPdf")
    assert fn, "_genBautagPdf fehlt (siehe Riegel 1)."
    assert _k_pdf_zaehlt_seiten(fn), (
        "Keine Seitenzaehlung. Ein Konvolut ohne 'Seite x von y' laesst sich "
        "nicht auf Vollstaendigkeit pruefen. Muster: index.html:16790."
    )


def test_5_wetter_ist_nicht_mehr_auf_kirchberg_verdrahtet(index_html):
    """P0. Jede Baustelle bekommt heute das Wetter des Firmensitzes."""
    assert "const lat=48.46;const lon=15.74" not in index_html, (
        "Die Bautagebuch-Koordinaten sind weiterhin fest auf Kirchberg am "
        "Wagram verdrahtet (index.html:18862). Eine Baustelle in Wien 1100 "
        "bekommt damit das Wetter von 3470 - im Verzugsstreit ein Eigentor. "
        "Der Weg ueber die Projekt-PLZ und plz_geo liegt bereit."
    )


def test_6_wetter_holt_niederschlag_und_wind(index_html):
    """P0. Fuer den Verzugsnachweis zaehlen Regen und Wind, nicht eine
    Tagesmitteltemperatur."""
    vb = _vbautag(index_html)
    assert _k_wetter_url_vollstaendig(vb), (
        "Die Open-Meteo-Abfrage des Bautagebuchs holt nur temperature_2m und "
        "weather_code (index.html:18865/18866). Niederschlag "
        "(precipitation_sum / precipitation) und Wind (wind_speed_10m_max) "
        "fehlen - genau die Werte, mit denen ein Schlechtwettertag belegt wird."
    )


def test_7_wetter_wird_beim_datumswechsel_nachgezogen(index_html):
    """P0. Ein nachgetragener Bericht traegt sonst das Wetter von heute."""
    vb = _vbautag(index_html)
    # v3.9.882: [^,]+ fing nur bis zum ersten Komma - der Handler ist jetzt ein
    # Block ({...}) statt eines Ausdrucks, und autoFillWeather steht dahinter.
    # Ein Riegel, dessen Fangfenster kuerzer ist als das Gepruefte, misst nichts.
    m = re.search(r'type: "date", value: form\.datum, onChange: (.{0,300})', vb, re.S)
    assert m, (
        "Das Datumsfeld des Tagesberichts ist nicht mehr auffindbar - Anker "
        "veraltet (index.html:18985)."
    )
    assert "autoFillWeather" in m.group(1), (
        "Beim Wechsel des Datums wird das Wetter NICHT neu geholt "
        "(index.html:18985 setzt nur form.datum). autoFillWeather laeuft nur "
        "in startNewEntry mit dem heutigen Datum (index.html:18888). Ein am "
        "Montag nachgetragener Freitagsbericht behauptet damit das "
        "Montagswetter."
    )


def test_8_druckregel_erzwingt_lesbare_schrift(index_html):
    """P0 fuer ALLE 13 Druckknoepfe: im Dunkelmodus kommt heute ein leeres
    Blatt aus dem Drucker."""
    regel = _print_regel(index_html)
    assert _k_druckregel_erzwingt_schrift(regel), (
        "Die Druckregel (index.html:5899) uebersteuert die Inline-Schriftfarbe "
        "nicht. .app-shell traegt inline color:V.tx (index.html:8996), im "
        "Dunkelmodus #f0f0f2; Hintergruende druckt der Browser ohne "
        "print-color-adjust gar nicht. Ergebnis: weisse Schrift auf weissem "
        "Papier. Noetig ist ein Selektor auf die Kinder von #root mit "
        "!important."
    )


def test_9_druckregel_loest_die_scroll_klammer(index_html):
    """P0 fuer ALLE Druckknoepfe: es kommt hoechstens ein Bildschirm aufs
    Papier."""
    regel = _print_regel(index_html)
    assert _k_druckregel_loest_scrollklammer(regel), (
        "Die Druckregel hebt height:100dvh/overflow:hidden nicht auf. "
        "@media(max-width:1199px) setzt .app-shell{height:100dvh;"
        "overflow:hidden} und .main-pad{overflow-y:auto}; die A4-Druckflaeche "
        "ist schmaler als 1199px, also greift die Regel beim Drucken mit. "
        "Alles unterhalb des ersten Bildschirms wird abgeschnitten."
    )


def test_10_toter_print_stz_selektor_hat_ein_ziel_oder_ist_weg(index_html):
    """P1. Ein Druck-Stylesheet, das auf nichts zeigt, ist gruen und misst
    nichts - dieselbe Krankheit wie die vier Riegel aus v3.9.193."""
    # v3.9.882: auf den blossen Namen zu pruefen ist zu grob - der Kommentar, der
    # die Entfernung ERKLAERT, nennt ihn ebenfalls. Gesucht ist eine echte
    # CSS-Regel, also '#print-stz' gefolgt von '{' oder einem Nachkommen-Selektor.
    styled = bool(re.search(r"#print-stz[^*/{]{0,24}\{", index_html))
    if not styled:
        return  # Regel entfernt - in Ordnung
    hat_ziel = bool(re.search(r'id: *"print-stz"|id=\\?"print-stz', index_html))
    assert hat_ziel, (
        "Die Druckregel pflegt sechs Regeln fuer #print-stz (index.html:5899), "
        "aber kein einziges Element traegt diese id. Der ganze Zweig - "
        "position:fixed, color:#000!important, thead-Wiederholung, "
        "page-break-inside auf .sig-row - ist tot. Entweder das Ziel "
        "vergeben oder die Regeln loeschen."
    )


# ══════════════════════════════════════════════════════════════════════════
# GRUEN heute - die Belege, auf denen der Vorschlag steht
# ══════════════════════════════════════════════════════════════════════════

def test_11_beleg_signaturepad_existiert_und_wird_woanders_genutzt(index_html):
    """Die Unterschrift fehlt im Bautagebuch nicht aus Mangel an Technik."""
    assert "function SignaturePad({label,value,onChange" in index_html, (
        "SignaturePad ist weg - dann steht der Vorschlag anders da."
    )
    nutzungen = index_html.count("React.createElement(SignaturePad")
    assert nutzungen >= 4, (
        "SignaturePad wird an weniger als 4 Stellen benutzt (erwartet: "
        "Regiebericht 2x, Checkliste 2x, PZE 1x) - erwartet >=4, gefunden "
        + str(nutzungen)
    )
    vb = _vbautag(index_html)
    if "SignaturePad" in vb:
        return  # Patch ist da
    # Sonst: der Befund steht.


def test_12_beleg_projekte_tragen_plz_und_ort(index_html):
    """Ohne PLZ am Projekt waere der Wetter-Befund nicht reparierbar."""
    assert re.search(r"const emptyProj=\{[^\n]*plz:\"\"", index_html), (
        "Das Projekt-Formular fuehrt kein plz-Feld mehr - dann traegt der "
        "Wetter-Vorschlag nicht."
    )
    assert 'value: form.plz, onChange:' in index_html, (
        "Das PLZ-Eingabefeld im Projekt-Formular (index.html:15015) ist weg."
    )


def test_13_beleg_geo_weg_existiert_bereits(index_html):
    """plz_geo + Nominatim sind vorhanden - es muss nichts Neues gebaut
    werden, nur benutzt."""
    assert '_sbGet("plz_geo")' in index_html, (
        "Der plz_geo-Ladeweg (index.html:10212) ist weg."
    )
    assert "nominatim.openstreetmap.org" in index_html, (
        "Der Nominatim-Nachzieher (index.html:4921) ist weg - dann fehlt der "
        "Rueckfallweg fuer PLZ, die noch nicht in plz_geo stehen."
    )


def test_14_beleg_checklisten_pdf_ist_das_vorbild(index_html):
    """Das Muster fuer das Bautagebuch-PDF steht im Repo."""
    fn = _extract_fn(index_html, "_genChecklistPdf")
    assert fn, "_genChecklistPdf ist weg - das Vorbild fuer den Vorschlag fehlt."
    assert _k_pdf_hat_zwei_unterschriften(fn), "Vorbild hat keine zwei Unterschriften mehr."
    assert _k_pdf_zaehlt_seiten(fn), "Vorbild zaehlt keine Seiten mehr."
    assert 'new JsPDF({unit:"mm",format:"a4"})' in fn, "Vorbild ist nicht mehr A4/mm."


def test_15_beleg_keine_freigabe_und_keine_historie(index_html):
    """Haelt fest, dass ein halbjahresalter Eintrag heute frei
    ueberschreibbar ist. Kippt, sobald eine Freigabe eingebaut wird - dann
    ist dieser Riegel anzupassen und der Befund erledigt."""
    vb = _vbautag(index_html)
    hat_freigabe = bool(re.search(r"freigegeben|gesperrt|freigabe_am|locked", vb, re.I))
    hat_historie = bool(re.search(r"bautagebuch_historie|_btHistorie|revisions", vb, re.I))
    assert not (hat_freigabe and hat_historie), (
        "Freigabe UND Historie sind da - dieser Riegel hat seinen Zweck "
        "erfuellt und gehoert umgeschrieben."
    )
    # Der Befund selbst, damit er in der Ausgabe steht wenn man -rA faehrt:
    assert "SQ.push({url:\"/api/bautagebuch/\"+id,method:\"DELETE\"" in index_html, (
        "Der Loeschweg des Bautagebuchs hat sich geaendert - der Befund "
        "'Hard-Delete ohne Historie' (index.html:18942) ist neu zu pruefen."
    )


# ══════════════════════════════════════════════════════════════════════════
# UMKEHRPROBE
# Ein Riegel, der nicht rot werden kann, belegt nichts. Hier bekommt jeder
# Pruefkern einen synthetischen guten und einen synthetischen kaputten Text.
# ══════════════════════════════════════════════════════════════════════════

_GUT_PDF = (
    'async function _genBautagPdf(rows,proj,monteure,curUser){'
    'const doc=new JsPDF({unit:"mm",format:"a4"});'
    'doc.text(COMPANY_FOOTER.name,M,y);'
    '_sig("Unterschrift Bauleitung",e.sigMA,M);_sig("Unterschrift OEBA",e.sigKunde,M+95);'
    'const pc=doc.getNumberOfPages();doc.text("Seite "+i+" von "+pc,PW-M,290);}'
)
_SCHLECHT_PDF = (
    'async function _genBautagPdf(rows,proj){'
    'const doc=new JsPDF({unit:"mm",format:"a4"});doc.text("Bautagebuch",M,y);doc.save("x.pdf");}'
)

_GUT_URL = (
    '"https://api.open-meteo.com/v1/forecast?latitude="+lat+"&longitude="+lon'
    '+"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,'
    'wind_speed_10m_max,weather_code"'
)
_SCHLECHT_URL = (
    '"https://api.open-meteo.com/v1/forecast?latitude="+lat+"&longitude="+lon'
    '+"&daily=temperature_2m_max,temperature_2m_min,weather_code"'
)

_GUT_CSS = (
    "@media print{body>*:not(#root){display:none}button{display:none!important}"
    "#root,#root *{color:#000!important;background:transparent!important}"
    ".app-shell{height:auto!important;overflow:visible!important}"
    ".main-pad{overflow:visible!important;flex:none!important}}"
)
_SCHLECHT_CSS = (
    "@media print{body>*:not(#root){display:none}button{display:none!important}"
    "body{background:#fff!important;color:#1a1a1a}}"
)


def test_umkehrprobe_pdf_riegel_schlagen_an():
    assert _k_pdf_hat_briefkopf(_GUT_PDF)
    assert not _k_pdf_hat_briefkopf(_SCHLECHT_PDF), (
        "Umkehrprobe: der Briefkopf-Riegel wuerde ein PDF ohne Firmendaten "
        "durchwinken."
    )
    assert _k_pdf_hat_zwei_unterschriften(_GUT_PDF)
    assert not _k_pdf_hat_zwei_unterschriften(_SCHLECHT_PDF), (
        "Umkehrprobe: der Unterschriften-Riegel wuerde ein PDF ohne "
        "Unterschriftsfelder durchwinken."
    )
    assert _k_pdf_zaehlt_seiten(_GUT_PDF)
    assert not _k_pdf_zaehlt_seiten(_SCHLECHT_PDF), (
        "Umkehrprobe: der Seitenzahl-Riegel wuerde ein PDF ohne Zaehlung "
        "durchwinken."
    )


def test_umkehrprobe_wetter_riegel_schlaegt_an():
    assert _k_wetter_url_vollstaendig(_GUT_URL)
    assert not _k_wetter_url_vollstaendig(_SCHLECHT_URL), (
        "Umkehrprobe: der Wetter-Riegel wuerde eine Abfrage ohne Niederschlag "
        "und Wind durchwinken - genau den heutigen Stand."
    )


def test_umkehrprobe_druck_riegel_schlagen_an():
    assert _k_druckregel_erzwingt_schrift(_GUT_CSS)
    assert not _k_druckregel_erzwingt_schrift(_SCHLECHT_CSS), (
        "Umkehrprobe: der Schriftfarben-Riegel wuerde die heutige Regel "
        "durchwinken - dann bliebe das leere Blatt unbemerkt."
    )
    assert _k_druckregel_loest_scrollklammer(_GUT_CSS)
    assert not _k_druckregel_loest_scrollklammer(_SCHLECHT_CSS), (
        "Umkehrprobe: der Scroll-Klammer-Riegel wuerde die heutige Regel "
        "durchwinken - dann bliebe der Beschnitt nach einem Bildschirm "
        "unbemerkt."
    )


def test_umkehrprobe_anker_des_alten_knopfes_ist_echt(index_html):
    """Der Riegel 1 haengt an einem woertlichen Anker. Faellt der Anker
    auseinander, wuerde er GRUEN werden, ohne dass sich etwas gebessert hat.
    Hier wird belegt, dass der Anker heute wirklich trifft."""
    treffer = index_html.count(_PDF_KNOPF_ALT)
    if "_genBautagPdf" in index_html:
        return  # Patch ist da, der alte Knopf darf fehlen
    assert treffer == 1, (
        "Der Anker des alten window.print()-Knopfes trifft " + str(treffer) +
        "x statt 1x. Damit ist Riegel 1 nicht mehr aussagekraeftig - Anker "
        "nachziehen."
    )
