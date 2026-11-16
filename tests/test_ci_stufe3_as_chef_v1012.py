# -*- coding: utf-8 -*-
"""v3.9.1012 CI-Stufe 3 - Arbeitsscheine-Seite und Chef-Portal ohne Emoji.

Gezaehlt wird im SICHTBAREN Teil der beiden Seiten (Kommentare raus, ueber
_hilfen.nur_code):

  Arbeitsscheine  ab dem Seitentitel _ikT("bericht","Arbeitsscheine / Störungen")
                  bis zum Ende von ArbeitsscheinView (Liste, Karte, Rechner-Zeile,
                  QR-Scan, QR-Fenster, Kalender, Bearbeitungsformular)
  Chef-Portal     ab `var CD_TABS=` bis zum Ende von ChefDashboard

Was danach noch an Emoji steht, ist eine BEGRUENDETE Restmenge - jede Stelle
steht unten mit ihrem Grund. Der Riegel verlangt: nach Abzug genau dieser
Stellen bleibt KEIN Emoji uebrig, und jede Ausnahme kommt noch vor (eine
veraltete Ausnahme waere ein stilles Loch in der Liste).

Gruende der Restmenge:
  * Toast-, Rueckfrage- und Scan-Meldungstexte (Regel: Toast-Texte nicht anfassen;
    asScanMsg wird ueber startsWith("✅"/"❌") eingefaerbt - das ist Logik).
  * OFFA/Juprowa: Knopf "📊 OFFA Excel" (test_offa_import_removed_v780 pinnt den
    Wortlaut, offa-Tests werden nie angepasst), OFFA-Banner (Auftrag: nicht
    anfassen), Push-/Juprowa-Kennzeichen im Formular und der Wolken-Knopf der
    Rechner-Zeile (test_as_zeile_flaechen_v920: Warnzeichen bleiben Wort fuer Wort),
    Kontaktblock "(OFFA)", Juprowa-Monteurcode-Zuordnung (Admin).
  * Formular-Auftragstyp zeigt Icon+Label aus AS_ART (Vertrag in
    test_scheinart_push_v797 / test_as_formular_kein_dropdown_v803) - steht nicht
    als Literal hier, AS_ART ist eine globale Tabelle.
  * Hinweistexte (Schloss bei abgeschlossenem Schein / Monteur legt nur fuer sich
    an, Mikrofon am Diktierfeld) - kein Knopf, Reiter, Chip oder Kartenkopf.
  * Chef: _ampLbl und die Budget-Ampel p.amp sind in test_bughunt_2026_06_17 als
    Schwellen-Riegel samt Emoji gepinnt. Angezeigt wird jetzt ein Punkt; _CD_AMPEL
    ordnet den gepinnten Ampelwert der Punktfarbe zu (Emoji nur als Schluessel).
"""
import re

import pytest

from _hilfen import nur_code

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿⌀-⏿️]")

AS_ANFANG = '_ikT("bericht","Arbeitsscheine / Störungen")'
AS_ENDE = "function _ezWtag("
CHEF_ANFANG = "var CD_TABS=["
CHEF_ENDE = "function FahrtenbuchPanel("

AS_REST = [
    # OFFA / Juprowa
    '"📊 OFFA Excel"',
    # WARNUNGEN 16.11.: '"⚠ "+"OFFA-Feed' entfaellt - der Feed-Kasten ist jetzt eine Hinweis-Zeile mit Linien-Ikone (keine Emojis)
    '"⚠ "+um.length+" unbekannte Monteur-Codes: "',
    '"❌ ausgeschieden"',
    '_2("✅ "+code+" → "',
    'title: a.push_error?"⚠ Push-Fehler: "',
    'a.push_error?"⚠↻":"☁️↑"',
    '"🔗 Juprowa #"',
    '"⬆ Push ausstehend"',
    '"✓ Gepusht: "',
    '"❌ ",_kurz(form.push_error',
    '"⚠ in OFFA prüfen"',
    'jupPushing?"⏳...":"☁️↑ Push"',
    '"🔗 OFFA"',
    '"⚠ Monteur nicht nach OFFA übertragbar',
    '"📞 Kontakt (OFFA)"',
    '"☎"',
    '"✉"',
    # Scan-Meldung (Faerbung haengt am ersten Zeichen)
    'asScanMsg.startsWith("✅")',
    'asScanMsg.startsWith("❌")',
    # Toasts
    '"📋 Link kopiert"',
    '"⚠ Kopieren fehlgeschlagen',
    '"📋 Link kopiert (Fallback)":"⚠ Clipboard nicht verfügbar"',
    '"⚠ Clipboard nicht verfügbar — Link manuell markieren"',
    '"✓ Vorschlag übernommen',
    '"✓ "+_nr+',
    '"🔓 Sperre aufgehoben"',
    '"🚫 Tag gesperrt: "',
    '"⚠️ Sperren-Tabelle',
    '"❌ Sperre nicht gespeichert: "',
    '"⚠️ Ungültiger Status-Wechsel von "',
    '"⚠️ Bitte Datum wählen"',
    # Hinweistexte
    '"🔒 Dieser Schein ist abgeschlossen ("',
    '"🔒 Du legst nur für dich selbst an"',
    '"Durchzuführen * 🎤"',
    '"Notizen 🎤"',
]

CHEF_REST = [
    "const _CD_AMPEL={'⚪':[V.mt,'kein Budget hinterlegt'],'🟢':[_okG('#22c55e'),'im Budget'],"
    "'🟡':['#eab308','Budget knapp'],'🔴':['#ef4444','über Budget']};",
    "const _ampLbl=pct=>pct<70?'🟢 Luft für neue Aufträge':pct<90?'🟡 gut ausgelastet':"
    "pct<=100?'🟠 am Anschlag':'🔴 überlastet';",
]


def _bereich(html, a, e):
    i = html.index(a)
    j = html.index(e, i)
    return nur_code(html[i:j])


def _ikon_schluessel(code):
    i = code.index("const IKON={")
    j = code.index("};function _ik(", i)
    return set(re.findall(r'(?:[{,]|\*/)([a-z]+):\[', code[i:j]))


def _rest_abziehen(teil, rest):
    fehlt = [r for r in rest if r not in teil]
    for r in rest:
        teil = teil.replace(r, "")
    return teil, fehlt


def _emoji_stellen(teil):
    return [teil[max(0, m.start() - 40):m.end() + 20] for m in EMOJI.finditer(teil)]


@pytest.mark.parametrize("name,a,e,rest", [
    ("Arbeitsscheine", AS_ANFANG, AS_ENDE, AS_REST),
    ("Chef-Portal", CHEF_ANFANG, CHEF_ENDE, CHEF_REST),
])
def test_bereich_ohne_emoji_bis_auf_die_begruendete_restmenge(index_html, name, a, e, rest):
    teil, fehlt = _rest_abziehen(_bereich(index_html, a, e), rest)
    assert not fehlt, "%s: Ausnahme(n) kommen nicht mehr vor - Liste nachziehen: %r" % (name, fehlt)
    stellen = _emoji_stellen(teil)
    assert not stellen, "%s: %d Emoji ausserhalb der Restmenge: %r" % (name, len(stellen), stellen[:8])


def test_umkehrprobe_ein_eingesetztes_emoji_wird_erkannt(index_html):
    kaputt = index_html.replace('{key:"meine",label:"Meine",ik:"person"}',
                                '{key:"meine",label:"\U0001F464 Meine"}', 1)
    assert kaputt != index_html
    teil, _ = _rest_abziehen(_bereich(kaputt, AS_ANFANG, AS_ENDE), AS_REST)
    assert _emoji_stellen(teil)
    kaputt = index_html.replace("['ueberblick','krone','Überblick']", "['ueberblick','\U0001F451','Überblick']", 1)
    assert kaputt != index_html
    teil, _ = _rest_abziehen(_bereich(kaputt, CHEF_ANFANG, CHEF_ENDE), CHEF_REST)
    assert _emoji_stellen(teil)


def _verwendete_schluessel(index_html):
    asb = _bereich(index_html, AS_ANFANG, AS_ENDE)
    chef = _bereich(index_html, CHEF_ANFANG, CHEF_ENDE)
    sch = set(re.findall(r'_asIk\("([a-z]+)"', asb))
    sch |= set(re.findall(r'_ik\("([a-z]+)"', asb))
    sch |= set(re.findall(r'\bik:"([a-z]+)"', asb))
    m = re.search(r"var CD_TABS=\[(.*?)\];", chef)
    sch |= set(re.findall(r"\['[a-z]+','([a-z]+)','", m.group(1)))
    sch |= set(re.findall(r"_card\('[a-z]+','([a-z]+)'", chef))
    return sch


def test_jeder_verwendete_schluessel_hat_eine_zeichnung(index_html):
    """_ik zeichnet bei unbekanntem Schluessel ein LEERES svg - ein Knopf ohne
    Symbol und ohne Fehlermeldung. Deshalb jeder Schluessel gegen IKON."""
    sch = _verwendete_schluessel(index_html)
    assert len(sch) >= 20, "nur %d Schluessel gefunden - Muster pruefen: %r" % (len(sch), sorted(sch))
    fehlt = sorted(sch - _ikon_schluessel(index_html))
    assert not fehlt, "Schluessel ohne Zeichnung in IKON: %r" % fehlt
    for neu in ("qr", "verbot"):
        assert neu in _ikon_schluessel(index_html)


def test_umkehrprobe_unbekannter_schluessel_faellt_auf(index_html):
    kaputt = index_html.replace("_card('gs','kolben',", "_card('gs','gibtsnicht',", 1)
    assert kaputt != index_html
    assert "gibtsnicht" in _verwendete_schluessel(kaputt)
    assert "gibtsnicht" not in _ikon_schluessel(kaputt)


def test_status_als_punkt_nicht_als_emoji(index_html):
    asb = _bereich(index_html, AS_ANFANG, AS_ENDE)
    assert "_asPkt(st.c), st.l" in asb, "Status-Abzeichen der Karte ohne Punkt"
    assert "st.i" not in asb, "Status-Emoji (AS_STATUS.i) wird wieder angezeigt"
    assert 'v.i+" "+v.l' not in asb, "Status-Emoji in Kachel oder Auswahl zurueck"
    chef = _bereich(index_html, CHEF_ANFANG, CHEF_ENDE)
    assert "fontSize:16}},p.amp)" not in chef, "Budget-Ampel zeigt wieder das Emoji"
    assert "_cdPkt((_CD_AMPEL[p.amp]" in chef
    assert "_ampLbl(kapPct))" not in chef, "Auslastung zeigt wieder das Ampel-Emoji"


def test_keine_zierfarbe_in_chef_karten_und_kalender(index_html):
    chef = _bereich(index_html, CHEF_ANFANG, CHEF_ENDE)
    for f in ("#a855f7", "#6366f1", "#0ea5e9", "#d97706"):
        assert f not in chef, "Zierfarbe %s im Chef-Portal" % f
    asb = _bereich(index_html, AS_ANFANG, AS_ENDE)
    kal = asb[asb.index('sub==="kalender"'):asb.index('sub==="dispo"')]
    assert "#8b5cf6" not in kal and "139,92,246" not in kal, "Violett im Arbeitsschein-Kalender"


def test_die_logik_daneben_ist_unberuehrt(index_html):
    """Nur Anzeige: Klickwege, OFFA-Export und Chip-Schluessel bleiben."""
    asb = _bereich(index_html, AS_ANFANG, AS_ENDE)
    for weg in ("onClick:()=>exportOffa(k)", "onClick: ()=>setShowExportPicker(p=>!p), style: {...xBtn(\"xls\")}}, \"📊 OFFA Excel\"",
                "onClick:()=>setQuickFilter(chip.key)", "storno(a.id);", "openEdit(a);", "genAsPdf(a);",
                "setAsShowQR(asShowQR===a.id?null:a.id);"):
        assert weg in asb, weg
    for k in ("offen", "inarbeit", "erledigt", "meine", "heute", "ueberfaellig", "keinmonteur"):
        assert '{key:"%s",label:' % k in asb, k
