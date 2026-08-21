"""
Nachtlauf-Hunt v3.9.843 — 3 verifizierte Korrektheitsfixes (je aus einem
read-only Hunt-Agenten, jeder Fund selbst gegen den Code gegengeprüft).

(A) Material-Bestellungen: der "Erledigt"-Filter-Zähler war hart `cnt:0`,
    obwohl der Filter `status==="geliefert"||"storniert"` selektiert und die
    anderen Tabs ihren cnt berechnen → das Badge zeigte nie eine Zahl.
(B) Fahrzeug-QR km-Eintrag (qDoKm): schrieb den History-Eintrag mit `notiz`
    (Anzeige liest `note`) + ohne `by` → Notiz/Autor leer; und persistierte nur
    `{kmStand}`, nicht das km_log → QR-km-History ging beim Reload verloren.
    Jetzt via upd() wie der kanonische addKm (Felder note/by + km_log-Persist).
(C) Bautagebuch 0 °C wurde als falsy verschluckt an 3 Consumer-Stellen
    (Bearbeiten-Vorbelegung, Export-Zeile, Listen-Anzeige).
"""


# ---------- (A) Material Erledigt-Zähler ----------

def test_material_erledigt_counter_berechnet(index_html):
    # der harte cnt:0 ist weg ...
    assert '{id:"erledigt",l:"Erledigt",cnt:0}' not in index_html
    # ... und wird jetzt aus demselben Prädikat wie der Filter berechnet
    assert '{id:"erledigt",l:"Erledigt",cnt:suppOrders.filter(o=>o.status==="geliefert"||o.status==="storniert").length}' in index_html


# ---------- (B) Fahrzeug-QR km-Eintrag ----------

def test_qdokm_kanonische_felder_und_persist(index_html):
    # kein Voll-Overwrite/Falschfeld-Log mehr
    assert 'const log={id:uid(),km,datum:td2(),notiz:qKmNote};' not in index_html
    assert 'SQ.push({url:"/api/fahrzeuge/"+fid,method:"PUT",body:{kmStand:km}});' not in index_html
    # jetzt via upd() mit kanonischen Feldern note/by UND km_log-Persist
    assert 'upd(fid,f=>{f.kmLog=[{km,datum:td2(),note:qKmNote,by:' in index_html
    assert 'f.kmStand=km;return f;},u=>({kmLog:u.kmLog,kmStand:u.kmStand}));' in index_html


# ---------- (C) Bautagebuch 0 °C nicht als falsy ----------

def test_bautagebuch_0grad_edit_vorbelegung(index_html):
    assert 'temperatur:e.temperatur||"",anwesende:e.anwesende||[]' not in index_html
    assert 'temperatur:(e.temperatur!=null&&e.temperatur!=="")?String(e.temperatur):""' in index_html


def test_bautagebuch_0grad_export_und_anzeige(index_html):
    # Export-Zeile
    assert 'e.temperatur?(e.temperatur+" °C"):""' not in index_html
    assert '(e.temperatur!=null&&e.temperatur!=="")?(e.temperatur+" °C"):""' in index_html
    # Listen-Anzeige (kein bare-"0"-Render mehr)
    assert '(e.temperatur!=null&&e.temperatur!=="")&&React.createElement(\'span\', { style: {fontSize:12,color:V.dm,fontFamily:mono}}, e.temperatur, " °C")' in index_html
