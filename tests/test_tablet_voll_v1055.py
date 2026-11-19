"""v1055 Tablet-Vollpruefung 19.11.2026 (Lenovo TB328XU, hoch + quer, v3.9.1052).

Die Rechner laufen in Node mit dem ECHTEN Code aus index.html (keine Abschrift). Zu jedem Riegel
gibt es eine Umkehrprobe: der Rueckbau (oder die alte Regel) muss den Test rot machen.

 1  Flotte: Info-Karte hoeher als die Karte (quer ~270 px) -> Blatt bei niedriger Karte, Popup mit
    Hoechsthoehe + einmaliges Verschieben, GPS-Badge nicht ueber der offenen Karte.
 2  Glocke: alte Ausfall-Meldungen (rls_frist / rls_material) werden nach einer gelesenen Runde gelesen.
 3  Glocke: Neue Abwesenheit ... Urlaub, obwohl der Tag inzwischen Krankenstand ist -> Hinweis mit echtem
    Typ; 8.5h -> 8,5 h.
 4  Dispo: fixer Schein an einem Abwesenheitstag -> Warnzeile an der Kachel.
 5  Home: Pickerl nach derselben Toleranzregel wie Fahrzeuge/Fristen.
 6  Fahrzeug: Letztes Service zaehlt nur Service/Inspektion, keinen Reifenwechsel.
 7  Auswertungen: Wertbeschriftung neben dem Balken wird nicht mehr abgeschnitten.
 8  Team-Timeline: kein Wortbruch im Namen.
 9  Plaene: Lade-Hinweis verschwindet, sobald diese Seite gezeichnet ist.
10  Material: 416 hinter der letzten Seite = Ende der Liste, kein Verbindungsfehler.
11  Emoji -> Linien-Ikonen (Mitarbeiter-Detail, Planung-Wetter, Buero-Portal).
"""
import json
import re

import pytest

from conftest import run_node_snippet, _extract_fn


def _fns(src, *names):
    out = []
    for n in names:
        f = _extract_fn(src, n)
        assert f, n + " nicht gefunden"
        out.append(f)
    return "\n".join(out) + "\n"


def _const_obj(src, name):
    i = src.index("const " + name + "={")
    j = src.index("{", i)
    d = 0
    for k in range(j, len(src)):
        if src[k] == "{":
            d += 1
        elif src[k] == "}":
            d -= 1
            if d == 0:
                return src[i:k + 1] + ";\n"
    raise AssertionError(name)


def _times(src):
    z = re.findall(r"^const TIME_\w+=[^;\n]+;", src, re.M)
    assert len(z) >= 4
    return "\n".join(z) + "\n"


def _run(node_exe, code, expr):
    return json.loads(run_node_snippet(node_exe, code + "\nprocess.stdout.write(JSON.stringify(" + expr + "));"))


# ── 1 Flotte ─────────────────────────────────────────────────────────────────

def _flotte(src):
    m = re.search(r"var FZ_POPUP_MIN_KARTE_H=\d+;", src)
    assert m
    return m.group(0) + "\n" + _fns(src, "_fzInfoModus", "_fzPopupMaxH", "_fzPopupPan")


def test_flotte_niedrige_karte_bekommt_das_blatt(index_html, node_exe):
    r = _run(node_exe, _flotte(index_html),
             "[_fzInfoModus(false,true,270),_fzInfoModus(false,true,600),_fzInfoModus(true,true,800),"
             "_fzInfoModus(false,false,600),_fzInfoModus(false,true,0)]")
    assert r == ["sheet", "popup", "sheet", "overlay", "popup"]


def test_flotte_popup_passt_in_die_karte(index_html, node_exe):
    r = _run(node_exe, _flotte(index_html),
             "[_fzPopupMaxH(490),_fzPopupMaxH(200),_fzPopupPan(330,120,300,380,660,490),_fzPopupPan(330,460,300,300,660,490),"
             "_fzPopupPan(40,400,300,200,660,490),_fzPopupPan(NaN,1,1,1,1,1)]")
    assert r[0] == 394 and r[1] == 160
    # Marker oben (y 120), Popup 380 hoch: muss um 288 px nach unten (380+28 = 408)
    assert r[2] == {"dx": 0, "dy": 288}
    assert r[3] == {"dx": 0, "dy": 0}
    assert r[4]["dx"] == 120 and r[4]["dy"] == 0
    assert r[5] == {"dx": 0, "dy": 0}


def test_flotte_umkehrprobe_alte_regel_ohne_hoehe(index_html, node_exe):
    kaputt = index_html.replace("if(isFinite(hh)&&hh>0&&hh<FZ_POPUP_MIN_KARTE_H)return 'sheet';", "", 1)
    assert kaputt != index_html
    r = _run(node_exe, _flotte(kaputt), "_fzInfoModus(false,true,270)")
    assert r == "popup", "Umkehrprobe: ohne Hoehenregel kaeme quer wieder das zu hohe Popup"


def test_flotte_verdrahtung(index_html):
    assert "const _infoModus=!_selRow?'':_fzInfoModus(isMob,_selPosOk,_kartenH);" in index_html
    assert "_popRef.current.options.maxHeight=_fzPopupMaxH(map.getSize().y);" in index_html
    assert "map.panBy([-d.dx,-d.dy])" in index_html
    assert "(st.loaded&&!showEmpty&&fahrzeuge.length&&!_infoModus)?h('div',{'aria-live':'polite'" in index_html
    # autoPan bleibt aus (sonst liefe die Karte bei jedem Poll unter dem Finger weg)
    assert "L.popup({closeButton:false,autoPan:false," in index_html


# ── 2 Glocke: Ausfall-Meldungen ──────────────────────────────────────────────

def _esk(src):
    return ("var ESK_AUSFALL_TITEL=" + re.search(r"var ESK_AUSFALL_TITEL=(\{[^}]*\});", src).group(1) + ";\n"
            "var ESK_AUSFALL_TYP=" + re.search(r"var ESK_AUSFALL_TYP=(\{[^}]*\});", src).group(1) + ";\n"
            + _fns(src, "_notifKeyId", "_eskAusfallErledigtIds"))


def _djb2(s):
    h = 5381
    for ch in s:
        h = ((h << 5) + h + ord(ch)) & 0xFFFFFFFF
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    out = ""
    while h:
        out = digits[h % 36] + out
        h //= 36
    return out or "0"


def test_glocke_id_wie_pushNotif(index_html, node_exe):
    # dieselbe Formel wie pushNotif (dedupKey -> djb2 von k:key)
    assert '_idHash=dedupKey?_ndKey("k:"+String(dedupKey))' in index_html
    assert 'id:"n_"+tuid+"_"+type+"_"+_idHash' in index_html
    r = _run(node_exe, _esk(index_html), '_notifKeyId("u1","ticket_eskalation","rls_frist")')
    assert r == "n_u1_ticket_eskalation_" + _djb2("k:rls_frist")


def test_glocke_alte_ausfall_meldung_wird_erledigt(index_html, node_exe):
    liste = [
        {"id": "x1", "type": "ticket_eskalation", "title": "Fristenprüfung unvollständig", "read": False, "user": "u1"},
        {"id": "x2", "type": "material_eskalation", "title": "Material-Fristen NICHT geprüft", "read": False, "user": "u1"},
        {"id": "x3", "type": "ticket_eskalation", "title": "Fristenprüfung unvollständig", "read": False, "user": "u2"},
        {"id": "x4", "type": "ticket_eskalation", "title": "Ticket überfällig: Dach", "read": False, "user": "u1"},
        {"id": "x5", "type": "ticket_eskalation", "title": "Fristenprüfung unvollständig", "read": True, "user": "u1"},
    ]
    code = _esk(index_html) + "var L=" + json.dumps(liste, ensure_ascii=False) + ";"
    r = _run(node_exe, code,
             '[_eskAusfallErledigtIds(L,"u1","rls_frist"),_eskAusfallErledigtIds(L,"u1","rls_material"),'
             '_eskAusfallErledigtIds(L,"",""),_eskAusfallErledigtIds(L.concat([{id:_notifKeyId("u1","ticket_eskalation","rls_frist"),'
             'type:"ticket_eskalation",title:"anders",read:false,user:"u1"}]),"u1","rls_frist").length]')
    assert r[0] == ["x1"], "nur die eigene, ungelesene Ausfall-Meldung"
    assert r[1] == ["x2"]
    assert r[2] == []
    assert r[3] == 2, "auch ueber die deterministische id gefunden"


def test_glocke_verdrahtung_und_umkehrprobe(index_html):
    a = 'Offene Bestellungen werden gerade nicht überwacht.",admins);if(_mArt==="")_ausfallErledigt("rls_material");}'
    b = 'Überfällige Tickets und Mängel werden gerade NICHT gemeldet.",_pmU);if(_fArt==="")_ausfallErledigt("rls_frist");}'
    assert a in index_html and b in index_html
    assert 'fire("rls_frist",ESK_AUSFALL_TYP.rls_frist,ESK_AUSFALL_TITEL.rls_frist,' in index_html
    assert 'fire("rls_material",ESK_AUSFALL_TYP.rls_material,ESK_AUSFALL_TITEL.rls_material,' in index_html
    i = index_html.index("const _ausfallErledigt=(key)=>{")
    blk = index_html[i:i + 500]
    assert 'SQ.push({url:"/api/notifications/"+id,method:"PUT",body:{read:1}})' in blk
    assert "ODB.save(\"notifications\",upd)" in blk
    kaputt = index_html.replace('if(_fArt==="")_ausfallErledigt("rls_frist");', "", 1)
    assert b not in kaputt


# ── 3 Glocke: Abwesenheits-Meldung ───────────────────────────────────────────

def _abs(src):
    return (re.search(r"const COLORS=\{[^}]*\};", src).group(0) + "\n" + _const_obj(src, "AT_T") + _const_obj(src, "_NOTIF_TAB_DE")
            + _fns(src, "_notifAnzeige", "_absNotifStand", "_absNotifText"))


def test_abwesenheit_meldung_gegen_aktuellen_stand(index_html, node_exe):
    code = _abs(index_html) + (
        'var ABS={"Barger_2026-11-17":{type:"krankenstand"},"Barger_2026-11-02":{type:"urlaub"}};'
        'function N(b){return {type:"absence_new",body:b};}')
    r = _run(node_exe, code,
             '[_absNotifText(N("Barger: Urlaub am 17.11.2026 (8.5h)"),ABS),'
             '_absNotifText(N("Barger: Urlaub am 3.11.2026 (8.5h)"),ABS),'
             '_absNotifText(N("Barger: Urlaub am 2.11.2026 (8,5 h)"),ABS),'
             '_absNotifText(N("Barger: Urlaub am 3.11.2026 (4.5h)"),{}),'
             '_absNotifStand({type:"absence_sick",body:"Barger hat sich krankgemeldet (17.11.2026)"},ABS)]')
    assert r[0] == "Barger: Urlaub am 17.11.2026 (8,5 h) – inzwischen: Krankenstand"
    assert r[1] == "Barger: Urlaub am 3.11.2026 (8,5 h) – inzwischen gelöscht"
    assert r[2] == "Barger: Urlaub am 2.11.2026 (8,5 h)", "stimmt der Typ, kein Zusatz"
    assert r[3] == "Barger: Urlaub am 3.11.2026 (4,5 h)", "ohne geladene Abwesenheiten wird nichts behauptet"
    assert r[4] is None


def test_abwesenheit_verdrahtung(index_html):
    assert "title: _absNotifText(n,abs)}, _absNotifText(n,abs))" in index_html
    assert index_html.count('" am "+fdt(dk(d))+" ("+_absH(stdVonTag(d,_wocheOf(sel)),1)+" h)")') == 2
    assert '" am "+fdt(dk(d))+" ("+stdVonTag(d,_wocheOf(sel))+"h)"' not in index_html


# ── 4 Dispo ──────────────────────────────────────────────────────────────────

def test_dispo_abwesenheit_konflikt(index_html, node_exe):
    code = _fns(index_html, "_dispoAbwLabel", "_dispoAbwKonflikt")
    r = _run(node_exe, code,
             '[_dispoAbwKonflikt({type:"krankenstand",status:"genehmigt"}),_dispoAbwKonflikt({type:"urlaub",status:"beantragt"}),'
             '_dispoAbwKonflikt({type:"urlaub",status:"abgelehnt"}),_dispoAbwKonflikt(null),_dispoAbwKonflikt({type:"krankenstand"})]')
    assert r[0] == "Monteur abwesend: Krankenstand"
    assert r[1] == "Abwesenheit beantragt: Urlaub"
    assert r[2] is None and r[3] is None
    assert r[4] == "Monteur abwesend: Krankenstand", "ohne Status gilt genehmigt (wie _dispoAbwAbzug)"


def test_dispo_verdrahtung(index_html):
    assert 'if(ab)abwTag[m.id+"_"+t.key]={type:ab.type,status:ab.status};' in index_html
    assert "abwTag:abwTag," in index_html
    assert index_html.count('abwesend:_dispoAbwKonflikt((_built.abwTag||{})[m.id+"_"+t.key])') == 2
    assert "o.abwesend?h('div',{'data-abw-konflikt':\"1\"" in index_html
    assert '_dpIkTxt("⚠",o.abwesend)' in index_html
    # nur Anzeige: kein Schreibweg im Konflikt-Helfer
    f = _extract_fn(index_html, "_dispoAbwKonflikt")
    assert "SQ." not in f and "_sb" not in f


# ── 5 Pickerl ────────────────────────────────────────────────────────────────

def _pick(src):
    return _times(src) + _fns(src, "_fzDatumTeile", "_fzTagKey", "_fzTageBis", "_fzPickerlStufe", "_homePickerlEintrag")


NOW_1911 = "new Date(2026,10,19,12,0,0).getTime()"


def test_home_pickerl_toleranz(index_html, node_exe):
    r = _run(node_exe, _pick(index_html),
             "[_homePickerlEintrag('2026-11-10'," + NOW_1911 + "),_homePickerlEintrag('2026-06-10'," + NOW_1911 + "),"
             "_homePickerlEintrag('2026-12-01'," + NOW_1911 + "),_homePickerlEintrag('2025-01-10'," + NOW_1911 + "),"
             "_homePickerlEintrag('2027-06-01'," + NOW_1911 + ")]")
    assert r[0]["badge"] == "Toleranzfrist" and "31.3.2027" in r[0]["sub"] and r[0]["farbe"] == "orange"
    assert r[1]["badge"] == "Abgelaufen" and r[1]["farbe"] == "rot", "Toleranz endete 31.10.2026"
    assert r[2]["sub"] == "gültig bis 1.12.2026" and r[2]["urgent"] is True
    assert r[3] is None and r[4] is None


def test_home_pickerl_umkehrprobe_alte_regel(index_html):
    alt = 'sub:(diff<0?"abgelaufen seit ":"gültig bis ")+fdt(f.pickerl),badge:diff<0?"Abgelaufen":_inTagen(diff)'
    assert alt not in index_html, "Home rechnet wieder ohne Toleranz"
    assert "const _pe=_homePickerlEintrag(f.pickerl,Date.now(),_inTagen);" in index_html


# ── 6 Letztes Service ────────────────────────────────────────────────────────

def _svc(src):
    return _fns(src, "_fzZahl", "_fzDatumTeile", "_fzServiceStats")


def test_letztes_service_ohne_reifenwechsel(index_html, node_exe):
    code = _svc(index_html) + (
        "var F={serviceheft:[{datum:'2025-04-15',art:'Service',km:100000,kosten:300},"
        "{datum:'2026-11-10',art:'Reifenwechsel',km:129453,kosten:80},{datum:'2025-01-01',km:90000}]};"
        "var G={serviceheft:[{datum:'2026-11-10',art:'Reifenwechsel',km:129453}]};")
    r = _run(node_exe, code, "[_fzServiceStats(F),_fzServiceStats(G)]")
    assert r[0]["letzte"] == "2025-04-15" and r[0]["letzteKm"] == 100000
    assert r[0]["anzahl"] == 3 and r[0]["euro"] == 380, "Anzahl und Kosten zaehlen weiter alle Eintraege"
    assert r[1]["letzte"] == ""


def test_letztes_service_umkehrprobe(index_html, node_exe):
    kaputt = index_html.replace("    if(art!==''&&art!=='service'&&art!=='inspektion')continue;\n", "", 1)
    assert kaputt != index_html
    code = _svc(kaputt) + "var G={serviceheft:[{datum:'2026-11-10',art:'Reifenwechsel',km:1}]};"
    assert _run(node_exe, code, "_fzServiceStats(G).letzte") == "2026-11-10"


# ── 7 Auswertungen ───────────────────────────────────────────────────────────

def test_hbar_wert_hat_platz(index_html, node_exe):
    code = _fns(index_html, "_hbarWertBreite")
    r = _run(node_exe, code, '[_hbarWertBreite(["€ 5.410","€ 0"],12),_hbarWertBreite(["243 848"],12),_hbarWertBreite(["3"],12)]')
    assert r[0] >= 6 + 7 * 12 * 0.62 and r[0] > 40, "vorher fest 40 - zu wenig fuer € 5.410"
    assert r[1] > 40
    assert r[2] == 40
    assert "Math.max(20,width-lw-_hbWertB)" in index_html
    assert "(width-lw-40)" not in index_html
    assert "fontWeight: 700}, _hbWerte[i])" in index_html


# ── 8 Team-Timeline ──────────────────────────────────────────────────────────

def test_team_timeline_kein_wortbruch(index_html):
    i = index_html.index('"aria-label": "Kalender für "+m+" öffnen"')
    blk = index_html[i:i + 1600]
    assert 'flexDirection:"column"' in blk
    assert "..._zweiZeilen" not in blk, "_zweiZeilen bricht mit overflowWrap anywhere mitten im Wort"
    assert 'whiteSpace:"nowrap",overflowWrap:"normal",wordBreak:"normal",hyphens:"none"' in blk


# ── 9 Plaene ─────────────────────────────────────────────────────────────────

def test_plan_ladehinweis_folgt_dem_ergebnis(index_html):
    assert "const _planFertig = !!(_isPdf && plan && pageDims && pageDims._plan === plan.id && pageDims._pg === pageNum);" in index_html
    assert "const _ladeSicht = loading && !_planFertig;" in index_html
    i = index_html.index('}, "Plan wird geladen…") : null,')
    assert "_ladeSicht ? React.createElement('div', {" in index_html[i - 300:i]
    assert index_html.count("!_ladeSicht && plan && ticketsOnPage.length > 0 ?") == 2
    # die Abmessung, gegen die geprueft wird, traegt Plan und Seite
    assert "setPageDims({...dims, _plan: plan.id, _pg: pageNum});" in index_html


# ── 10 Material ──────────────────────────────────────────────────────────────

def test_material_416_ist_listenende(index_html, node_exe):
    code = _fns(index_html, "_matSeiteEnde")
    r = _run(node_exe, code,
             '[_matSeiteEnde(new Error("HTTP416 {\\"code\\":\\"PGRST103\\"}"),5000),_matSeiteEnde(new Error("HTTP416"),0),'
             '_matSeiteEnde(new Error("HTTP500 boom"),5000),_matSeiteEnde(new TypeError("Failed to fetch"),5000),_matSeiteEnde(null,5000)]')
    assert r == [True, False, False, False, False]
    assert '.catch(_er=>_matSeiteEnde(_er,_saOff)?[]:null);' in index_html
    assert '"Noch keine DATANORM-Kataloge importiert. Standard-Platzhalter aktiv."' not in index_html
    assert '"Keine DATANORM-Datei importiert. Im Warenkorb aktiv: "+catalogs.length+" Kataloge' in index_html


def test_material_umkehrprobe(index_html, node_exe):
    kaputt = index_html.replace("return /HTTP416|PGRST103/.test(t);", "return false;", 1)
    assert kaputt != index_html
    r = _run(node_exe, _fns(kaputt, "_matSeiteEnde"), '_matSeiteEnde(new Error("HTTP416"),5000)')
    assert r is False


# ── 11 Emoji -> Linien-Ikonen ────────────────────────────────────────────────

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐]")
ERLAUBT = ("__toast", "_showToast", "_confirmModal", "genXls(", "setMsg(", "console.")


def _emoji_ohne_toasts(teil):
    teil = re.sub(r"/\*.*?\*/", "", teil, flags=re.S)
    weg = []
    for m in EMOJI.finditer(teil):
        anf = teil.rfind("\n", 0, m.start()) + 1
        vor = teil[max(anf, m.start() - 200):m.start()]
        if any(k in vor for k in ERLAUBT):
            continue
        weg.append(vor[-50:] + m.group())
    return weg


@pytest.mark.parametrize("a,e", [
    ("const KOMPETENZEN_DEFS=[", "\n// ═══"),
    ("function WorkerNfcPanel(", "\nfunction "),
    ("function FahrtenbuchPanel(", "\nfunction "),
    ('_ikVw("fieber","Atteste / Krankmeldungen")', "\nfunction "),
    ('_ikVw("auto","Fahrbewilligungen")', "\nfunction "),
    ('_ikVw("ordner","Persönliche Dokumente")', "\nfunction "),
])
def test_mitarbeiter_detail_ohne_emoji(index_html, a, e):
    if a not in index_html:
        pytest.skip("Abschnitt " + a + " nicht vorhanden")
    i = index_html.index(a)
    j = index_html.index(e, i + len(a))
    rest = [x for x in _emoji_ohne_toasts(index_html[i:j]) if not (x.endswith("✓") or x.endswith("✕"))]  # Haken/Kreuz = Schrift
    assert not rest, rest


def test_kompetenzen_ikonen_existieren(index_html):
    i = index_html.index("const KOMPETENZEN_DEFS=[")
    j = index_html.index("];", i)
    namen = re.findall(r"icon:'([a-zA-Z]+)'", index_html[i:j])
    assert len(namen) == 10
    # IKON-Grundbestand + alle Object.assign(IKON,{...})-Ergaenzungen
    k = index_html.index("const IKON={")
    teile = [index_html[k:index_html.index("};function _ik(", k)]]
    for m in re.finditer(r"Object\.assign\(IKON,\{", index_html):
        teile.append(index_html[m.start():m.start() + 20000])
    vorrat = set()
    for t in teile:
        vorrat |= set(re.findall(r"(?:[{,]|\*/)\s*([A-Za-z]+):\[", t))
    for n in namen + ["stern"]:
        assert n in vorrat, n


def test_planung_wetter_und_buero(index_html):
    assert "(w&&w.code!==null&&w.code!==undefined)?_ik(_wmoIk(w.code),28):\"\"" in index_html
    assert '(w&&w.icon)?w.icon:""' not in index_html
    assert '_ikVw("warnung",noAtt+" Mitarbeiter mit Krankenstand ohne Attest")' in index_html
    assert 'text: _ikVw("bericht",ps.regCnt+" Regie")' in index_html
    # OFFA Excel bleibt byte-gleich
    assert "📊 OFFA Excel" in index_html


# ── Minor ────────────────────────────────────────────────────────────────────

def test_minor_monat_und_einheiten(index_html, node_exe):
    code = re.search(r"const MO_DE=\[[^\]]*\];?", index_html).group(0).rstrip(";") + ";\n" + _fns(index_html, "_monatAnz")
    assert _run(node_exe, code, "[_monatAnz('2026-11'),_monatAnz('2026-01'),_monatAnz('kaputt')]") == ["November 2026", "Jänner 2026", "kaputt"]
    assert "'Keine Fahrten in '+month" not in index_html
    assert '+" MB":_n((totalSize/BYTES_KB),0)+" KB")' in index_html
    assert "Probelauf (nichts ändern)" in index_html and "Pausenlänge" in index_html
    # die Dispo-Schaetzung steht VOR der Zahl (1,5h= las sich wie ein verirrtes Gleichheitszeichen)
    assert '(o.dauerGeschaetzt?"≈":"")+((Math.round((o.dauerMin||0)/60*10)/10).toLocaleString("de-AT")+"h")' in index_html
    # erledigt kommt als 0/1 - 0&& zeichnete eine 0 neben Service
    assert ", t.erledigt&&React.createElement('span'" not in index_html


def test_minor_buero_projektstunden_summe(index_html):
    i = index_html.index('label: "Stunden auf Projekten"')
    blk = index_html[i - 1400:i]
    assert "var _hP=projStats.reduce(function(s,p){return s+(p.hrs||0);},0);" in blk
    assert "archivierte/andere Projekte" in blk


def _katalog_416_js(html, gesamt, server_max=1000):
    seiten = re.search(r"const _MAT_KAT_SEITEN=\d+;", html).group(0)
    a = html.index("const sa=[];let _saOff")
    b = html.index("setSuppLoad({n:sa.length", a)
    fn = html[html.index("function _matSeiteEnde("):html.index("\n", html.index("function _matSeiteEnde("))]
    return (seiten + fn + "\nlet a=true;const _saSel='s';"
            "globalThis.setTimeout=(f,ms)=>{f();return 0;};"
            "async function _sbGet(t,f){const off=+f.split('offset=')[1];const lim=+/limit=(\\d+)/.exec(f)[1];"
            "if(off>0&&off>=" + str(gesamt) + ")throw new Error('HTTP416 PGRST103 Requested range not satisfiable');"
            "const n=Math.max(0,Math.min(lim," + str(server_max) + "," + str(gesamt) + "-off));"
            "return Array.from({length:n},(_,i)=>({id:off+i}));}"
            "(async()=>{" + html[a:b] + "console.log(JSON.stringify({n:sa.length,f:_saFehler,g:_saGekappt}));})();")


def test_material_genau_5000_ohne_fehlalarm(index_html, node_exe):
    r = json.loads(run_node_snippet(node_exe, _katalog_416_js(index_html, 5000)))
    assert r == {"n": 5000, "f": False, "g": False}, r
    kaputt = index_html.replace(".catch(_er=>_matSeiteEnde(_er,_saOff)?[]:null);", ".catch(()=>null);", 1)
    assert kaputt != index_html
    r2 = json.loads(run_node_snippet(node_exe, _katalog_416_js(kaputt, 5000)))
    assert r2["f"] is True, "Umkehrprobe: ohne die 416-Regel kaeme wieder der Fehlalarm"
