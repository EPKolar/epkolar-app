# -*- coding: utf-8 -*-
"""v3.9.885 - Zwei Wege, auf denen der Monteur Lohnzeit verlor, ohne es zu merken.

────────────────────────────────────────────────────────────────────────────
BEFUND 1 - Das Stundenfeld war eine Attrappe.
────────────────────────────────────────────────────────────────────────────
`addEntry` rechnet die Stunden IMMER neu:

    const _rVon=_zeitRundVon(addVon), _rBis=_zeitRundBis(addBis);
    let _h2=parseFloat(addHours)||0;
    if(_rVon&&_rBis){const _d=_wrapHrs(_rVon,_rBis)-addPause;if(_d>0)_h2=...;}

Und von/bis sind per Vorbelegung IMMER gesetzt (07:00/16:00, auch nach jedem
Zuruecksetzen). Wer also "10" in das Stundenfeld tippte und die Zeiten stehen
liess, buchte **8** - ohne Hinweis, ohne Warnung.

Ein sichtbares, beschreibbares Feld, dessen Eingabe stillschweigend verworfen
wird, ist schlimmer als gar kein Feld: der Monteur glaubt, er habe 10 Stunden
gebucht, und merkt es erst auf der Lohnabrechnung - wenn ueberhaupt.

Das Feld gab es an ZWEI Stellen (Projekt-Zeiterfassung und Haupt-Zeiterfassung),
beide mit demselben Fehler.

FIX: `_zeitEffektiveStunden(von,bis,pause)` liefert GENAU die Zahl, die addEntry
speichern wird - eine Quelle fuer Anzeige und Speicherung. Das Feld zeigt sie und
ist dann nicht beschreibbar. Sind von/bis leer, liefert der Helfer null und die
Handeingabe greift weiter: das ist die bewusste Hintertuer, deshalb ist readOnly
an die Bedingung geknuepft und nicht hart.

Gemessen (node, echte Helfer aus index.html):

    07:00-16:00 Pause 1h    ->  8
    07:00-16:00 Pause 0     ->  9
    06:00-18:00 Pause 0,5   ->  11,5
    von leer                ->  null   (Handeingabe zaehlt)
    bis leer                ->  null   (Handeingabe zaehlt)
    22:00-06:00 Pause 0     ->  8      (Nachtschicht, ueber Mitternacht)

────────────────────────────────────────────────────────────────────────────
BEFUND 2 - Ein geleertes Feld loeschte den Zeiteintrag.
────────────────────────────────────────────────────────────────────────────
Das Inline-Stundenfeld der Tageskarte rief

    onChange: e => updateEntryHours(iso, eIdx, parseFloat(e.target.value)||0)

`parseFloat("")` ist NaN, `NaN||0` ist **0** - und 0 loescht den Eintrag nach
800 ms.

WICHTIG, und deshalb NICHT geaendert: das Loeschen bei 0 ist ein ausdruecklicher
Chef-Entscheid (v3.9.437, Kommentar im Code: "0 heisst, war an dem Tag nicht
da"). Der bleibt.

Der Fehler ist, dass LEEREN nicht von NULL-EINGABE unterschieden wurde. Wer das
Feld zum Korrigieren leert und dann abgelenkt wird - Handschuh, Anruf, Sonne -
verlor nach 800 ms seinen Zeiteintrag, ohne Rueckfrage und ohne Hinweis. Der Weg
ueber das Kreuz hat ein Bestaetigungsfenster, dieser hatte keines.

Dazu die deutsche Tastatur: "8,5" liefert in einem type=number-Feld in vielen
Browsern ebenfalls einen leeren Wert - auch das darf nicht loeschen.

FIX: leeres Feld = "noch nichts eingegeben", loest gar nichts aus. Eine getippte
0 loescht weiterhin. Komma wird als Dezimaltrennzeichen akzeptiert.
"""
import json
import re

from conftest import run_node_snippet, _extract_fn


# ══ BEFUND 1 ════════════════════════════════════════════════════════════════

def test_es_gibt_genau_eine_quelle_fuer_die_stunden(index_html):
    assert "function _zeitEffektiveStunden(von,bis,pause){" in index_html, (
        "_zeitEffektiveStunden fehlt - dann rechnen Anzeige und Speicherung "
        "wieder unabhaengig voneinander, und das Feld kann wieder luegen."
    )


def test_der_helfer_rechnet_wie_addEntry(node_exe, index_html):
    """Der Kern: der Helfer MUSS dasselbe liefern wie der Speicherpfad -
    sonst zeigt das Feld eine andere Zahl, als gebucht wird."""
    namen = ("_zeitParse", "_zeitFmt", "_zeitRundVon", "_zeitRundBis",
             "_wrapHrs", "_zeitEffektiveStunden")
    teile = []
    for n in namen:
        f = _extract_fn(index_html, n)
        assert f, "Helfer nicht gefunden: " + n
        teile.append(f)
    snippet = "var ZEIT_RASTER_MIN=5;\n" + "\n".join(teile) + (
        "\nconst f=[['07:00','16:00',1],['07:00','16:00',0],['06:00','18:00',0.5],"
        "['','16:00',1],['07:00','',1],['22:00','06:00',0]];"
        "process.stdout.write(JSON.stringify(f.map(a=>_zeitEffektiveStunden(a[0],a[1],a[2]))));"
    )
    res = json.loads(run_node_snippet(node_exe, snippet))
    assert res[0] == 8, "07:00-16:00 mit 1h Pause muss 8 ergeben, war %s" % res[0]
    assert res[1] == 9, "ohne Pause 9, war %s" % res[1]
    assert res[2] == 11.5, "06:00-18:00 mit 0,5h Pause muss 11,5 ergeben, war %s" % res[2]
    assert res[3] is None and res[4] is None, (
        "Bei leerem von/bis MUSS der Helfer null liefern - sonst faellt die "
        "Hintertuer fuer die Handeingabe weg. War: %s / %s" % (res[3], res[4])
    )
    assert res[5] == 8, (
        "Nachtschicht 22:00-06:00 muss 8 ergeben (ueber Mitternacht), war %s" % res[5]
    )


def test_beide_stundenfelder_zeigen_den_gespeicherten_wert(index_html):
    """Der Fehler steckte an ZWEI Stellen - Projekt- und Haupt-Zeiterfassung."""
    n = index_html.count("value:(_zeitEffektiveStunden(addVon,addBis,addPause)!=null"
                         "?_zeitEffektiveStunden(addVon,addBis,addPause):addHours)")
    assert n == 2, (
        "Erwartet 2 Stundenfelder mit dem errechneten Wert (Projekt- und "
        "Haupt-Zeiterfassung), gefunden %d. Eine Stelle wuerde wieder luegen." % n
    )


def test_das_feld_ist_gesperrt_solange_es_errechnet_wird(index_html):
    n = index_html.count("readOnly:_zeitEffektiveStunden(addVon,addBis,addPause)!=null")
    assert n == 2, (
        "Erwartet 2 gesperrte Stundenfelder, gefunden %d. Ein beschreibbares "
        "Feld, dessen Eingabe verworfen wird, ist genau der alte Fehler." % n
    )


def test_die_hintertuer_bleibt_offen(index_html):
    """Bewusste Grenze: bei leerem von/bis MUSS die Handeingabe weiter zaehlen -
    sonst gibt es keinen Weg mehr, eine abweichende Zeit zu buchen."""
    assert "readOnly:_zeitEffektiveStunden(addVon,addBis,addPause)!=null" in index_html, (
        "readOnly ist nicht an die Bedingung geknuepft - waere es hart true, "
        "gaebe es keinen Weg mehr, eine abweichende Zeit einzutragen."
    )
    m = re.search(r"if\(!rv\|\|!rb\)return null;", index_html)
    assert m, (
        "Der Helfer liefert bei leerem von/bis kein null mehr - dann waere das "
        "Feld dauerhaft gesperrt und eine abweichende Zeit gar nicht buchbar."
    )


# ══ BEFUND 2 ════════════════════════════════════════════════════════════════

def test_leeres_feld_loest_nichts_aus(index_html):
    assert 'var _roh=String(e.target.value==null?"":e.target.value).trim();' in index_html, (
        "Der Rohwert wird nicht mehr geprueft - dann macht parseFloat('')||0 "
        "aus einem geleerten Feld wieder eine 0."
    )
    assert 'if(_roh==="")return;' in index_html, (
        "Ein leeres Feld ruft wieder updateEntryHours - und 0 loescht den "
        "Eintrag nach 800ms, ohne Rueckfrage."
    )


def test_unlesbare_eingabe_loest_nichts_aus(index_html):
    """Deutsche Tastatur: '8,5' liefert in type=number oft einen leeren Wert."""
    assert "if(isNaN(_z))return;" in index_html, (
        "Eine nicht lesbare Eingabe faellt wieder auf 0 zurueck und loescht."
    )
    assert '_roh.replace(",",".")' in index_html, (
        "Das Komma wird nicht als Dezimaltrennzeichen akzeptiert - dann ist "
        "'8,5' auf einer deutschen Tastatur nicht eingebbar."
    )


def test_der_chef_entscheid_bleibt_unangetastet(index_html):
    """v3.9.437: eine getippte 0 bedeutet 'war nicht da' und LOESCHT. Das war
    eine ausdrueckliche Entscheidung und wird hier NICHT rueckgaengig gemacht -
    nur vom versehentlichen Leeren getrennt."""
    assert "else if(entry.id&&!(newHours>0)){" in index_html, (
        "Der Loeschzweig fuer eine echte 0 ist weg - damit waere ein Chef-"
        "Entscheid stillschweigend zurueckgenommen."
    )
    assert 'method:"DELETE"' in index_html, "Der Loeschpfad selbst ist weg."


# ══ Umkehrprobe ═════════════════════════════════════════════════════════════

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    zurueck = index_html.replace('if(_roh==="")return;', "", 1)
    assert zurueck != index_html, "Rueckbau 1 griff nicht - Anker veraltet"
    assert 'if(_roh==="")return;' not in zurueck, (
        "Umkehrprobe: der Leer-Riegel wuerde nicht anschlagen"
    )

    zurueck2 = index_html.replace(
        "readOnly:_zeitEffektiveStunden(addVon,addBis,addPause)!=null,", "", 1)
    assert zurueck2 != index_html, "Rueckbau 2 griff nicht - Anker veraltet"
    assert zurueck2.count(
        "readOnly:_zeitEffektiveStunden(addVon,addBis,addPause)!=null") == 1, (
        "Umkehrprobe: der Sperr-Riegel zaehlt nicht - er wuerde einen "
        "einseitigen Rueckbau nicht bemerken."
    )
