# -*- coding: utf-8 -*-
"""v3.9.1119 Arbeitsscheine: Uhrzeit (termin_zeit) nur Admin, Buero, PL (GF 25.11.2026, Paket 3 v2).

Bestaetigung an Sebastian: "Uhrzeit: Admin, Büro, PL (vorher 'nur Admin und Büro')".
Monteur, Helfer und Techniker (alle Nicht-Staff, im ArbeitsscheinView: !isAdmin) sehen die Uhrzeit nur.
Kein Schreibweg darf termin_zeit fuer sie mitschicken - sonst lehnt der DB-Trigger trg_as_feldrollen_guard
(sql/ARBEITSSCHEINE_FELDROLLEN_v2_ENTWURF.sql) den GANZEN Diff-PUT mit 403 ab.

Gepinnt:
  1. Formular: das Uhrzeitfeld ist fuer !isAdmin gesperrt und der onChange schreibt nicht.
  2. saveAs (Diff-PUT): terminZeit/terminBestaetigt werden fuer !isAdmin auf den geladenen Stand geforct
     (dann steht im Diff nichts davon).
  3. updAs: terminZeit/terminBestaetigt werden fuer !isAdmin aus dem Update entfernt.
  4. verschieben(): Handler-Riegel !isAdmin (Knopf ist seit 1108 schon nur Staff).
  5. Im ArbeitsscheinView ist isAdmin = admin, projektleiter, buero (Techniker ist NICHT Staff).
  6. Dispo-Reiter (schreibt Termin/Uhrzeit) ist nur fuer Staff erreichbar.
"""
import io
import os
import re

HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")


def _s():
    return io.open(HTML, encoding="utf-8", newline="").read()


def _av(s=None):
    s = s if s is not None else _s()
    i = s.index("function ArbeitsscheinView(")
    return s[i:re.compile(r"\nfunction [A-Z]").search(s, i + 10).start()]


UHRZEIT_FELD = re.compile(
    r"React\.createElement\('input', \{ type: \"time\", value: _asZeitAnz\(form\.terminZeit\), "
    r"onChange: e=>\{if\(!isAdmin\)return;setForm\(p=>\(\{\.\.\.p,terminZeit:e\.target\.value\}\)\);\}, "
    r"disabled:_asMtLocked\|\|!isAdmin/\*[^*]*\*/, ")
SAVE_FORCE = re.compile(
    r"const _FELD_TERMIN=\['terminBestaetigt','terminZeit'\];/\*[^*]*\*/\s*"
    r"const _lockedKeys=\[[^;\n]*?,\.\.\.\(!isAdmin\?_FELD_TERMIN:\[\]\)\];")
UPD_RIEGEL = re.compile(
    r"if\(!isAdmin&&\(\('terminZeit'in _u\)\|\|\('terminBestaetigt'in _u\)\)\)\{delete _u\.terminZeit;delete _u\.terminBestaetigt;")
VERSCH = re.compile(r"const verschieben=\(id,d\)=>\{if\(!d\)return;if\(!isAdmin\)\{[^}]*return;\}")


def _luecken(av):
    f = []
    if len(UHRZEIT_FELD.findall(av)) != 1:
        f.append("Formular Uhrzeit")
    if len(SAVE_FORCE.findall(av)) != 1:
        f.append("saveAs Diff-PUT")
    if len(UPD_RIEGEL.findall(av)) != 1:
        f.append("updAs")
    if len(VERSCH.findall(av)) != 1:
        f.append("verschieben")
    return f


def test_uhrzeit_fuer_feldrollen_gesperrt():
    assert _luecken(_av()) == []


def test_umkehrprobe_altstand_waere_rot():
    av = _av()
    alt = av.replace("onChange: e=>{if(!isAdmin)return;setForm(p=>({...p,terminZeit:e.target.value}));}, disabled:_asMtLocked||!isAdmin",
                     "onChange: e=>setForm(p=>({...p,terminZeit:e.target.value})), disabled:_asMtLocked")
    alt = alt.replace(",...(!isAdmin?_FELD_TERMIN:[])]", "]")
    alt = alt.replace("if(!isAdmin&&(('terminZeit'in _u)", "if(false&&(('terminZeit'in _u)")
    alt = re.sub(r"(const verschieben=\(id,d\)=>\{if\(!d\)return;)if\(!isAdmin\)\{[^}]*return;\}", r"\1", alt)
    assert alt != av
    assert set(_luecken(alt)) == {"Formular Uhrzeit", "saveAs Diff-PUT", "updAs", "verschieben"}


def test_isadmin_im_arbeitsschein_ist_genau_staff():
    av = _av()
    m = re.search(r"\n  const isAdmin=([^;]*);", av)
    assert m and m.group(1) == 'curUser.role==="admin"||curUser.role==="projektleiter"||curUser.role==="buero"'
    assert "techniker" not in m.group(1)


def test_genau_ein_uhrzeitfeld_fuer_termin_zeit():
    # Positivkontrolle: das Suchmuster findet die Termin-Uhrzeit; es gibt kein zweites Eingabefeld darauf.
    av = _av()
    assert av.count("_asZeitAnz(form.terminZeit)") == 1
    assert len(re.findall(r"terminZeit:e\.target\.value", av)) == 1


def test_dispo_reiter_nur_staff():
    s = _s()
    av = _av(s)
    # DispoPanel wird nur bei sub==="dispo" gerendert; der Reiter dorthin ist an Staff-Rollen gebunden
    assert av.count('sub==="dispo"&&React.createElement(DispoPanel') == 1
    assert av.count('...((["admin","buero","projektleiter"].indexOf(curUser.role)>=0)?[{id:"dispo",ik:"raster",l:"Dispo"}]:[])') == 1
    # setSub kennt keinen anderen Weg nach "dispo" (Reiterliste, vorheriger Reiter, Liste/Formular/QR)
    assert 'setSub("dispo")' not in av
    # Termin bestaetigen aus der Planung: Rollenliste = Staff
    assert 'var DISPO_PLAN_ROLLEN=["admin","buero","projektleiter"];' in s
    assert "if(DISPO_PLAN_ROLLEN.indexOf(rolle)<0)return {ok:false" in s
