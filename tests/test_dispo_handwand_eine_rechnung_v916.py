# -*- coding: utf-8 -*-
"""v3.9.916 - Die Hand-Wand rechnet ihre freie Kapazitaet an DREI Stellen.
Gehen sie auseinander? GEMESSEN: NEIN. Der Verdacht ist widerlegt.

DIE DREI STELLEN (comment-frei gemessen, mehr gibt es nicht; Zeilen zum Stand
v3.9.913 - Zeilennummern altern, die Zusicherungen unten nicht):
  :10242  var eigen=(ci===st.srcIso)?st.dauerMin:0, frei=(norm-used)+eigen;   (pointermove, Live-Feedback)
  :10256  var eigen=(ti===st.srcIso)?st.dauerMin:0, frei=(norm-used)+eigen;   (pointerup, das Schreiben)
  :5576   var frei=(normMin||0)-(usedMin||0)+(eigen||0);                      (_dispoAblehnGrund, der Toast)

Die EINE Quelle der Eingangswerte ist :10411
  'data-norm':(t.normMin-_abwAbz),'data-used':usedMin
Beide Handler-Zweige lesen sie per getAttribute+parseInt zurueck.

Die ersten beiden reichen ihr Ergebnis an _dispoDropOk, die dritte bildet die
Groesse neu, weil sie norm/used/eigen EINZELN bekommt. Drei Rechnungen, eine
Groesse - das Muster, an dem in diesem Repo schon oft etwas auseinandergelaufen
ist.

WARUM HIER TROTZDEM NICHTS ZUSAMMENGELEGT WIRD
──────────────────────────────────────────────
Weil die Messung den Verdacht WIDERLEGT. Ueber die erreichbare Domaene
(normMin ist 0|270|510 laut "normMin:_fei?0:(i===4?270:510)", davon geht der
Abwesenheitsabzug ab -> data-norm liegt in [0..510]; usedMin ist eine Summe von
Dauern, also >=0; eigen ist EXAKT st.dauerMin oder 0) gibt es

    0 Entscheidungs-Abweichungen und 0 Zahlen-Abweichungen.

Ein Umbau waere hier also kein Fehler-Fix, sondern eine Umformatierung - und
die Erfahrung dieses Repos ist, dass ein Umbau ohne gemessenen Anlass neue
Fehler einfuehrt, statt welche zu entfernen.

WAS DIESER RIEGEL STATTDESSEN TUT
─────────────────────────────────
Er haelt die GLEICHHEIT fest, nicht die Schreibweise. Bisher stand in
test_dispo_kapazitaet_v790::test_handwand_nutzt_abwabz die Zeile

    assert index_html.count("frei=(norm-used)+eigen;") == 2

Das zaehlt Zeichen. Wer beide Kopien gleichzeitig auf "(norm-used)-eigen"
aendert, laesst diese Zusicherung GRUEN und dreht die Hand-Wand um. Und wer
_dispoAblehnGrund allein anfasst - die dritte Kopie, die dort gar nicht
vorkommt - wird ueberhaupt nicht bemerkt. Dieser Riegel schneidet alle drei
Ausdruecke woertlich aus index.html und FUEHRT SIE AUS.

RICHTIGSTELLUNG ZUM WARN-KOMMENTAR BEI _dispoNormFrei (v3.9.899)
────────────────────────────────────────────────────────────────
Dort steht als Warnung vor dem Zusammenlegen woertlich:

    "Ueberbuchter Tag (norm 510, belegt 600), gezogener Chip liegt schon
     darauf (eigen 90): der Handler bekommt (510-600)+90 = 0 und LEHNT AB,
     eine geklemmte Fassung bekaeme max(0,510-600)+90 = 90 und LIESSE ZU."

Der zweite Halbsatz ist FALSCH, und zwar nachgemessen (test_v899_klemm_beispiel
unten). Die geklemmte Fassung liefert frei=90, und _dispoDropOk verlangt
Dauer+PUFFER_JE_STOPP <= frei, also 90+10 <= 90 - das ist ebenfalls falsch, der
Drop wird ebenfalls ABGELEHNT. Weil eigen strukturell immer entweder 0 oder
genau st.dauerMin ist und der Puffer echt groesser als 0, kann die Klemmung die
Entscheidung ueberhaupt nie umdrehen.

Das ist kein Wortklauben: dieser Kommentar ist die einzige aktenkundige
Begruendung dafuer, die drei Kopien stehen zu lassen. Sie traegt in ihrer
angegebenen Form nicht. Die tragfaehige Begruendung ist die Messung hier - und
die kommt zum selben Ergebnis, nur aus dem richtigen Grund.

Was sich sehr wohl unterscheidet, ist die ANZEIGE: ungeklemmt beziffert der
Toast "0h frei", geklemmt "1,5h frei". Wer je zusammenlegt, muss auf die
UNGEKLEMMTE Fassung zusammenlegen, sonst verspricht der Toast auf ueberbuchten
Tagen freie Zeit, die es nicht gibt.
"""
import re
import subprocess

from conftest import EPK_TEST_TIMEOUT

# Nur die beiden Handler-Zeilen stehen hier als Text - sie werden woertlich
# geschnitten, weil sie mitten in einem Rueckruf sitzen und keinen Namen haben.
# Die dritte Kopie braucht KEINE Textkonstante: _dispoAblehnGrund wird ueber
# seinen Funktionsnamen geschnitten. Eine Konstante fuer ihren Zeilentext waere
# ein Name ohne Leser - und genau der hat diesen Riegel schon einmal am
# Wortlaut abbrechen lassen, bevor er messen konnte (siehe _basis).
MV = "var eigen=(ci===st.srcIso)?st.dauerMin:0, frei=(norm-used)+eigen;"
UP = "var eigen=(ti===st.srcIso)?st.dauerMin:0, frei=(norm-used)+eigen;"


def _pure(index_html, name):
    i = index_html.index("function " + name + "(")
    j = index_html.index("\n}", i) + 2
    return index_html[i:j]


def _kopf(index_html):
    """PUFFER_JE_STOPP + die beiden puren Funktionen woertlich aus index.html."""
    puf = re.search(r"var PUFFER_JE_STOPP=\d+", index_html).group(0)
    return (puf + ";\n"
            + _pure(index_html, "_dispoDropOk") + "\n"
            + _pure(index_html, "_dispoAblehnGrund") + "\n")


# Die beiden Handler-Zweige woertlich, jeweils in eine ausfuehrbare Huelle
# gelegt. Das parseInt auf String-Attribute ist KEINE Nachbildung, sondern
# steht genauso im Handler - React setzt data-norm/data-used als Text.
_HANDLER = """
function _wegMV(normAttr,usedAttr,srcIso,ci,dauerMin){
  var norm=parseInt(normAttr||"0",10), used=parseInt(usedAttr||"0",10);
  var st={srcIso:srcIso,dauerMin:dauerMin,mid:"M1"};
  __MV__
  return {frei:frei,eigen:eigen,ok:_dispoDropOk(st.mid,"M1",false,frei,st.dauerMin)};
}
function _wegUP(normAttr,usedAttr,srcIso,ti,dauerMin){
  var norm=parseInt(normAttr||"0",10), used=parseInt(usedAttr||"0",10);
  var st={srcIso:srcIso,dauerMin:dauerMin,mid:"M1"};
  __UP__
  return {frei:frei,eigen:eigen,ok:_dispoDropOk(st.mid,"M1",false,frei,st.dauerMin)};
}
"""

# Erreichbare Domaene, bewusst NICHT nur in 15-min-Schritten: der Dauer-Griff
# schnappt zwar auf 15, _dispoParseDauer liefert aber beliebige Minuten aus
# Text. Mit einem reinen 15er-Raster waren zwei der fuenf Gegenproben unten
# unsichtbar (Puffer 15 statt 10, und >= statt >) - da hat das RASTER den
# Fehler verdeckt, nicht der Code ihn vermieden. Deshalb 7er/11er-Schritte.
_GITTER = """
var normA=[0,7,30,53,60,120,150,210,240,270,300,390,450,509,510];
var usedA=[]; for(var _u=0;_u<=960;_u+=7)usedA.push(_u);
var dauerA=[]; for(var _d=0;_d<=600;_d+=11)dauerA.push(_d);
var ISO="2026-09-02";
function durchlauf(zweigB){
  var n=0, abwEnt=0, abwZahl=0, bsp=null;
  for(var i=0;i<normA.length;i++)for(var j=0;j<usedA.length;j++)for(var l=0;l<dauerA.length;l++)
  for(var e=0;e<2;e++){
    var nm=normA[i], um=usedA[j], dm=dauerA[l];
    /* e=1: der gezogene Chip liegt schon auf dem Zieltag -> eigen=dauerMin */
    var a=_wegMV(String(nm),String(um),e?ISO:"2026-09-01",ISO,dm);
    var b=zweigB(nm,um,dm,a.eigen);
    n++;
    if(a.ok!==(b===null)){abwEnt++; if(!bsp)bsp="norm="+nm+" used="+um+" dauer="+dm+
      " eigen="+a.eigen+" | Handler frei="+a.frei+" ok="+a.ok+" | Toast-Zweig="+JSON.stringify(b);}
    if(typeof b==="string" && b.indexOf("Tagesnorm")===0){
      var mm=b.match(/,\\s*(-?[0-9,]+)h frei/);
      if(mm){ var gez=parseFloat(mm[1].replace(",","."))*60, wand=(a.frei<0?0:a.frei);
        /* Der Toast rundet auf 0,1 h = 6 min -> zulaessige Abweichung 3 min. */
        if(Math.abs(gez-wand)>3.000001){abwZahl++; if(!bsp)bsp="norm="+nm+" used="+um+
          " dauer="+dm+" eigen="+a.eigen+" | Wand="+wand+" min | Toast beziffert "+gez+" min";}}}
  }
  return {n:n,ent:abwEnt,zahl:abwZahl,bsp:bsp};
}
function echterToastZweig(nm,um,dm,eg){ return _dispoAblehnGrund("",nm,um,dm,eg); }
"""


def _lauf(node_exe, tmp_path, name, js):
    f = tmp_path / (name + ".js")
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    return r.stdout


def _basis(index_html):
    # Diese beiden Zeilen werden WOERTLICH geschnitten - also muss der Schnitt
    # eindeutig sein. Das ist eine Aussage ueber das Messgeraet, keine ueber das
    # Verhalten des Codes.
    assert index_html.count(MV) == 1, "pointermove-Zweig der Hand-Wand nicht eindeutig gefunden"
    assert index_html.count(UP) == 1, "pointerup-Zweig der Hand-Wand nicht eindeutig gefunden"
    #
    # HIER STAND EINMAL:
    #   assert index_html.count("var frei=(normMin||0)-(usedMin||0)+(eigen||0);") == 1
    # Sie ist RAUS, und das ist der Punkt. _dispoAblehnGrund wird ueber seinen
    # FUNKTIONSNAMEN geschnitten, nicht ueber diesen Zeilentext - der Riegel
    # braucht ihn also nicht. Er hat aber Schaden angerichtet: bei der
    # Gegenprobe (nur _dispoAblehnGrund verstellt) schlug er ZUERST an und
    # verdeckte damit, dass die ausgefuehrte Messung darunter ebenfalls rot
    # wird. Ein Riegel, der am Wortlaut abbricht, bevor er misst, laesst nicht
    # pruefen, ob er ueberhaupt messen kann. Ohne ihn faellt der Test dort, wo
    # er soll: an der Entscheidungs-Abweichung.
    return (_kopf(index_html)
            + _HANDLER.replace("__MV__", MV).replace("__UP__", UP)
            + _GITTER)


def test_drei_kopien_eine_groesse(index_html, node_exe, tmp_path):
    """Die drei Rechnungen liefern ueber die erreichbare Domaene dasselbe.

    Gemessen wird die EIGENSCHAFT: alle drei Ausdruecke werden woertlich aus
    index.html geschnitten und AUSGEFUEHRT. Entscheidung (Drop erlaubt?) UND
    die im Toast bezifferte Restzeit muessen uebereinstimmen.
    """
    js = _basis(index_html) + """
var r=durchlauf(echterToastZweig);
console.log("FAELLE "+r.n);
console.log("ENT "+r.ent);
console.log("ZAHL "+r.zahl);
if(r.bsp)console.log("BSP "+r.bsp);
/* pointermove und pointerup muessen Wert fuer Wert dasselbe liefern */
var uneins=0, ubsp="";
for(var i=0;i<normA.length;i++)for(var j=0;j<usedA.length;j++)for(var l=0;l<dauerA.length;l++)
for(var e=0;e<2;e++){
  var s=e?ISO:"2026-09-01";
  var m1=_wegMV(String(normA[i]),String(usedA[j]),s,ISO,dauerA[l]);
  var m2=_wegUP(String(normA[i]),String(usedA[j]),s,ISO,dauerA[l]);
  if(m1.ok!==m2.ok||m1.frei!==m2.frei||m1.eigen!==m2.eigen){uneins++;
    if(!ubsp)ubsp=" norm="+normA[i]+" used="+usedA[j]+" dauer="+dauerA[l];}
}
console.log("MVUP "+uneins+ubsp);
"""
    out = _lauf(node_exe, tmp_path, "handwand916", js)
    n = int(re.search(r"FAELLE (\d+)", out).group(1))
    ent = int(re.search(r"ENT (\d+)", out).group(1))
    zahl = int(re.search(r"ZAHL (\d+)", out).group(1))
    mvup = int(re.search(r"MVUP (\d+)", out).group(1))
    m_bsp = re.search(r"BSP (.+)", out)
    bsp = m_bsp.group(1) if m_bsp else "(keins)"
    assert n > 200000, "Gitter zu klein - eine Messung ohne Faelle ist keine Messung (%d)" % n
    assert mvup == 0, ("pointermove (Live-Feedback gruen/rot) und pointerup (das Schreiben) "
                       "rechnen die Hand-Wand nicht mehr gleich - genau dort entsteht "
                       "'gruen angezeigt, aber abgelehnt'.\n%s" % out)
    assert ent == 0, ("Die Hand-Wand (Drag-Handler -> _dispoDropOk) und der Ablehn-Toast "
                      "(_dispoAblehnGrund) entscheiden verschieden. Der Anwender bekommt dann "
                      "eine Ablehnung ohne Grund oder einen Grund ohne Ablehnung. "
                      "Beispiel: %s" % bsp)
    assert zahl == 0, ("Der Ablehn-Toast beziffert eine andere Restzeit, als die Wand "
                       "wirklich benutzt hat. Beispiel: %s" % bsp)


def test_gegenprobe_der_riegel_sieht_drift(index_html, node_exe, tmp_path):
    """GEGENPROBE: kann dieser Riegel einen Drift ueberhaupt sehen?

    Ein Riegel, dessen rote Lampe nie angeht, misst nichts. Deshalb wird die
    dritte Kopie hier kuenstlich verstellt - jede Verstellung ist eine, die
    beim Bearbeiten EINER von drei Stellen real entstehen kann - und der
    Durchlauf MUSS rot werden.

    Bewusst NICHT in dieser Liste: das Klemmen auf 0. Das ist die einzige
    Verstellung, die die ENTSCHEIDUNG nachweislich nie umdreht (Begruendung
    und Messung in test_v899_klemm_beispiel) - sie fehlt hier also aus einem
    belegten Grund, nicht aus Blindheit des Messgeraets.
    """
    js = _basis(index_html) + """
function zeig(k,f){var r=durchlauf(f);console.log(k+" "+r.ent);}
zeig("M2", function(nm,um,dm,eg){var f=nm-um;    return ((dm+PUFFER_JE_STOPP)>f)?"Tagesnorm: x":null;});
zeig("M3", function(nm,um,dm,eg){var f=nm-um+eg; return ((dm+15)>f)?"Tagesnorm: x":null;});
zeig("M4", function(nm,um,dm,eg){var f=nm-um-eg; return ((dm+PUFFER_JE_STOPP)>f)?"Tagesnorm: x":null;});
zeig("M5", function(nm,um,dm,eg){var f=nm-um+eg; return ((dm+PUFFER_JE_STOPP)>=f)?"Tagesnorm: x":null;});
zeig("M6", function(nm,um,dm,eg){var f=nm-um+eg; return (dm>f)?"Tagesnorm: x":null;});
"""
    out = _lauf(node_exe, tmp_path, "handwand916_gegen", js)
    erwartet = {
        "M2": "eigen vergessen (v752 #30a nur an 2 von 3 Kopien nachgezogen)",
        "M3": "Puffer 15 statt 10 an nur einer Stelle",
        "M4": "Vorzeichendreher: -eigen statt +eigen",
        "M5": ">= statt > in der Schwelle",
        "M6": "Puffer in einer Kopie ganz vergessen",
    }
    for k in sorted(erwartet):
        n = int(re.search(k + r" (\d+)", out).group(1))
        assert n > 0, ("GEGENPROBE GESCHEITERT: die Verstellung '%s' (%s) macht den "
                       "Riegel NICHT rot. Dann sichert er nichts.\n%s"
                       % (k, erwartet[k], out))


def test_v899_klemm_beispiel(index_html, node_exe, tmp_path):
    """Der Warn-Kommentar bei _dispoNormFrei nennt ein Beispiel, das nicht stimmt.

    Behauptet: die geklemmte Fassung "LIESSE ZU". Gemessen: sie lehnt genauso
    ab, weil _dispoDropOk Dauer+PUFFER verlangt und eigen strukturell entweder
    0 oder genau die Dauer ist. Was sich sehr wohl unterscheidet, ist die im
    Toast bezifferte Restzeit - deshalb wird auch DAS hier festgehalten.
    """
    js = _kopf(index_html) + """
/* woertlich die Zahlen aus dem Kommentar: norm 510, belegt 600, eigen 90 */
var freiOffen = (510-600)+90;              /* die laufende, ungeklemmte Fassung */
var freiKlemm = Math.max(0,510-600)+90;    /* die Fassung, vor der der Kommentar warnt */
console.log("OFFEN_FREI "+freiOffen);
console.log("KLEMM_FREI "+freiKlemm);
console.log("OFFEN_OK "+_dispoDropOk('M1','M1',false,freiOffen,90));
console.log("KLEMM_OK "+_dispoDropOk('M1','M1',false,freiKlemm,90));
/* und der Unterschied, den es WIRKLICH gibt: die bezifferte Restzeit im Toast */
console.log("TOAST_OFFEN "+_dispoAblehnGrund("",510,600,90,90));
"""
    out = _lauf(node_exe, tmp_path, "handwand916_v899", js)
    assert "OFFEN_FREI 0" in out and "KLEMM_FREI 90" in out, out
    assert "OFFEN_OK false" in out, out
    assert "KLEMM_OK false" in out, (
        "Wenn das hier true wird, stimmt der v899-Kommentar doch - dann diese "
        "Richtigstellung zurueckziehen.\n" + out)
    assert "0h frei" in out, (
        "Die ungeklemmte Fassung muss auf einem ueberbuchten Tag '0h frei' beziffern; "
        "eine geklemmte wuerde hier '1,5h frei' sagen. Genau das ist der einzige echte "
        "Unterschied der beiden Fassungen.\n" + out)
