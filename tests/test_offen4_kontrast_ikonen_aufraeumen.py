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
    banner = src[a:src.index("\nfunction TimerBanner(", a)]
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


# ── 4 Ticket-Fotos aufraeumen ──────────────────────────────────────────────
NAMEN = ("_tkFotoPfadOk", "_tkFotoPfadeWeg", "_tkWegListe", "_tkWegSetzen")
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
const LS={};const localStorage={getItem:k=>(k in LS?LS[k]:null),setItem:(k,v)=>{LS[k]=String(v);},removeItem:k=>{delete LS[k];}};
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
r.weg=_tkFotoPfadeWeg([A,B,"data:alt",{name:"c",dataUrl:"data:x"}],[B]);
r.fremd=_tkFotoPfadeWeg([{path:"photos/p1/x.jpg"},{path:"tickets/../plans/x.pdf"},{path:"tickets/p1/t1"},{path:"plans/tickets/p1/t1/x.jpg"}],[]);
Q=[{id:"q1",nurStorage:true,storagePath:"tickets/p1/t1/1_0.jpg"},{id:"q2",nurStorage:false,storagePath:"tickets/p1/t1/1_0.jpg"},{id:"q3",nurStorage:true,storagePath:"tickets/p1/t2/9_0.jpg"}];
r.a1=await _tkFotoAufraeumen(r.weg);
r.q=Q.map(x=>x.id);r.del1=geloescht.slice();
Q=[{id:"q4",nurStorage:true,storagePath:"tickets/p1/t1/1_1.jpg",file_path:"https://x/epkolar-files/tickets/p1/t1/1_1.jpg"}];
storageOk=false;r.a2=await _tkFotoAufraeumen(["tickets/p1/t1/1_1.jpg","photos/p1/x.jpg"]);
r.merk=JSON.parse(LS[_TK_WEG_KEY]||"[]");
for(let i=0;i<6;i++)await _tkFotoWegNachholen();
r.nachAufgeben=LS[_TK_WEG_KEY]||"";
storageOk=false;await _tkFotoAufraeumen(["tickets/p9/t9/5_0.jpg"]);storageOk=true;r.nach=await _tkFotoWegNachholen();r.leer=LS[_TK_WEG_KEY]||"";
r.del=geloescht.slice();
process.stdout.write(JSON.stringify(r));
"""


def pruef_aufraeumen(r):
    b = []
    if r["weg"] != ["tickets/p1/t1/1_0.jpg"]:
        b.append("Differenz falsch: %s" % r["weg"])
    if r["fremd"]:
        b.append("fremde/kaputte Pfade durchgelassen: %s" % r["fremd"])
    if "q1" in r["q"]:
        b.append("noch nicht hochgeladenes Ticket-Foto blieb in der PhotoQ (wuerde spaeter als Waise hochgeladen)")
    if "q2" not in r["q"] or "q3" not in r["q"]:
        b.append("fremde PhotoQ-Eintraege entfernt: %s" % r["q"])
    if r["del1"]:
        b.append("nie hochgeladenes Objekt trotzdem per DELETE angefragt: %s" % r["del1"])
    if r["a2"]["offen"] != 1 or [x["p"] for x in r["merk"]] != ["tickets/p1/t1/1_1.jpg"]:
        b.append("gescheiterter DELETE nicht gemerkt: %s / %s" % (r["a2"], r["merk"]))
    if any("photos/" in d for d in r["del"]):
        b.append("anderes Praefix geloescht: %s" % r["del"])
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
    ("/^tickets\\/[A-Za-z0-9._-]+\\/[A-Za-z0-9._-]+\\/[A-Za-z0-9._-]+$/", "/^[A-Za-z0-9._\\/-]+$/"),
    ("else offen.push({p:p,n:1});", ""),
    ("else if((x.n||0)+1<5)rest.push", "else rest.push"),
])
def test_aufraeumen_umkehrprobe(index_html, node_exe, ersetzen):
    r = _lauf(node_exe, _bausatz(index_html, ersetzen), KOERPER)
    assert pruef_aufraeumen(r), "Riegel blind fuer: " + ersetzen[0]


def test_aufraeumen_verdrahtet(index_html):
    """Beide Entfernen-Wege und beide Loesch-Wege rufen den Aufraeumer; PhotoQ holt Gemerktes nach."""
    assert index_html.count("_tkFotoAufraeumen(_tkFotoPfadeWeg([ph],[]))") == 2
    assert index_html.count("_tkFotoAufraeumen(_tkFotoPfadeWeg(_tDel.photos,[]))") == 2
    a = index_html.index("const PhotoQ={")
    assert "_tkFotoWegNachholen()" in index_html[a:index_html.index("// GPS-Erfassung", a)]
