# -*- coding: utf-8 -*-
"""v3.9.923 - DER GEWAEHLTE WERT MUSS UNTER DEN ANGEBOTENEN OPTIONEN SEIN.

WORAUS DAS ENTSTAND
-------------------
v3.9.919 hatte die Prioritaets-Auswahl der Arbeitsschein-Liste einen Wert, der
auf "keine" fiel, und einen Vorrat, aus dem "keine" herausgefiltert war. Ein
select ohne passende Option zeigt die ERSTE - AS_PRIO beginnt mit
"aufgeschoben". Der Schein sah aus wie ein aufgeschobener.

tests/test_prio_leer_v919.py riegelt diese eine Stelle. Dieser Riegel riegelt
die ANDEREN, die am 31.08. mit derselben Frage gemessen wurden. index.html hat
118 Auswahlfelder; die Regel dieses Repos lautet, dass eine Reparatur an einer
von vier Stellen keine ist.

WAS IM BROWSER GEMESSEN WURDE (scripts/select_wert_messen.py, vorher/nachher
gegen eine gepatchte KOPIE, gleiche Saat, gleiche Klickfolge):

    Stelle                             VORHER                     NACHHER
    Werkzeug-Formular Projekt          Wert p7 -> "Kein Projekt"  Wert p7, Index 6
    AS-Liste Sachbearbeiter            fremder Name -> "-"        Name steht drin
    AS-Liste Status                    ohne Status -> aufgenommen sauber
    AS-Formular Verrechnung            ohne Wert -> verrechenbar  sauber
    AS-Liste Monteur (geloescht)       -> "-"                     unveraendert

Die letzte Zeile ist Absicht: ein Monteur, der gar nicht mehr in der Liste
steht, kann von keinem Filter zurueckgeholt werden. _maWaehlbar haelt den
AUSGETRETENEN drin - das ist unten ausgefuehrt belegt - aber es kann keinen
Namen zu einer Kennung erfinden, die es nicht mehr gibt.

WIE HIER GEMESSEN WIRD
----------------------
Nicht durch Abschreiben der Schreibweise. Die Ausdruecke werden woertlich aus
index.html geschnitten und mit Node AUSGEFUEHRT, und zu jedem Riegel gehoert
eine Gegenprobe, die die alte Fassung zurueckbaut und verlangt, dass sie
bricht. Drei Bestandsriegel dieser Woche waren gruen und hielten einen Fehler
FEST, statt ihn zu finden; das ist der Grund fuer diese Form.
"""
import json
import subprocess

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
INDEX = WURZEL / "index.html"

BS = chr(92)


# ═══ Werkzeug zum Schneiden ══════════════════════════════════════════════
def _quelle():
    return INDEX.read_text(encoding="utf-8")


def _block(quelle, anfang, ende):
    """Von anfang (einschliesslich) bis vor ende - beide woertlich."""
    i = quelle.index(anfang)
    j = quelle.index(ende, i)
    return quelle[i:j].replace(chr(13), "")


def _funktion(quelle, kopf):
    """function name(...){...} ueber die Klammerbilanz schneiden."""
    i = quelle.index(kopf)
    d = 0
    j = quelle.index("{", i)
    k = j
    while k < len(quelle):
        c = quelle[k]
        if c == "{":
            d += 1
        elif c == "}":
            d -= 1
            if d == 0:
                return quelle[i:k + 1].replace(chr(13), "")
        k += 1
    raise AssertionError("Klammern von %r nicht ausgeglichen" % kopf)


def _node(programm, tmp_path, name, arg=None):
    p = tmp_path / name
    p.write_text(programm, encoding="utf-8")
    cmd = ["node", str(p)]
    if arg is not None:
        cmd.append(json.dumps(arg))
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _einmal(quelle, text, wofuer):
    n = quelle.count(text)
    assert n == 1, (
        "%s ist nicht mehr eindeutig zu finden (%d Treffer). Dieser Riegel "
        "misst dann nichts - genau der Zustand, in dem ein gruener Lauf "
        "wertlos ist." % (wofuer, n))


# ═══ 1) DER MASSSTAB: _maWaehlbar haelt den Ausgetretenen drin ═══════════
# Diese Pruefung ist heute GRUEN und steht bewusst zuerst. Sie zeigt, dass es
# im Repo bereits eine richtige Antwort auf die Frage gibt - alle Reparaturen
# unten sind nach ihrem Vorbild gebaut. Und sie ist die Gegenprobe fuer die
# ganze Familie: waere sie rot, waere jede Aussage unten wertlos.
def test_maWaehlbar_haelt_den_getragenen_ausgetretenen_drin(tmp_path):
    q = _quelle()
    prog = (
        "function _ezHeuteISO(){return " + chr(34) + "2026-08-31" + chr(34) + ";}" + chr(10)
        + _funktion(q, "function _maIstEhemalig(") + chr(10)
        + _funktion(q, "function _maWaehlbar(") + chr(10)
        + "const liste=[{id:'M1',n:'Aktiv',austritt:''},"
          "{id:'M9',n:'Ehemalig',austritt:'2026-06-01'}];" + chr(10)
        + "const ids=(a)=>_maWaehlbar(liste,a).map(m=>m.id);" + chr(10)
        + "console.log(JSON.stringify({"
          "getragen: ids('M9'), fremd: ids('M1'), ohne: ids(''),"
          "geloescht: ids('M_GIBT_ES_NICHT')}));" + chr(10))
    aus = _node(prog, tmp_path, "mawaehlbar.js")

    assert aus["getragen"] == ["M1", "M9"], (
        "Ein Schein, der einen AUSGETRETENEN traegt, muss ihn weiter angeboten "
        "bekommen - sonst zeigt das Feld eine fremde Person. Bekommen: %r"
        % aus["getragen"])
    assert aus["fremd"] == ["M1"] and aus["ohne"] == ["M1"], (
        "Ohne getragenen Wert darf der Ausgetretene NICHT waehlbar sein "
        "(v3.9.874). Bekommen: %r / %r" % (aus["fremd"], aus["ohne"]))
    # Die Grenze, ausdruecklich festgehalten: eine Kennung, die gar nicht mehr
    # in der Liste steht, kann nicht zurueckgeholt werden. Wer das spaeter
    # reparieren will, braucht einen Namen aus einer anderen Quelle, keinen
    # anderen Filter.
    assert aus["geloescht"] == ["M1"], aus["geloescht"]


# ═══ 2) WERKZEUG-FORMULAR: das getragene Projekt bleibt waehlbar ═════════
WZ_WERT = 'form.projekt||""'
WZ_NEU = ('projects.filter(p=>p.status==="aktiv"'
          '||String(p.id)===String(form.projekt||""))')
WZ_ALT = 'projects.filter(p=>p.status==="aktiv")'

WZ_PROJEKTE = [
    {"id": "p1", "status": "aktiv"},
    {"id": "p7", "status": "abgeschlossen"},
    {"id": "p8", "status": "archiv"},
]
WZ_FAELLE = [
    ("aktives Projekt", {"projekt": "p1"}),
    ("abgeschlossenes Projekt", {"projekt": "p7"}),
    ("archiviertes Projekt", {"projekt": "p8"}),
    ("kein Projekt", {}),
    ("leerer Text", {"projekt": ""}),
]


def _wz_programm(filter_ausdruck):
    return (
        "const projects=" + json.dumps(WZ_PROJEKTE) + ";" + chr(10)
        + "const faelle=JSON.parse(process.argv[2]);" + chr(10)
        + "console.log(JSON.stringify(faelle.map(function(f){" + chr(10)
        + "  const form=f.form;" + chr(10)
        + "  const wert=" + WZ_WERT + ";" + chr(10)
        # Die leere Option steht im Quelltext als erstes Kind des select und
        # gehoert deshalb in den Vorrat.
        + "  const optionen=[''].concat(" + filter_ausdruck
        + ".map(function(p){return p.id;}));" + chr(10)
        + "  return {name:f.name, wert:wert, optionen:optionen," + chr(10)
        + "          dabei:optionen.indexOf(wert)>=0," + chr(10)
        + "          gezeigt:optionen.indexOf(wert)>=0?wert:(optionen.length?optionen[0]:null)};"
        + chr(10) + "})));" + chr(10))


def _wz_arg():
    return [{"name": n, "form": f} for n, f in WZ_FAELLE]


def test_werkzeug_formular_bietet_das_getragene_projekt_an(tmp_path):
    q = _quelle()
    _einmal(q, WZ_NEU, "die Projekt-Auswahl im Werkzeug-Formular")
    _einmal(q, WZ_WERT + ", onChange: e=>setForm(p=>({...p,projekt:e.target.value}))",
            "die Wertzeile der Projekt-Auswahl")

    aus = _node(_wz_programm(WZ_NEU), tmp_path, "wz_neu.js", _wz_arg())
    for r in aus:
        assert r["dabei"], (
            "Fall '%s': der Wert %r steht NICHT unter den Optionen %r. Das "
            "Feld zeigt dann %r - bei diesem select also '— Kein Projekt —' "
            "fuer ein Geraet, das sehr wohl auf einem Projekt liegt."
            % (r["name"], r["wert"], r["optionen"], r["gezeigt"]))


def test_gegenprobe_werkzeug_alter_filter_verliert_das_projekt(tmp_path):
    """Ohne diese Umkehr waere nicht belegt, dass der Aufbau den Fehler SIEHT."""
    aus = _node(_wz_programm(WZ_ALT), tmp_path, "wz_alt.js", _wz_arg())
    verloren = [r["name"] for r in aus if not r["dabei"]]
    assert verloren == ["abgeschlossenes Projekt", "archiviertes Projekt"], (
        "Der alte Filter MUSS genau die beiden nicht mehr aktiven Projekte "
        "verlieren - sonst misst dieser Riegel nichts. Verloren: %r" % verloren)
    for r in aus:
        if not r["dabei"]:
            assert r["gezeigt"] == "", (
                "Fall '%s' haette %r gezeigt, erwartet war die leere Option "
                "('— Kein Projekt —')" % (r["name"], r["gezeigt"]))


# ═══ 3) AS-FORMULAR: ohne Verrechnung wird keine behauptet ═══════════════
VERR_NEU = ('value: form.verrechnung||"", onChange: '
            'e=>setForm(p=>({...p,verrechnung:e.target.value})), '
            'disabled:_asMtLocked, style: II()}, '
            '!form.verrechnung&&React.createElement(\'option\', '
            '{ key: "_leer", value: ""}, "—")')
VERR_FAELLE = [
    ("Feld fehlt", {}),
    ("null", {"verrechnung": None}),
    ("leerer Text", {"verrechnung": ""}),
    ("verrechenbar", {"verrechnung": "verrechenbar"}),
    ("garantie", {"verrechnung": "garantie"}),
]


def _verr_programm(quelle, mit_leerer_option):
    return (
        "const COLORS={ERROR:'#ef4444'};" + chr(10)
        + _block(quelle, "const AS_VERRECH=", "const SACHBEARBEITER=") + chr(10)
        + "const faelle=JSON.parse(process.argv[2]);" + chr(10)
        + "console.log(JSON.stringify(faelle.map(function(f){" + chr(10)
        + "  const form=f.form;" + chr(10)
        + ("  const wert=form.verrechnung||'';" if mit_leerer_option
           else "  const wert=''+form.verrechnung;") + chr(10)
        + ("  const optionen=(!form.verrechnung?['']:[])"
           ".concat(Object.keys(AS_VERRECH));" if mit_leerer_option
           else "  const optionen=Object.keys(AS_VERRECH);") + chr(10)
        + "  return {name:f.name, wert:wert, optionen:optionen," + chr(10)
        + "          dabei:optionen.indexOf(wert)>=0," + chr(10)
        + "          gezeigt:optionen.indexOf(wert)>=0?wert:(optionen.length?optionen[0]:null)};"
        + chr(10) + "})));" + chr(10))


def _verr_arg():
    return [{"name": n, "form": f} for n, f in VERR_FAELLE]


def test_as_formular_behauptet_keine_verrechnung(tmp_path):
    q = _quelle()
    _einmal(q, VERR_NEU, "die Verrechnungs-Auswahl im AS-Formular")

    aus = _node(_verr_programm(q, True), tmp_path, "verr_neu.js", _verr_arg())
    for r in aus:
        assert r["dabei"], (
            "Fall '%s': Wert %r nicht unter %r" % (r["name"], r["wert"], r["optionen"]))
    leer = {r["name"]: r["gezeigt"] for r in aus
            if r["name"] in ("Feld fehlt", "null", "leerer Text")}
    assert leer == {"Feld fehlt": "", "null": "", "leerer Text": ""}, leer
    gesetzt = {r["name"]: r["gezeigt"] for r in aus
               if r["name"] in ("verrechenbar", "garantie")}
    assert gesetzt == {"verrechenbar": "verrechenbar", "garantie": "garantie"}, gesetzt
    # Die leere Option darf NUR auftauchen, solange nichts gesetzt ist - sonst
    # waere "keine Verrechnung" eine waehlbare Stufe geworden.
    fuer_gesetzt = next(r for r in aus if r["name"] == "garantie")
    assert "" not in fuer_gesetzt["optionen"], fuer_gesetzt["optionen"]


def test_gegenprobe_verrechnung_alt_zeigt_verrechenbar(tmp_path):
    aus = _node(_verr_programm(_quelle(), False), tmp_path, "verr_alt.js",
                _verr_arg())
    kaputt = [r for r in aus if not r["dabei"]]
    assert len(kaputt) == 3, [r["name"] for r in kaputt]
    for r in kaputt:
        assert r["gezeigt"] == "verrechenbar", (
            "Fall '%s' haette %r gezeigt - erwartet war 'verrechenbar', also "
            "eine Aussage ueber Geld, die niemand getroffen hat."
            % (r["name"], r["gezeigt"]))


# ═══ 4) STATUS: ein Schein ohne Status war eingefroren ═══════════════════
# Hier geht es nicht nur um die Anzeige. Die Zeile rechnet laengst mit
# st=AS_STATUS[a.scheinstatus]||AS_STATUS.aufgenommen, der Wert des Feldes aber
# nicht - und derselbe rohe Wert ging als _oldS in den Uebergangs-Waechter.
ST_LISTE = ('value: a.scheinstatus||"aufgenommen"')
ST_FORM = ('value: form.scheinstatus||"aufgenommen"')
ST_LEER = [None, ""]


def _st_programm(quelle, normalisiert):
    return (
        _block(quelle, "const _AS_ALL_STATES", "const AS_GRP_OFFEN=") + chr(10)
        + "const faelle=JSON.parse(process.argv[2]);" + chr(10)
        + "console.log(JSON.stringify(faelle.map(function(f){" + chr(10)
        + "  const a=f.schein;" + chr(10)
        + ("  const alt=a.scheinstatus||'aufgenommen';" if normalisiert
           else "  const alt=a.scheinstatus;") + chr(10)
        + "  return {name:f.name, alt:String(alt)," + chr(10)
        + "          erlaubt:_isLegalAsTransition(alt,'freigegeben')};"
        + chr(10) + "})));" + chr(10))


ST_FAELLE = [("Feld fehlt", {}), ("null", {"scheinstatus": None}),
             ("leerer Text", {"scheinstatus": ""}),
             ("aufgenommen", {"scheinstatus": "aufgenommen"})]


def _st_arg():
    return [{"name": n, "schein": s} for n, s in ST_FAELLE]


def test_schein_ohne_status_ist_nicht_eingefroren(tmp_path):
    q = _quelle()
    _einmal(q, ST_LISTE, "die Status-Auswahl der AS-Liste")
    _einmal(q, ST_FORM, "die Status-Auswahl des AS-Formulars")
    _einmal(q, 'if(!_isLegalAsTransition(as.scheinstatus||"aufgenommen",newStatus)){',
            "der Wisch-Statuswechsel")

    aus = _node(_st_programm(q, True), tmp_path, "st_neu.js", _st_arg())
    for r in aus:
        assert r["erlaubt"], (
            "Fall '%s': der Wechsel nach 'freigegeben' wird abgelehnt. Das "
            "Feld zeigte 'aufgenommen', der Waechter bekam aber %r - der "
            "Schein war damit unbeweglich und meldete beim Klick "
            "'Ungueltiger Status-Wechsel von undefined'." % (r["name"], r["alt"]))


def test_gegenprobe_roher_status_lehnt_jeden_wechsel_ab(tmp_path):
    aus = _node(_st_programm(_quelle(), False), tmp_path, "st_alt.js", _st_arg())
    abgelehnt = [r["name"] for r in aus if not r["erlaubt"]]
    assert abgelehnt == ["Feld fehlt", "null", "leerer Text"], (
        "Ohne Normalisierung MUESSEN genau die drei leeren Formen abgelehnt "
        "werden - sonst misst dieser Riegel nichts. Abgelehnt: %r" % abgelehnt)


# ═══ 5) SACHBEARBEITER: der getragene Name bleibt waehlbar ═══════════════
SB_FAELLE = ["SCHOBER", "Gibt Es Nicht", "", None]


def test_sachbearbeiter_bleibt_waehlbar(tmp_path):
    q = _quelle()
    _einmal(q, "function _sbWaehlbar(", "der Sachbearbeiter-Helfer")
    _einmal(q, "_sbWaehlbar(a.sachbearbeiter)", "die AS-Liste")
    _einmal(q, "_sbWaehlbar(defaultSB)", "der Standard-Sachbearbeiter")

    prog = (
        _block(q, "const SACHBEARBEITER=", "function _getDefaultSB") + chr(10)
        + "const faelle=JSON.parse(process.argv[2]);" + chr(10)
        + "console.log(JSON.stringify(faelle.map(function(a){" + chr(10)
        + "  const wert=a||'';" + chr(10)
        + "  const optionen=[''].concat(_sbWaehlbar(a));" + chr(10)
        + "  return {wert:wert, optionen:optionen," + chr(10)
        + "          dabei:optionen.indexOf(wert)>=0," + chr(10)
        + "          gezeigt:optionen.indexOf(wert)>=0?wert:(optionen.length?optionen[0]:null)};"
        + chr(10) + "})));" + chr(10))
    aus = _node(prog, tmp_path, "sb_neu.js", SB_FAELLE)
    for r in aus:
        assert r["dabei"], (
            "Wert %r steht nicht unter %r - das Feld zeigt dann %r, also "
            "'kein Sachbearbeiter' fuer einen Schein, der einen hat."
            % (r["wert"], r["optionen"], r["gezeigt"]))
    # Der fremde Name darf NUR dann dazukommen, wenn er getragen wird.
    ohne = next(r for r in aus if r["wert"] == "")
    assert "Gibt Es Nicht" not in ohne["optionen"], ohne["optionen"]


def test_gegenprobe_rohe_sachbearbeiterliste_verliert_den_namen(tmp_path):
    q = _quelle()
    prog = (
        _block(q, "const SACHBEARBEITER=", "function _sbWaehlbar") + chr(10)
        + "const faelle=JSON.parse(process.argv[2]);" + chr(10)
        + "console.log(JSON.stringify(faelle.map(function(a){" + chr(10)
        + "  const wert=a||'';" + chr(10)
        + "  const optionen=[''].concat(SACHBEARBEITER);" + chr(10)
        + "  return {wert:wert, dabei:optionen.indexOf(wert)>=0,"
          "gezeigt:optionen.indexOf(wert)>=0?wert:optionen[0]};"
        + chr(10) + "})));" + chr(10))
    aus = _node(prog, tmp_path, "sb_alt.js", SB_FAELLE)
    verloren = [r["wert"] for r in aus if not r["dabei"]]
    assert verloren == ["Gibt Es Nicht"], verloren
    assert aus[1]["gezeigt"] == "", aus[1]


# ═══ 6) DIE EIGENSCHAFT ueber ALLE Auswahlfelder, nicht eine Zahl ════════
def _selects(quelle):
    """Jedes React.createElement('select', ...) mit Eigenschaften und Kindern.

    Ueber die Klammerbilanz geschnitten, damit verschachtelte Aufrufe nicht
    zerreissen. Liefert (eigenschaften, kinder) je Fundort.
    """
    marke = "React.createElement('select'"
    raus = []
    stelle = quelle.find(marke)
    while stelle >= 0:
        i = quelle.index("(", stelle)
        d = 0
        instr = None
        esc = False
        k = i
        ende = -1
        while k < len(quelle):
            c = quelle[k]
            if instr:
                if esc:
                    esc = False
                elif c == BS:
                    esc = True
                elif c == instr:
                    instr = None
            else:
                if c in ('"', chr(39), chr(96)):
                    instr = c
                elif c in "([{":
                    d += 1
                elif c in ")]}":
                    d -= 1
                    if d == 0:
                        ende = k
                        break
            k += 1
        koerper = quelle[stelle:ende + 1]
        raus.append(koerper)
        stelle = quelle.find(marke, stelle + 1)
    return raus


def test_jede_projekt_auswahl_faellt_auf_eine_leere_option_zurueck():
    """Der Vorrat ist gefiltert - dann MUSS das erste Angebot neutral sein.

    Nicht gezaehlt, sondern gemessen: aus index.html werden alle Auswahlfelder
    geschnitten, davon die, deren Optionen aus einer auf aktive Projekte
    gefilterten Liste kommen. Faellt der Wert bei einem von ihnen heraus, zeigt
    das Feld sein erstes Angebot - und das darf dann kein FREMDES Projekt sein.

    Genau das war der Schaden von v3.9.919 in anderer Gestalt: dort war das
    erste Angebot "aufgeschoben" und wurde zur Aussage.
    """
    q = _quelle()
    treffer = [s for s in _selects(q)
               if 'p.status==="aktiv"' in s or "p.status==='aktiv'" in s]
    assert len(treffer) >= 6, (
        "Erwartet werden mindestens sechs Projekt-Auswahlen, gefunden: %d - "
        "der Schnitt greift nicht mehr und dieser Riegel misst nichts."
        % len(treffer))
    ohne_leere = [s[:120] for s in treffer
                  if 'value: ""' not in s and "value:''" not in s
                  and 'value:""' not in s and "value: ''" not in s]
    assert not ohne_leere, (
        "Diese Projekt-Auswahl filtert ihren Vorrat, bietet aber KEINE leere "
        "Option an. Faellt der getragene Wert heraus, zeigt sie ein fremdes "
        "Projekt als das gewaehlte: %r" % ohne_leere)

    # Und genau eine von ihnen - die, deren Wert aus einem gespeicherten
    # Datensatz kommt - haelt das Getragene zusaetzlich im Vorrat.
    mit_rueckhalt = [s for s in treffer if WZ_NEU in s]
    assert len(mit_rueckhalt) == 1, (
        "Das Werkzeug-Formular ist die einzige Projekt-Auswahl, deren Wert aus "
        "einem gespeicherten Datensatz kommt (openEdit setzt setForm({...w})). "
        "Sein Rueckhalt fehlt oder es sind mehrere geworden: %d"
        % len(mit_rueckhalt))
