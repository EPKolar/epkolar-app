# -*- coding: utf-8 -*-
"""v3.9.1012 - CI-Stufe 3, Bereich zeit_planung: Wochenplanung, Zeiterfassung,
Abwesenheiten, Monatsabrechnung ohne Emoji in Bedienelementen.

Riegel auf die EIGENSCHAFT:
  * In den vier Ansichten steht kein Emoji mehr in Knoepfen, Reitern, Karten-
    koepfen, Chips oder Hinweisen. Gezaehlt wird jedes Emoji (Regex wie
    test_ikonen_navigation_v1010); ERLAUBT ist nur eine benannte Restmenge:
    Toast-, Push-, Bestaetigungs-, Excel-/Vorschau- und Drucktexte (die laut
    Auftrag unangetastet bleiben) und die Schriftzeichen ✓ ✕ (Haken/Kreuz,
    kein Bild-Emoji). Alles andere ist ein Treffer.
  * Jeder _ik/_zpIk-Schluessel der vier Ansichten hat eine Zeichnung in IKON
    (sonst zeichnet _ik ein leeres SVG - unsichtbarer Knopf ohne Fehler).
  * Samstag traegt in der Planung kein Rot mehr (Rahmen, Kopf-Hintergrund,
    Kopf-Schrift). v3.9.1008 hatte nur die Tageswahl neutralisiert.
  * Die Kachel "Ausstehend" erfindet kein "+ ?" mehr: sie zeigt die gemessene
    Zahl und sagt, was nicht gezaehlt ist.
Jeder Riegel hat eine Umkehrprobe.
"""
import re

import pytest

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿⌀-⏿️]")
SCHRIFTZEICHEN = set("✓✕")  # Haken / Kreuz - typografisch, kein Bild-Emoji

BEREICHE = {
    "Wochenplanung": ("\nfunction WeekPlan(", "\nfunction AbsView("),
    "Abwesenheiten": ("\nfunction AbsView(", "\nfunction SvgBar("),
    "Monatsabrechnung": ("\nfunction StundenzettelView(", "\nfunction PhotoSyncStatus("),
    "Zeiterfassung": ("\nfunction ZeiterfassungView(", "\nconst WMO_ICON="),
}

# Zeilen-Kontext VOR dem Treffer, der ihn zur erlaubten Restmenge macht.
ERLAUBT = (
    "__toast", "_showToast", "pushNotif", "_confirmModal", "_plMsg", "_apMsg",
    "genXls(", "_exportReviewModal", "confirmLabel", "reviewRows",
    "r.bvh===", "label:\"", "title:\"", "<td", "<span class", "<div style",
    "ZEIT_BIS_VOR_VON_MSG",
)


def _ohne_kommentare(text):
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def _bereich(code, name):
    a, e = BEREICHE[name]
    i = code.index(a)
    j = code.index(e, i)
    return _ohne_kommentare(code[i:j])


def _treffer(teil):
    """(erlaubt, verboten) - je Treffer der Zeilenanfang bis zum Emoji."""
    erl, verb = [], []
    for m in EMOJI.finditer(teil):
        z = m.group()
        if z == "️" or z in SCHRIFTZEICHEN:
            continue
        anf = teil.rfind("\n", 0, m.start()) + 1
        vor = teil[max(anf, m.start() - 220):m.start()]
        (erl if any(k in vor for k in ERLAUBT) else verb).append(vor[-60:] + z)
    return erl, verb


def _ikon_schluessel(code):
    i = code.index("const IKON={")
    j = code.index("};function _ik(", i)
    return set(re.findall(r'(?:[{,]|\*/)([a-z]+):\[', code[i:j]))


@pytest.mark.parametrize("name", sorted(BEREICHE))
def test_kein_emoji_in_bedienelementen(index_html, name):
    teil = _bereich(index_html, name)
    erl, verb = _treffer(teil)
    assert not verb, "%s: Emoji ausserhalb der erlaubten Restmenge:\n%s" % (
        name, "\n".join(repr(v) for v in verb))


# Obergrenze der Restmenge je Ansicht (gemessen v3.9.1012). Waechst sie, ist
# entweder ein neuer Toast dazugekommen (dann Grenze heben) oder ein Emoji
# hat sich hinter einem Erlaubt-Wort versteckt.
RESTMENGE = {"Wochenplanung": 18, "Abwesenheiten": 40, "Monatsabrechnung": 16,
             "Zeiterfassung": 34}


@pytest.mark.parametrize("name", sorted(BEREICHE))
def test_restmenge_bleibt_begrenzt(index_html, name):
    erl, _ = _treffer(_bereich(index_html, name))
    assert len(erl) <= RESTMENGE[name], "%s: Restmenge %d > %d:\n%s" % (
        name, len(erl), RESTMENGE[name], "\n".join(repr(v) for v in erl))
    # Koeder: die Restmenge ist nicht leer - sonst misst der Filter nichts
    assert len(erl) >= 5, "%s: Restmenge nur %d - Bereichsanker pruefen" % (name, len(erl))


def test_umkehrprobe_emoji_im_knopf_wird_erkannt(index_html):
    teil = _bereich(index_html, "Wochenplanung")
    assert '_zpIk("kalender","Nächste Woche ▶")' in teil
    kaputt = teil.replace('_zpIk("kalender","Nächste Woche ▶")', '"\U0001F4C5 Nächste Woche ▶"', 1)
    assert _treffer(kaputt)[1], "eingesetztes Emoji im Knopf wurde nicht erkannt"
    toast = teil + '\nwindow.__toast("\U0001F4C5 nur ein Toast");'
    assert not _treffer(toast)[1], "Toast-Emoji darf nicht als Treffer zaehlen"


@pytest.mark.parametrize("name", sorted(BEREICHE))
def test_jeder_ikonenschluessel_hat_eine_zeichnung(index_html, name):
    teil = _bereich(index_html, name)
    werte = re.findall(r'_(?:ik|zpIk|zpIkI)\(["\']([a-z]+)["\']', teil)
    werte += re.findall(r'\bik:"([a-z]+)"', teil)
    assert werte, "%s: keine Ikone gefunden - Muster pruefen" % name
    sch = _ikon_schluessel(index_html)
    fehlt = sorted(set(w for w in werte if w not in sch))
    assert not fehlt, "%s: Schluessel ohne Zeichnung in IKON: %s" % (name, fehlt)


def test_neue_ikonen_sind_angehaengt_und_lizenziert(index_html):
    sch = _ikon_schluessel(index_html)
    for k in ("drucker", "tabelle", "brief", "klammer", "speichern", "auge",
              "download", "senden", "kopie", "fieber"):
        assert k in sch, k
    i = index_html.index("const IKON={")
    kopf = index_html[i:index_html.index("};function _ik(", i)]
    assert "v3.9.1012 CI-Stufe 3" in kopf and "Lucide (ISC" in kopf


def test_helfer_bleiben_aria_hidden(index_html):
    for n in ("function _zpIk(", "function _zpIkI(", "function _zpWarn(", "function _zpAbsK("):
        assert index_html.count(n) == 1, n
    i = index_html.index("function _zpIkI(")
    assert "'aria-hidden':\"true\"" in index_html[i:i + 300]
    i = index_html.index("function _zpWarn(")
    assert "role:\"img\",'aria-label':lbl" in index_html[i:i + 400]


def test_samstag_ohne_rot_in_der_planung(index_html):
    teil = _bereich(index_html, "Wochenplanung")
    rot = re.findall(r"isSa\?[^:,)]{0,40}(?:239,68,68|#ef4444|#dc2626|COLORS\.ERROR)", teil)
    assert not rot, "Samstag traegt wieder Rot: %r" % rot
    assert "border:'1px solid '+(isToday?V.ac:V.bd)," in teil
    # Umkehrprobe: der alte Zellrahmen faellt auf
    alt = teil.replace("border:'1px solid '+(isToday?V.ac:V.bd),",
                       "border:'1px solid '+(isToday?V.ac:(isSa?'rgba(239,68,68,.35)':V.bd)),", 1)
    assert re.findall(r"isSa\?[^:,)]{0,40}(?:239,68,68|#ef4444)", alt)


def test_abwesenheit_ohne_lila_und_blau_in_der_planung(index_html):
    teil = _bereich(index_html, "Wochenplanung")
    assert 'const KR=UI.achtungTxt, UR=UI.markeTxt, ZA=UI.neutralTxt;' in teil
    assert 'const KR="#ef4444", UR="#3b82f6", ZA="#a855f7";' not in teil


def test_ausstehend_erfindet_kein_fragezeichen(index_html):
    teil = _bereich(index_html, "Abwesenheiten")
    assert '" + ?"' not in teil, "Kachel zeigt wieder '0 + ?'"
    i = teil.index('React.createElement(Kpi, { label: pendingUnklar?"Ausstehend (nur Kalender)":"Ausstehend"')
    kachel = teil[i:i + 700]
    assert "value: pendingGesamt," in kachel
    assert "noch nicht gezählt" in kachel
    # Umkehrprobe
    assert '" + ?"' in teil.replace("value: pendingGesamt,", 'value: pendingUnklar?(pendingCount+" + ?"):pendingGesamt,', 1)


def test_stunden_chips_mit_kurzlabel_lesbar(index_html):
    teil = _bereich(index_html, "Abwesenheiten")
    for k, t in (("U", "Urlaub"), ("K", "Krankenstand"), ("ZA", "Zeitausgleich")):
        assert '{ title: "%s", style: {' % t in teil
        # Kurzlabel INLINE (die Kompaktliste laeuft in test_ausgetretene_live_v931 ohne _zpAbsK)
        assert 'textAlign:"center",color:V.tx}}, "%s")' % k in teil or '_zpAbsK("%s")' % k in teil
    # Lila (#a855f7) und Blau (#3b82f6) trugen keine Bedeutung - ausserhalb des Excel-Exports nirgends mehr
    ohne_excel = re.sub(r"statusMap:\{[^}]*\}", "", teil)
    # Ausnahme mit Grund: test_v3862_bugfixes findet den Urlaub-Tabellenkopf (Tooltip-Riegel) ueber #3b82f6
    ohne_excel = ohne_excel.replace('color:"#3b82f6"}, title: "Urlaubs-Stunden gesamt', "", 1)
    for f in ("#a855f7", "#3b82f6", "#6ea8ff"):
        assert f not in ohne_excel, "Fremdfarbe %s in den Abwesenheiten" % f
    assert "#a855f7" in teil, "Koeder: der Excel-Export behaelt seine Farbtabelle (unangetastet)"
    for rumpf in (index_html[index_html.index("function _zpAbsK("):][:400],
                  teil[teil.index('{ title: "Urlaub", style: {'):][:600]):
        assert "fontSize:UI.fMeta" in rumpf and "fontWeight:800" in rumpf, "Kurzlabel unter 12 px?"


def test_monatsabrechnung_kacheln_ohne_blau(index_html):
    teil = _bereich(index_html, "Monatsabrechnung")
    i = teil.index('[{l:"Gesamt",v:meineZettel.length')
    kpi = teil[i:i + 700]
    assert "#3b82f6" not in kpi
    assert '"2px solid "+UI.marke' in teil, "Auswahlrahmen nicht Markengruen"
