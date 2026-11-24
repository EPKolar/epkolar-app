# -*- coding: utf-8 -*-
"""Offen-4 (17.11.2026) - je Punkt ein Riegel MIT Umkehrprobe.

  2 Startanzeige dunkel: jede Schrift >= 4,5:1 auf #0f1117 (Rueckfallwerte der var()),
    weisse Knopfschrift >= 4,5:1 auf dem Knopfgrund (dunkel UND hell).
  3 Emoji-Rest: globale Sync-Leiste, Foto-Warteschlange im Kopf, Gewerk-Zeichen im
    Warenkorb, Prioritaetsknoepfe der Material-Anforderung -> Linien-Ikonen.
    Ausgenommen: Toasts und das Schliess-/Verwerfen-Kreuz (pinnt test_hotfix_sync_v3131 /
    test_dialogknoepfe_v976).
  4 Ticket-Fotos: Entfernen/Loeschen raeumt das Storage-Objekt auf - nur tickets/,
    vorher aus der PhotoQ, Fehlschlag wird gemerkt und nachgeholt (Node, echte Funktionen).
"""
import json
import re

import pytest

from conftest import run_node_snippet, _extract_fn
from test_ui_folge_plaene import _kontrast

DUNKEL_BG = "#0f1117"


# ── 2 Startanzeige dunkel ──────────────────────────────────────────────────
def pruef_boot_dunkel(src):
    b = []
    a = src.index('<div id="ep-boot-indicator"')
    boot = src[a:src.index("},8000);", a)]
    kopf = src[:a]
    m = re.search(r':root\[data-epk-thema="hell"\]\{([^}]*)\}</style>\s*$', kopf)
    hell = dict(re.findall(r"(--epk-boot-[a-z0-9]+):(#[0-9A-Fa-f]{6})", m.group(1))) if m else {}
    def voll(h):
        h = h.lstrip("#")
        return "#" + ("".join(c * 2 for c in h) if len(h) == 3 else h)
    schrift = re.findall(r"(?<![-a-z])color:var\((--epk-boot-[a-z0-9]+),(#[0-9a-fA-F]{3,6})\)", boot)
    if len(schrift) < 8:
        b.append("zu wenige Schriftfarben gefunden (%d) - Schnitt kaputt" % len(schrift))
    for var, fb in schrift:
        k = _kontrast(voll(fb), DUNKEL_BG)
        if k < 4.5:
            b.append("dunkel: %s Rueckfall %s nur %.2f:1" % (var, fb, k))
    knoepfe = re.findall(r"background:var\((--epk-boot-[a-z0-9]+),(#[0-9a-fA-F]{3,6})\);color:#fff", boot)
    if len(knoepfe) != 2:
        b.append("Knopfgruende: %d statt 2" % len(knoepfe))
    for var, fb in knoepfe:
        if _kontrast("#FFFFFF", voll(fb)) < 4.5:
            b.append("dunkel: weiss auf %s (%s) < 4,5:1" % (var, fb))
        hw = hell.get(var)
        if not hw or _kontrast("#FFFFFF", hw) < 4.5:
            b.append("hell: weiss auf %s (%s) < 4,5:1" % (var, hw))
    if "border-top-color:var(--epk-boot-orange,#f97316)" not in boot:
        b.append("Ladekreis verlor sein Orange")
    return b


def test_boot_dunkel_kontrast(index_html):
    assert pruef_boot_dunkel(index_html) == []


@pytest.mark.parametrize("alt,neu", [
    ("color:var(--epk-boot-dm,#a1a1aa)", "color:var(--epk-boot-dm,#71717a)"),
    ("color:var(--epk-boot-klein,#a1a1aa)", "color:var(--epk-boot-klein,#555)"),
    ("background:var(--epk-boot-knopf,#c2410c);color:#fff", "background:var(--epk-boot-orange,#f97316);color:#fff"),
    (";--epk-boot-knopf:#9A3412}", "}"),
])
def test_boot_dunkel_umkehrprobe(index_html, alt, neu):
    assert alt in index_html, alt
    assert pruef_boot_dunkel(index_html.replace(alt, neu, 1)), "Riegel blind fuer: " + alt


# ── 3 Emoji-Rest ───────────────────────────────────────────────────────────
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF\uFE0F]")
ERLAUBT = {"\u2715"}  # Schliess-/Verwerfen-Kreuz (von zwei Bestandsriegeln gepinnt)


def _ohne_kommentare_toasts(t):
    t = re.sub(r"/\*.*?\*/", " ", t, flags=re.S)
    return re.sub(r"__toast[^;\n]*", " ", t)


def _teile(src):
    a = src.index("function OfflineBanner(")
    # v3.9.1111: TimerBanner entfernt (GF 24.11.) - Ende jetzt am naechsten Abschnitt; vorher "\nfunction TimerBanner("
    banner = src[a:src.index("\n// ═══════════ HOME DASHBOARD", a)]
    p = src.index("showPhotoQ&&(React.createElement('div'")
    photoq = src[p:src.index("/* ═══ SYNC DETAIL PANEL ═══ */", p)]
    w = src.index("const mc=MATERIAL_CATS[kat.gewerk]")
    gewerk = src[w:src.index("\n", src.index("React.createElement('span', { style: {display:\"inline-flex\",flexShrink:0}}, _matIk(\"kat\"", w))]
    r = src.index("Object.entries(MAT_PRIO).map(([k,v])=>")
    prio = src[r:src.index("\n", r)]
    return {"Sync-Leiste": banner, "Foto-Warteschlange": photoq, "Gewerk": gewerk, "Prioritaet": prio}


def pruef_emoji(src):
    b = []
    for name, t in _teile(src).items():
        rest = [c for c in EMOJI.findall(_ohne_kommentare_toasts(t)) if c not in ERLAUBT]
        if rest:
            b.append("%s: %s" % (name, "".join(sorted(set(rest)))))
    t = _teile(src)
    # die Daten (MATERIAL_CATS/MAT_PRIO .i) tragen das Emoji - der Datenweg zaehlt mit
    if re.search(r"\bv\.i\b", t["Prioritaet"]) or re.search(r"\bmc\.i\b", t["Gewerk"]):
        b.append("Emoji aus den Daten (.i) gezeichnet")
    return b


def test_emoji_rest_weg(index_html):
    assert pruef_emoji(index_html) == []


@pytest.mark.parametrize("alt,neu", [
    ('_zpIk("drehen","Jetzt sync",14)', '"\U0001F504 Jetzt sync"'),
    ('(pendingCount+" Änderung"+(pendingCount!==1?"en":"")+" warten auf Sync")', '("\U0001F4E4 "+pendingCount+" Änderung"+(pendingCount!==1?"en":"")+" warten auf Sync")'),
    ('ph.gpsLat?_zpIk("standort","Standort",12):null', 'ph.gpsLat?"\U0001F4CD":null'),
    ('_zpIk("uhr","Warte auf Upload",12)', '"\u23F3 Warte auf Upload"'),
    ('_matIk("prio",k), _MAT_IK.prio[k]?" ":"", v.l', 'v.i, " ", v.l'),
])
def test_emoji_umkehrprobe(index_html, alt, neu):
    assert alt in index_html, alt
    kaputt = index_html.replace(alt, neu, 1)
    assert pruef_emoji(kaputt), "Riegel blind fuer: " + alt


def test_neue_ikonen_existieren(index_html):
    for n in ("wlan_aus", "hochladen"):
        assert re.search(r"Object\.assign\(IKON,\{[^;]*\b%s:\[" % n, index_html), n
    for n in ("drehen", "kamera", "standort", "uhr", "warnung", "eimer"):
        assert re.search(r"[{,]%s:\[" % n, index_html), n


# ── 4 Ticket-Fotos aufraeumen (mit Sicherheits-Nachzug: an Projekt+Ticket gebunden, Nachholliste je Benutzer)
NAMEN = ("_tkPfadTeil", "_tkFotoPraefix", "_tkFotoPfadOk", "_tkFotoPfadeWeg", "_tkAktUid", "_tkWegListe", "_tkWegSetzen")
ASYNC = ("_tkFotoAufraeumen", "_tkFotoWegNachholen")


def _bausatz(src, ersetzen=None):
    teile = []
    for n in NAMEN:
        f = _extract_fn(src, n)
        assert f, n
        teile.append(f)
    for n in ASYNC:
        f = _extract_fn(src, n)
        assert f, n
        teile.append("async " + f)
    code = "\n".join(teile)
    if ersetzen:
        alt, neu = ersetzen
        assert alt in code, "Umkehrprobe greift ins Leere: " + alt
        code = code.replace(alt, neu)
    return code


VORSPANN = r"""
const LS={epkolar_user:JSON.stringify({id:"u1"})};const localStorage={getItem:k=>(k in LS?LS[k]:null),setItem:(k,v)=>{LS[k]=String(v);},removeItem:k=>{delete LS[k];}};
const navigator={onLine:true};
const SB_BUCKET="epkolar-files";const _TK_WEG_KEY="epk_tk_foto_weg";
let Q=[];const geloescht=[];let storageOk=true;
const PhotoQ={getAll:async()=>Q.slice(),remove:async id=>{Q=Q.filter(x=>x.id!==id);}};
async function _sbDeleteObj(b,p){geloescht.push(b+"|"+p);return storageOk;}
"""


def _lauf(node_exe, code, koerper):
    return json.loads(run_node_snippet(node_exe, VORSPANN + code + "\n(async()=>{" + koerper + "})();"))


KOERPER = r"""
const r={};
const A={name:"a",path:"tickets/p1/t1/1_0.jpg",thumb:"x"},B={name:"b",path:"tickets/p1/t1/1_1.jpg",thumb:"x"};
r.weg=_tkFotoPfadeWeg([A,B,"data:alt",{name:"c",dataUrl:"data:x"}],[B],"p1","t1",[]);
/* IDOR: fremde Pfade im lokalen Ticket-Objekt (anderes Ticket, anderes Projekt, anderes Praefix, ..) */
r.fremd=_tkFotoPfadeWeg([{path:"tickets/p1/t2/1_0.jpg"},{path:"tickets/p2/t1/1_0.jpg"},{path:"photos/p1/x.jpg"},{path:"tickets/p1/t1/../t2/x.jpg"},{path:"tickets/p1/t1/.."},{path:"tickets/p1/t1/a/b.jpg"},{path:"plans/tickets/p1/t1/x.jpg"}],[],"p1","t1",[]);
r.ohneKontext=_tkFotoPfadeWeg([A],[],"","t1",[]).concat(_tkFotoPfadeWeg([A],[],"p1","",[]));
/* ein anderes Ticket im Plan verweist noch auf A */
r.geteilt=_tkFotoPfadeWeg([A,B],[],"p1","t1",[{id:"t1",photos:[A,B]},{id:"t7",photos:[A]}]);
r.sonderzeichen=_tkFotoPfadeWeg([{path:"tickets/P_1/T_1/5_0.jpg"}],[],"P/1","T 1",[]);
/* Aufraeumer prueft selbst noch einmal gegen Projekt+Ticket */
r.direkt=await _tkFotoAufraeumen(["tickets/p1/t2/1_0.jpg","photos/p1/x.jpg"],"p1","t1");r.delDirekt=geloescht.slice();
Q=[{id:"q1",nurStorage:true,storagePath:"tickets/p1/t1/1_0.jpg"},{id:"q2",nurStorage:false,storagePath:"tickets/p1/t1/1_0.jpg"},{id:"q3",nurStorage:true,storagePath:"tickets/p1/t2/9_0.jpg"}];
r.a1=await _tkFotoAufraeumen(r.weg,"p1","t1");
r.q=Q.map(x=>x.id);r.del1=geloescht.slice();
Q=[{id:"q4",nurStorage:true,storagePath:"tickets/p1/t1/1_1.jpg",file_path:"https://x/epkolar-files/tickets/p1/t1/1_1.jpg"}];
storageOk=false;r.a2=await _tkFotoAufraeumen(["tickets/p1/t1/1_1.jpg"],"p1","t1");
r.merk=JSON.parse(LS[_TK_WEG_KEY]||"[]");
/* anderer Benutzer am selben Geraet: Eintrag von u1 wird NICHT nachgeholt */
storageOk=true;LS.epkolar_user=JSON.stringify({id:"u2"});const vorU2=geloescht.length;r.u2=await _tkFotoWegNachholen();r.u2Del=geloescht.length-vorU2;r.u2Liste=JSON.parse(LS[_TK_WEG_KEY]||"[]").length;
/* niemand angemeldet: nichts */
delete LS.epkolar_user;const vorOhne=geloescht.length;r.ohneUser=await _tkFotoWegNachholen();r.ohneUserDel=geloescht.length-vorOhne;
/* manipulierter Eintrag (fremder Pfad unter eigenem Benutzer) wird verworfen */
LS.epkolar_user=JSON.stringify({id:"u1"});
LS[_TK_WEG_KEY]=JSON.stringify([{p:"tickets/p1/t2/1_0.jpg",n:1,u:"u1",pid:"p1",tid:"t1"},{p:"tickets/p1/t1/1_1.jpg",n:1,u:"u1",pid:"p1",tid:"t1"}]);
storageOk=false;for(let i=0;i<6;i++)await _tkFotoWegNachholen();
r.nachAufgeben=LS[_TK_WEG_KEY]||"";
storageOk=false;await _tkFotoAufraeumen(["tickets/p9/t9/5_0.jpg"],"p9","t9");storageOk=true;r.nach=await _tkFotoWegNachholen();r.leer=LS[_TK_WEG_KEY]||"";
r.del=geloescht.slice();
process.stdout.write(JSON.stringify(r));
"""


def pruef_aufraeumen(r):
    b = []
    if r["weg"] != ["tickets/p1/t1/1_0.jpg"]:
        b.append("Differenz falsch: %s" % r["weg"])
    if r["fremd"]:
        b.append("fremde Pfade (anderes Ticket/Projekt/Praefix) durchgelassen: %s" % r["fremd"])
    if r["ohneKontext"]:
        b.append("ohne Projekt/Ticket wird geloescht: %s" % r["ohneKontext"])
    if r["geteilt"] != ["tickets/p1/t1/1_1.jpg"]:
        b.append("Pfad, auf den ein anderes Ticket verweist, wird geloescht: %s" % r["geteilt"])
    if r["sonderzeichen"] != ["tickets/P_1/T_1/5_0.jpg"]:
        b.append("Praefix-Bausteine weichen von _tkFotosAuslagern ab: %s" % r["sonderzeichen"])
    if r["delDirekt"] or r["direkt"]["offen"]:
        b.append("Aufraeumer loescht fremde Pfade: %s" % r["delDirekt"])
    if "q1" in r["q"]:
        b.append("noch nicht hochgeladenes Ticket-Foto blieb in der PhotoQ (wuerde spaeter als Waise hochgeladen)")
    if "q2" not in r["q"] or "q3" not in r["q"]:
        b.append("fremde PhotoQ-Eintraege entfernt: %s" % r["q"])
    if r["del1"]:
        b.append("nie hochgeladenes Objekt trotzdem per DELETE angefragt: %s" % r["del1"])
    merk = [(x["p"], x.get("u"), x.get("pid"), x.get("tid")) for x in r["merk"]]
    if r["a2"]["offen"] != 1 or merk != [("tickets/p1/t1/1_1.jpg", "u1", "p1", "t1")]:
        b.append("gescheiterter DELETE nicht mit Benutzer/Projekt/Ticket gemerkt: %s / %s" % (r["a2"], r["merk"]))
    if r["u2"] or r["u2Del"] or r["u2Liste"] != 1:
        b.append("Nachholliste unter fremdem Benutzer abgespielt/verworfen: %s/%s/%s" % (r["u2"], r["u2Del"], r["u2Liste"]))
    if r["ohneUser"] or r["ohneUserDel"]:
        b.append("ohne Anmeldung nachgeholt")
    if any("photos/" in d or "/t2/" in d for d in r["del"]):
        b.append("fremdes Objekt geloescht: %s" % r["del"])
    if r["nachAufgeben"]:
        b.append("Merkliste waechst ohne Grenze: %s" % r["nachAufgeben"])
    if r["nach"] != 1 or r["leer"]:
        b.append("Nachholen raeumt nicht: %s / %s" % (r["nach"], r["leer"]))
    return b


def test_aufraeumen_node(index_html, node_exe):
    r = _lauf(node_exe, _bausatz(index_html), KOERPER)
    assert pruef_aufraeumen(r) == []


@pytest.mark.parametrize("ersetzen", [
    ("if(x&&x.nurStorage&&liste.indexOf(x.storagePath)>=0){await PhotoQ.remove(x.id);", "if(false){"),
    ("p.indexOf(\"..\")<0&&", ""),
    ("&&p.indexOf(pre)===0&&/^[A-Za-z0-9._-]+$/.test(p.slice(pre.length))", "&&/^tickets\\//.test(p)"),
    ("if(!t||t.id===tid)return;", "return;"),
    ("filter(p=>_tkFotoPfadOk(p,pid,tid))", "filter(p=>!!p)"),
    ("else if(uid)offen.push({p:p,n:1,u:uid,pid:String(pid),tid:String(tid)});", ""),
    ("if(x.u!==uid){rest.push(x);continue;}", ""),
    ("const uid=_tkAktUid();if(!uid)return 0;", "const uid=\"u1\";"),
    ("else if((x.n||0)+1<5)rest.push", "else rest.push"),
    ("return String(v||\"x\").replace(/[^a-zA-Z0-9._-]/g,\"_\").slice(0,80);", "return String(v||\"x\");"),
])
def test_aufraeumen_umkehrprobe(index_html, node_exe, ersetzen):
    try:
        befunde = pruef_aufraeumen(_lauf(node_exe, _bausatz(index_html, ersetzen), KOERPER))
    except Exception as ex:
        befunde = [str(ex)[:200]]
    assert befunde, "Riegel blind fuer: " + ersetzen[0]


def test_pfadbausteine_wortgleich(index_html):
    """_tkPfadTeil ist zeichengleich mit dem Baustein _s, mit dem _tkFotosAuslagern den Pfad baut."""
    teil = re.search(r"function _tkPfadTeil\(v\)\{return (.*?);\}", index_html).group(1)
    aus = _extract_fn(index_html, "_tkFotosAuslagern")
    assert "const _s=v=>" + teil + ";" in aus
    assert '"tickets/"+_s(pid)+"/"+_s(tid)+"/"' in aus


def test_aufraeumen_verdrahtet(index_html):
    """Entfernen (Detail, Schnellblatt) und Loeschen (Plan, Maengel) laufen ueber den gebundenen Weg; Abmelden leert die Liste."""
    assert "_tkFotoPfadeWeg([ph],[]))" not in index_html
    assert index_html.count("_tkFotoAufraeumen(_tkFotoPfadeWeg(alt,neu,p.id,t.id,(planData&&planData.tickets)||[]),p.id,t.id)") == 1
    assert index_html.count("onFotoWeg: _vpFotoWeg}") == 2
    assert "if(onFotoWeg)onFotoWeg(ticket,[ph],[]);" in index_html
    assert "onPhotos: (arr)=>{_vpFotoWeg(quickTicket,quickTicket&&quickTicket.photos,arr);" in index_html
    assert "if(_tDel)_vpFotoWeg(_tDel,_tDel.photos,[]);" in index_html
    assert "_tkFotoAufraeumen(_tkFotoPfadeWeg(_tDel.photos,[],p.id,_tDel.id,planData.tickets),p.id,_tDel.id)" in index_html
    a = index_html.index("function setToken(t)")
    assert "localStorage.removeItem('epk_tk_foto_weg')" in index_html[a:index_html.index("function getToken", a)]
    a = index_html.index("const PhotoQ={")
    assert "_tkFotoWegNachholen()" in index_html[a:index_html.index("// GPS-Erfassung", a)]
