# -*- coding: utf-8 -*-
"""v3.9.900 - VIER STELLEN "BERECHNET UND NIE GELESEN", VIER VERSCHIEDENE ANTWORTEN.

Der Fund war jedesmal derselbe (eine Zuweisung, null Leser), die richtige
Behandlung jedesmal eine andere. Genau das zu unterscheiden war die Arbeit:

  1  _normFrei   (:10256)  AUSBAUEN  - die Hand-Wand rechnet woanders, s.u.
  2  asNextWeek  (:24131)  ANZEIGEN  - hier fehlte eine Kachel, kein Aufraeumen
  3  det         (:13918)  ANZEIGEN  - der Feed verschwieg, WAS geaendert wurde
  4  _evCache    (:7071)   AUSBAUEN  - samt einem Kommentar, der log

Zu 1 (die Pins dazu stehen in test_dispo_kapazitaet_v790.py):
_dispoNormFrei hiess im eigenen Kopf "FREIE Rest-Kapazitaet der HAND-WAND" und
wurde von der Hand-Wand nie gerufen. Die Drop-Pruefung liest data-norm und
data-used aus dem DOM und bildet frei=(norm-used)+eigen - an ZWEI Stellen
(pointermove fuer das Live-Feedback, pointerup fuer das Schreiben) -, und
_dispoAblehnGrund bildet dieselbe Groesse ein drittes Mal fuer den Toast. Die
ausgebaute Zeile war die vierte Rechnung derselben Groesse: die einzige ohne
Leser und die einzige, die auf 0 klemmte.

Zu 4: die tote Ref war harmlos, ihr Kommentar nicht. Er versprach eine
Absicherung fuer den Netzausfall, die es nie gab, waehrend die Richtung seit
v3.9.769 server-seitig entschieden wird und v3.9.699 den Offline-Fall bewusst
als ABBRUCH festgelegt hat. Wer das Versprechen einloest, dreht diese
Entscheidung zurueck und bekommt wieder Tage mit 0 Stunden und gruenem Haken.
"""
from _hilfen import nur_code, fundstellen


def _pure(index_html, name):
    i = index_html.index("function " + name + "(")
    j = index_html.index("\n}", i) + 2
    return index_html[i:j]


# == 1 - _normFrei: der ungelesene Zwilling ==================================

def test_der_ungelesene_zwilling_der_handwand_ist_weg(index_html):
    code = nur_code(index_html)
    for name in ("_normFrei", "_dispoNormFrei"):
        assert name not in code, (
            "%s ist wieder da. Eine Zuweisung ohne Leser plus die Funktion, die "
            "nur sie ruft - die Hand-Wand rechnet im Drag-Handler. %s"
            % (name, fundstellen(code, name))
        )


def test_die_handwand_rechnet_weiter_an_ihrer_echten_stelle(index_html):
    """UMKEHRPROBE zum Ausbau: das, was WIRKLICH rechnet, muss stehenbleiben.
    Ein Ausbau, der den lebenden Pfad mitnimmt, wird hier rot."""
    assert index_html.count("frei=(norm-used)+eigen;") == 2, (
        "Die Drop-Pruefung rechnet nicht mehr an beiden Stellen (pointermove = "
        "Live-Feedback, pointerup = Schreiben) - genau dort entsteht der Fall "
        "gruen angezeigt, aber abgelehnt."
    )
    assert "'data-norm':(t.normMin-_abwAbz)" in index_html
    assert "'data-used':usedMin" in index_html
    assert "var frei=(normMin||0)-(usedMin||0)+(eigen||0);" in index_html, (
        "_dispoAblehnGrund bildet die Groesse nicht mehr gleich - dann sagt der "
        "Ablehn-Toast etwas anderes als die Wand tut."
    )


# == 2 - asNextWeek: die fehlende Kachel =====================================

def test_asnextweek_wird_endlich_gezeigt(index_html):
    # v3.9.913 - DIE ZAHL IST WEG. Vorher stand hier zusaetzlich
    # `code.count("asNextWeek") >= 2`. Sie war kommentarblind (nur_code), aber
    # ueberfluessig: die Aussage lautet "asNextWeek hat einen LESER", und der
    # Leser steht eine Zeile weiter unten beim Namen. Zwei Vorkommen haetten
    # auch zwei Berechnungen ohne jeden Leser sein koennen - die Zahl war der
    # schwaechere von zwei Riegeln am selben Gegenstand.
    #
    # Nebenbefund fuer die Buchhaltung: kommentarblind sind es heute 3 (die
    # Definition + zweimal in der _metric-Zeile), dateiweit 5. Genau solche
    # Zahlen muss man beim Umbenennen einer Farbbedingung nachziehen - deshalb
    # steht sie hier nicht mehr als Zusicherung.
    code = nur_code(index_html)
    assert "const asNextWeek=" in code, (
        "asNextWeek wird gar nicht mehr berechnet. %s" % fundstellen(code, "asNextWeek")
    )
    assert ("_metric('Geplant nächste Woche',asNextWeek,"
            "asNextWeek>0?'#3b82f6':V.dm)") in index_html, (
        "asNextWeek wird wieder nur berechnet und nie angezeigt - die Kachel im "
        "Chef-Portal fehlt. %s" % fundstellen(code, "asNextWeek")
    )


def test_die_kachel_steht_in_der_arbeitsscheine_karte(index_html):
    """Gegenprobe zur blossen Existenz: die Kachel muss in DER Karte stehen, die
    im Tab 'arbeit' gerendert wird - sonst rechnet sie weiter fuer niemanden."""
    i = index_html.find("'Arbeitsscheine','#f97316',[")
    j = index_html.find("_drill('Arbeitsscheine','arbeitsscheine')", i)
    assert i != -1 and j > i, "Die Arbeitsscheine-Karte des Chef-Portals fehlt."
    assert "asNextWeek" in index_html[i:j], (
        "Die Kachel steht ausserhalb der Arbeitsscheine-Karte - dann zeigt sie "
        "im Chef-Portal nichts an."
    )


# == 3 - det: der Feed verschwieg das WAS ====================================

def _feedblock(index_html):
    i = index_html.find(", activity.slice(0,200).map((a,i)=>{")
    j = index_html.find("})\n          ))", i)
    assert i != -1 and j > i, "Der Aktivitaets-Feed wurde nicht gefunden."
    return index_html[i:j]


def test_der_feed_zeigt_die_details(index_html):
    blk = _feedblock(index_html)
    assert "_actDetailText(det," in blk, (
        "Der Aktivitaets-Feed baut det weiter bei jedem Render auf und zeigt es "
        "nicht - der Zustand vor v899. Die Details standen nur im CSV-Export."
    )
    # (a) lange Inhalte duerfen die Zeile nicht sprengen
    assert 'textOverflow:"ellipsis"' in blk and 'whiteSpace:"nowrap"' in blk, (
        "Die Detailzeile ist nicht mehr auf eine Zeile begrenzt - freie Texte "
        "sprengen dann den Feed."
    )
    # (b) roher Text, kein HTML-Einschleusen
    assert "dangerouslySetInnerHTML" not in blk, (
        "Im Feed wird HTML gesetzt statt Text - Details sind frei geformte, von "
        "aussen befuellbare Daten."
    )
    # (c) leere Details ergeben keine leere Zeile
    assert "if(!_dtx)return null;" in blk, (
        "Leere Details wuerden als leere Zeile gerendert."
    )


def test_actdetailtext_haelt_die_zeile_und_bleibt_text(index_html, node_exe, tmp_path):
    js = _pure(index_html, "_actDetailText") + u"""
function ok(c,n){ if(!c){ console.error('FAIL '+n+' -> '+JSON.stringify(_last)); process.exit(1);} }
var _last=null;
// (c) leer bleibt leer - der Aufrufer rendert dann gar keine Zeile
ok(_actDetailText(null,140)==='','null ergibt leer');
ok(_actDetailText({},140)==='','leeres Objekt ergibt leer');
ok(_actDetailText({a:null,b:''},140)==='','nur leere Werte ergeben leer');
// Normalfall: aus dem Objekt wird eine lesbare Zeile
_last=_actDetailText({feld:'status',alt:'offen',neu:'erledigt'},140);
ok(_last==='feld: status · alt: offen · neu: erledigt','Objekt wird eine Zeile');
_last=_actDetailText({n:5,b:true,o:{x:1}},140);
ok(_last==='n: 5 · b: true · o: {"x":1}','Zahl/Bool/verschachtelt');
_last=_actDetailText(['a','','b'],140);
ok(_last==='a · b','Array ohne Leerwerte');
// (a) lange Inhalte sprengen die Zeile nicht - und die Kuerzung ist sichtbar
_last=_actDetailText({t:new Array(400).join('x')},60);
ok(_last.length===60,'auf maxLen gekuerzt');
ok(_last.charAt(59)==='…','Kuerzung wird sichtbar gemacht');
// eine Zeile bleibt eine Zeile
_last=_actDetailText('a\\r\\nb\\tc',140);
ok(_last==='a b c','Umbrueche und Tabs werden zu Leerzeichen');
// (b) HTML wird NICHT gebaut, sondern bleibt roher Text (React maskiert das Kind)
_last=_actDetailText('<img src=x onerror=alert(1)>',140);
ok(_last.indexOf('<img')===0,'HTML bleibt roher Text');
console.log('ALL-OK');
"""
    f = tmp_path / "act899.js"
    f.write_text(js, encoding="utf-8")
    import subprocess
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "ALL-OK" in r.stdout


# == 4 - _evCache: das Versprechen ohne Deckung ==============================

def test_evcache_und_sein_versprechen_sind_weg(index_html):
    code = nur_code(index_html)
    assert "_evCache" not in code, (
        "_evCache ist wieder da. Solange nichts hineinschreibt und nichts "
        "daraus liest, ist der Kommentar daneben eine Zusage ohne Deckung. %s"
        % fundstellen(code, "_evCache")
    )


def test_die_richtung_kommt_weiter_vom_server(index_html):
    """UMKEHRPROBE: der Ausbau darf den ERSATZ nicht mitnehmen. Der Offline-Fall
    ist absichtlich ein Abbruch, kein geratener Wert."""
    assert "'/rpc/stempel_terminal_stempel'" in index_html, (
        "Die Richtung wird nicht mehr server-seitig entschieden - dann braucht "
        "der Client wieder eine eigene Quelle, und die gibt es nicht."
    )
    assert "function _stErrKind(e){" in index_html, (
        "Ohne _stErrKind kann der Scan Netz- und Rechtefehler nicht "
        "unterscheiden und bricht nicht mehr sauber ab."
    )
