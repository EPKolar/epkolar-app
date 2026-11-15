# -*- coding: utf-8 -*-
"""v3.9.1012 - CI-Stufe 3, Bereich VERWALTUNG.

Administration, Mitarbeiter (samt Stempel-Pausenregeln und KV-Konstanten),
Einstellungen, Werkzeuge & Geraete, Auswertungen, Flotte/Fahrzeuge,
Gefahrenstoffe, Bauprovisorien und Buero-Portal.

Vorher trugen hier Knoepfe, Reiter, Filter-Chips, Kartenkoepfe und Avatare
Emojis (rund 880 Treffer in den zehn Komponenten), aktive Reiter und der
gewaehlte Diagrammtyp leuchteten in Fremdfarben (Blau, Violett, ein roter
Rahmen), und vor JEDER Person stand ein Bauarbeiter - auch vor Buero und
Geschaeftsfuehrung.

Die Riegel halten die EIGENSCHAFT fest:
  * in jedem der zehn Bereiche steht kein SICHTBARES Emoji mehr - ausser der
    begruendeten Restmenge (unten),
  * die genannten Leisten (Admin-Reiter, Rollen-Chips, Buero-Reiter,
    Werkzeug-Reiter und -Chips, Diagrammtypen) sind emojifrei und aktiv
    Markengruen,
  * jeder Ikonen-Schluessel, den der Bereich zeichnet, existiert in IKON,
  * die Kachel "Login heute" zaehlt, was sie sagt, und zeigt "—", wenn der
    Login-Stempel nicht lesbar ist,
  * das Kaestchen "Labels inkl. stillgelegter/verlorener" ist sichtbar.

BEGRUENDETE RESTMENGE (wird gezaehlt, aber nicht als Verstoss):
  * Toast-, Status- und Rueckfrage-Texte (__toast, _toast, set*Msg,
    set*Status, _confirmModal/confirm, alert) - Auftrag: nicht anfassen; an
    mehreren Stellen wird der Statustext per startsWith("✅") ausgewertet.
  * Excel-/CSV-/Push-Texte (genXls, rows.push, pushNotif, _exportReviewModal).
  * ACT_LABELS - speist auch den CSV-Export des Aktivitaetsprotokolls.
  * der Reiter Juprowa: Inhalt tabu (nur der Reitername verlor sein Emoji).
  * Favoriten-Stern und Sterne-Bewertung (★/☆) - Schalterzustand, kein
    Ziersymbol; _ik kennt keine gefuellte Form.
  * "⬆" in der Installationsanleitung: zeigt das iOS-Teilen-Zeichen, das der
    Nutzer am Geraet SUCHEN muss.
"""
import re

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿⌀-⏿️]")

BEREICHE = [
    ("Mitarbeiter/KV/Pausen", "\nfunction KVRulesConfig(", "\nfunction _dispoMinToHHMM("),
    ("Buero-Portal", "\nfunction VBueroExport(", "\nfunction AdminPanel("),
    ("Administration", "\nfunction AdminPanel(", "\nfunction OfflineBanner("),
    ("Einstellungen", "\nfunction VerbindungView(", "\nfunction SmokeTestPanel("),
    ("Auswertungen", "\nfunction AuswertungView(", "\nfunction ZeiterfassungView("),
    ("Flotte", "\nfunction FlotteView(", "\nfunction FahrzeugView("),
    ("Fahrzeuge", "\nfunction FahrzeugView(", "\nconst DEMO_FZ=["),
    ("Gefahrenstoffe", "\nfunction VGefahrstoff(", "\nfunction BauprovisorienView("),
    ("Bauprovisorien", "\nfunction BauprovisorienView(", "\nfunction WerkzeugView("),
    ("Werkzeuge", "\nfunction WerkzeugView(", "\nvar App=exports.default"),
]

REST_KONTEXT = re.compile(
    r"__toast|_showToast|_toast\(|Msg\(|Status\(|onfirm|alert\(|genXls|"
    r"pushNotif|_exportReviewModal|startsWith|indexOf\(|rows\.push\(|_msg=")
REST_ZEICHEN = {"★", "☆"}


def _schnitt(html, a, e):
    i = html.index(a)
    j = html.index(e, i + 10)
    return html[i:j]


def _ohne_kommentare(t):
    return re.sub(r"/\*.*?\*/", lambda m: " " * len(m.group(0)), t, flags=re.S)


def _ohne_tabu(t):
    """Juprowa-Reiter, Export-Modal und ACT_LABELS durch Leerraum ersetzen."""
    for a, e in (('adminTab==="juprowa"&&(', 'adminTab==="haendler"&&('),
                 ("const ACT_LABELS={", "};")):
        i = t.find(a)
        if i >= 0:
            j = t.index(e, i)
            t = t[:i] + " " * (j - i) + t[j:]
    for m in list(re.finditer(r"_exportReviewModal\(\{", t)):
        j = t.find("addRow:", m.start())
        k = t.find("\n      ],", m.start())
        b = t.find("build:", j) if 0 < j - m.start() < 6000 else -1
        ende = max(j, k, b)
        if 0 < ende - m.start() < 6000:
            t = t[:m.start()] + " " * (ende - m.start()) + t[ende:]
    return t


def sichtbare_emojis(teil):
    t = _ohne_tabu(_ohne_kommentare(teil))
    treffer = []
    for m in EMOJI.finditer(t):
        z = m.group(0)
        if z in REST_ZEICHEN or z == "️" and t[m.start() - 1:m.start()] in REST_ZEICHEN:
            continue
        zs = t.rfind("\n", 0, m.start()) + 1
        if REST_KONTEXT.search(t[max(zs, m.start() - 220):m.start()]):
            continue
        if z == "⬆" and "Tippen Sie auf" in t[max(zs, m.start() - 160):m.start()]:
            continue
        treffer.append(t[max(zs, m.start() - 60):m.start() + 20])
    return treffer


def test_kein_sichtbares_emoji_in_den_zehn_bereichen(index_html):
    verstoss = {}
    for name, a, e in BEREICHE:
        t = sichtbare_emojis(_schnitt(index_html, a, e))
        if t:
            verstoss[name] = t[:5]
    assert not verstoss, "Sichtbare Emojis: %r" % verstoss


def test_restmenge_bleibt_begrenzt(index_html):
    """Die Restmenge ist begruendet, aber nicht frei: waechst sie, ist ein
    neues Emoji in einen Toast oder Status geraten - dann bewusst nachziehen."""
    gesamt = 0
    for name, a, e in BEREICHE:
        gesamt += len(EMOJI.findall(_ohne_kommentare(_schnitt(index_html, a, e))))
    assert gesamt <= 370, "Emoji-Gesamtmenge im Bereich: %d (vorher 883, gemessen 366)" % gesamt


def test_umkehrprobe_emoji_im_admin_reiter_wird_erkannt(index_html):
    teil = _schnitt(index_html, "\nfunction AdminPanel(", "\nfunction OfflineBanner(")
    assert not sichtbare_emojis(teil)
    kaputt = teil.replace('{id:"benutzer",l:"Benutzer"}', '{id:"benutzer",l:"\U0001F464 Benutzer"}', 1)
    assert kaputt != teil
    assert sichtbare_emojis(kaputt)
    # ein Emoji im Toast bleibt Restmenge - der Filter ist also nicht blind
    toast = teil.replace('{id:"benutzer",l:"Benutzer"}', '{id:"benutzer",l:"Benutzer"};window.__toast("\U0001F464 x")', 1)
    assert not sichtbare_emojis(toast)


def _ikon_schluessel(code):
    i = code.index("const IKON={")
    j = code.index("};function _ik(", i)
    return set(re.findall(r'(?:[{,]|\*/)([a-z]+):\[', code[i:j]))


def test_jede_gezeichnete_ikone_existiert(index_html):
    sch = _ikon_schluessel(index_html)
    for neu in ("tabelle", "drucker", "auto", "etikett", "klammer", "tank",
                "lineal", "torte", "ring", "linie", "balkenq"):
        assert neu in sch, "IKON: %s fehlt" % neu
    fehlt = set()
    for name, a, e in BEREICHE:
        t = _schnitt(index_html, a, e)
        for k in re.findall(r'_ik(?:Vw)?\("([a-z]+)"', t):
            if k not in sch:
                fehlt.add(k)
        for k in re.findall(r'\bik:"([a-z]+)"', t):
            if k not in sch:
                fehlt.add(k)
    for k in re.findall(r'ik:"([a-z]+)"', index_html[index_html.index("const CHART_TYPES="):][:300]):
        if k not in sch:
            fehlt.add(k)
    assert not fehlt, "Schluessel ohne Zeichnung (unsichtbarer Knopf): %s" % sorted(fehlt)


def test_ikvw_erbt_farbe_und_ist_aria_hidden(index_html):
    i = index_html.index("function _ikVw(name,txt)")
    rumpf = index_html[i:i + 400]
    assert "'aria-hidden':\"true\"" in rumpf
    assert "_ik(name,16)" in rumpf
    assert "color:" not in rumpf.split("_ik(name")[0], "_ikVw darf keine eigene Farbe setzen"


def test_leisten_ohne_emoji_und_aktiv_markengruen(index_html):
    admin = _schnitt(index_html, "const adminTabs=[", "];")
    assert not EMOJI.search(admin)
    assert '"#' not in admin, "Zierfarbe in den Admin-Reitern"
    assert 'border:"2px solid "+(adminTab===t.id?V.ac:"transparent")' in index_html
    assert "adminTab===t.id?t.c" not in index_html
    rollen = _schnitt(index_html, '["alle",...Object.keys(ROLES)].map(', "\n")
    assert "_ufr4.i" not in rollen and ".c])" not in rollen, "Rollen-Chips: Emoji oder Rollenfarbe zurueck"
    assert "userFilterRole===r?V.ac:" in rollen
    bx = _schnitt(index_html, "var BX_TABS=[", ";")
    assert not EMOJI.search(bx)
    wz = _schnitt(index_html, '[{id:"scan",', ".map(t=>")
    assert not EMOJI.search(wz) and 'ik:"kamera"' in wz
    chips = _schnitt(index_html, "{key:'alle',label:'Alle'},", "].map(chip=>")
    assert not EMOJI.search(chips)
    ct = _schnitt(index_html, "const CHART_TYPES=", ";")
    assert not EMOJI.search(ct)


def test_gewaehlter_diagrammtyp_ist_markengruen_nicht_abschnittsfarbe(index_html):
    i = index_html.index("Object.entries(CHART_TYPES).map(")
    knopf = index_html[i:i + 900]
    assert 'border:"1px solid "+(tp===k?V.ac:V.bd)' in knopf
    assert "tp===k?color" not in knopf and '"+color' not in knopf
    assert "'aria-label': v.l" in knopf


def test_avatare_sind_initialen(index_html):
    for name, a, e in BEREICHE:
        assert "\U0001F477" not in _schnitt(index_html, a, e), "Bauarbeiter-Avatar in %s" % name
    assert index_html.count("_vwAvatar(") >= 8
    i = index_html.index("function _vwAvatar(")
    rumpf = index_html[i:i + 500]
    assert 'borderRadius:"50%"' in rumpf and "UI.neutralBg" in rumpf


def test_login_heute_zaehlt_was_es_sagt(index_html):
    assert 'label: "Online heute"' not in index_html, "die Kachel verspricht wieder Anwesenheit"
    i = index_html.index('label: "Login heute"')
    kachel = index_html[i:i + 600]
    assert "_vwLoginHeute(users)" in kachel and "title:" in kachel
    j = index_html.index("function _vwLoginHeute(users)")
    rumpf = index_html[j:j + 400]
    assert "wert:null" in rumpf, "nicht lesbar muss als — erscheinen, nicht als 0"
    assert "td2()" in rumpf
    assert "lastLogin:_vwTagLokal(u.lastLogin||u.last_login)" in index_html, (
        "Ladeabbild schneidet last_login wieder als UTC-Datum ab")
    k = index_html.index("function _vwTagLokal(v)")
    assert "_ymd(d)" in index_html[k:k + 300]


def test_umkehrprobe_alte_kachel_faellt_auf(index_html):
    kaputt = index_html.replace('label: "Login heute"', 'label: "Online heute"', 1)
    try:
        test_login_heute_zaehlt_was_es_sagt(kaputt)
    except (AssertionError, ValueError):
        return
    raise AssertionError("Umkehrprobe: Riegel schlaegt nicht an")


def test_labels_kaestchen_ist_sichtbar(index_html):
    i = index_html.index('"Labels inkl. stillgelegter/verlorener"')
    block = index_html[i - 2500:i]
    assert 'WebkitAppearance:"auto",appearance:"auto"' in block, (
        "das Kaestchen erbt wieder appearance:none aus GCSS und zeichnet nichts")
    assert "#d97706" not in block
