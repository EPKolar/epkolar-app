# -*- coding: utf-8 -*-
"""v3.9.914 - vier weitere Stellen, an denen eine fehlgeschlagene Messung als
Zahl erschien. Fortsetzung von v3.9.898/908/909/910/911/912/913.

DIE VIER
────────────────────────────────────────────────────────────────────────────
1. ADMIN-STATISTIK. `activity_log` faellt aus -> Vorgaenge/Heute/Logins/
   Fehlversuche zeigen einen Strich, "Letzter Login" zeigt fuer JEDEN
   Mitarbeiter "Nie", "Logins gesamt" zeigt 0, und die Faerbung der Kachel
   Fehlversuche haengt an `(stats.failedLogins30d||0)>10` - sie kann bei einem
   Ausfall NIE rot werden. Ein Chef liest daraus: niemand arbeitet mit der App,
   und es gab keine Anmeldeversuche.

2. URLAUBSKONTINGENT. Faellt das Lesen aus, bleibt der Zustand auf der
   EINGEBAUTEN Voreinstellung 192,5h / Vorjahr 0 / Ueberstunden 0 - und die
   Tabelle zeigt daraus einen Resturlaub. Der Rueckfall auf den lokalen Cache
   greift nicht: der Speicher-Effekt schreibt beim Aufbau die Voreinstellung
   nach ODB, und der Cache-Merge fuellt nur Schluessel, die NOCH FEHLEN - es
   fehlt aber keiner. Schlimmer als die Anzeige ist der Knopf daneben:
   "Speichern" schreibt den ganzen Zustand per Upsert zurueck und haette die
   echten Werte aller Mitarbeiter durch die Voreinstellung ersetzt.

3. LOKALE DATEN LOESCHEN. Die zweite Stelle, an der die 0 aus dem
   Auffangzweig eine ZUSTIMMUNG zum Loeschen ist. v3.9.912 hat den Merker
   `_leseFehler` gebaut und ausdruecklich nur beim Abmelden gelesen. Dieser
   Knopf loescht HAERTER (indexedDB.deleteDatabase) und las ihn nicht.

4. FRISTEN. Faellt das Lesen von material_orders / tickets / defects aus,
   feuert die Automatik KEINE Ueberfaellig-Meldung. Die stille Glocke sieht
   aus wie "nichts ueberfaellig".

WELCHE REPARATURART WO - die Lehre des Tages, angewandt
────────────────────────────────────────────────────────────────────────────
* Admin-Statistik: die Anzeige kann bereits Text ("Strich") - aber der Strich
  ist zweideutig. Eigener Zustand PLUS ein Satz darueber, was nicht gemessen
  wurde. Ein null je Kennzahl haette hier nichts gebracht: die Faerbung fragt
  `>10`, und `null>10` ist genauso falsch wie `0>10`.
* Urlaub: die Anzeige RECHNET mit den Zahlen. Ein null waere NaN. Also
  zweiter Weg (Merker) + Banner + Schreibsperre.
* Wipe: alle Verbraucher fragen `>0`. Zweiter Weg, exakt wie v3.9.912.
* Fristen: es gab gar keine Darstellung - die vorhandene Glocke meldet
  ihren eigenen Ausfall.
"""
from _hilfen import nur_code


# ══ 1 ADMIN-STATISTIK ═══════════════════════════════════════════════════════

def test_admin_der_schnitt_verliert_die_marke_nicht(index_html):
    """DER STOLPERSTEIN: slice() liefert ein FRISCHES Array. Die Marke, die
    _sbGetOrder seit v3.9.910 auf das leere Array eines 401/403 setzt, waere
    dabei verschwunden - _rlsLeer() unten haette IMMER falsch gesagt und der
    Umbau haette wie eine Reparatur ausgesehen, ohne eine zu sein."""
    code = nur_code(index_html)
    assert code.count("const _s=r.slice(0,200);try{if(r&&r.__rlsFehler)_s.__rlsFehler=r.__rlsFehler;}") == 1
    assert code.count("const _s=r.slice(0,2000);try{if(r&&r.__rlsFehler)_s.__rlsFehler=r.__rlsFehler;}") == 1


def test_admin_die_einzelnen_auffangzweige_der_aktivitaet_sind_weg(index_html):
    """Bauart v3.9.909: wo ein AEUSSERER Auffangzweig bereits Toast und
    Leerbild zeigt, ist der innere nur ein Deckel darauf."""
    code = nur_code(index_html)
    assert 'action=like.login*").then(r=>r.slice(0,200)).catch(()=>[])' not in code
    assert '.then(r=>r.slice(0,2000)).catch(()=>[])' not in code


def test_admin_die_seite_weiss_dass_sie_nichts_weiss(index_html):
    code = nur_code(index_html)
    assert "const _alUnlesbar=_rlsLeer(actRows)||_rlsLeer(logRows);" in code
    assert "alUnlesbar:_alUnlesbar" in code
    assert "stats.alUnlesbar?React.createElement(" in code


def test_admin_der_hinweis_nennt_die_betroffenen_zahlen(index_html):
    """Ein Banner, das nur "Fehler" sagt, laesst den Leser raten, WELCHE Zahl
    gelogen hat. Die vier Kacheln und die zwei Tabellenspalten muessen
    dastehen."""
    i = index_html.find("stats.alUnlesbar?React.createElement(")
    assert i != -1
    t = index_html[i:i + 900]
    assert "NICHT GEMESSEN" in t
    assert "Fehlversuche" in t and "Letzter Login" in t


def test_admin_die_bestehende_anzeige_bleibt(index_html):
    """GEGENPROBE: die vier Kacheln waren nicht falsch gebaut, nur
    unbeschriftet. Sie duerfen sich nicht veraendert haben."""
    assert 'value: stats.total||"—", sub: "letzte 30 Tage"' in index_html
    assert 'color: (stats.failedLogins30d||0)>10?COLORS.ERROR:COLORS.NEUTRAL' in index_html


# ══ 2 URLAUBSKONTINGENT ═════════════════════════════════════════════════════

def test_urlaub_der_ausfall_wird_markiert_und_gemerkt(index_html):
    code = nur_code(index_html)
    assert ('const data=await _sbGet("urlaubskontingent","jahr=eq."+yr)'
            '.catch(()=>{const _e=[];try{_e.__rlsFehler=-1;}catch(_m){}return _e;});') in code
    assert "setKontUnlesbar(_rlsLeer(data));" in code
    assert "const [kontUnlesbar,setKontUnlesbar]=_react.useState.call(void 0, false);" in code


def test_urlaub_die_leere_aber_gelesene_antwort_bleibt_harmlos(index_html):
    """WICHTIGE ABGRENZUNG. Sind fuer ein Jahr wirklich keine Kontingente
    hinterlegt, ist die Voreinstellung die richtige Antwort - der Merker darf
    dann NICHT gesetzt werden. Deshalb haengt er an _rlsLeer (Marke), nicht an
    data.length."""
    code = nur_code(index_html)
    assert "setKontUnlesbar(_rlsLeer(data));" in code
    assert "setKontUnlesbar(!data.length)" not in code
    assert "setKontUnlesbar(data.length===0)" not in code


def test_urlaub_speichern_ist_gesperrt_solange_nichts_gelesen_wurde(index_html):
    """DER TEURE TEIL. Der Knopf schreibt den GANZEN Zustand fuer JEDEN
    Monteur per Upsert zurueck. Ohne diese Sperre haette ein Klick die echten
    Anspruchs-, Vorjahres- und Ueberstundenwerte aller Mitarbeiter durch
    192,5 / 0 / 0 ersetzt."""
    code = nur_code(index_html)
    assert "onClick: ()=>{if(editKontingent&&kontUnlesbar){" in code
    i = code.find("onClick: ()=>{if(editKontingent&&kontUnlesbar){")
    t = code[i:i + 700]
    assert "NICHT gespeichert" in t, "Die Sperre sagt dem Nutzer nicht, dass nicht gespeichert wurde."
    assert "setEditKontingent(false);return;" in t, "Die Sperre kehrt nicht zurueck - der Upsert liefe weiter."


def test_urlaub_das_banner_nennt_die_voreinstellung(index_html):
    i = index_html.find("kontUnlesbar?React.createElement(")
    assert i != -1
    t = index_html[i:i + 800]
    assert "192,5" in t, "Das Banner nennt die eingebauten Werte nicht - der Leser haelt sie fuer gemessen."
    assert "NICHT GEMESSEN" in t


# ══ 3 LOKALE DATEN LOESCHEN ═════════════════════════════════════════════════

def test_wipe_liest_den_merker_aus_v912(index_html):
    """DIE ZWEITE STELLE. v3.9.912 hat den Merker gebaut und nur beim Abmelden
    gelesen. Dieser Knopf loescht HAERTER: indexedDB.deleteDatabase."""
    code = nur_code(index_html)
    assert "const _wipeUnlesbar=(!!SQ._leseFehler)||(!!PhotoQ._leseFehler);" in code
    assert "if(_wipeUnlesbar){" in code


def test_wipe_die_rueckfrage_sagt_unbekannt_nicht_null(index_html):
    i = index_html.find("if(_wipeUnlesbar){")
    assert i != -1
    t = index_html[i:i + 900]
    assert "NICHT gelesen werden" in t
    assert "lässt sich NICHT feststellen" in t, (
        "Die Rueckfrage sagt nicht, dass die ANZAHL unbekannt ist - eine "
        "Rueckfrage, die 'keine offenen Aenderungen' behauptet, waere dieselbe "
        "Luege in neu."
    )


def test_wipe_die_gezaehlte_warnung_bleibt_unveraendert(index_html):
    """GEGENPROBE: der Fall 'es sind nachweislich N offen' war schon richtig
    und darf nicht gegen den neuen Zweig getauscht worden sein."""
    code = nur_code(index_html)
    assert "}else if(_cnt>0||_pcnt>0){" in code
    assert 'title:"Ungesyncte Daten gehen verloren"' in index_html
    assert 'title:"Lokale Daten löschen"' in index_html


# ══ 4 FRISTEN ═══════════════════════════════════════════════════════════════

def test_fristen_alle_drei_lesungen_markieren_ihren_ausfall(index_html):
    code = nur_code(index_html)
    for tab in ('_sbGet("material_orders","status=eq.angefordert")',
                '_sbGet("tickets","select=id,title,due_date,status,assignee&due_date=lt."+_today)',
                '_sbGet("defects","select=id,title,frist,status,zugewiesen,worker&frist=lt."+_today)'):
        assert (tab + ".catch(()=>{const _e=[];try{_e.__rlsFehler=-1;}catch(_m){}return _e;});") in code, (
            "Diese Lesung markiert ihren Ausfall nicht: " + tab
        )
        assert (tab + ".catch(()=>[]);") not in code


def test_fristen_der_ausfall_wird_ueber_die_glocke_gemeldet(index_html):
    """Es gab hier gar keine Darstellung fuer 'nicht gemessen'. Die Glocke ist
    die vorhandene Anzeige - also meldet sie ihren eigenen Ausfall. fire() hat
    4h Sperrzeit je Schluessel, das bleibt eine Meldung, kein Dauerpiepen."""
    code = nur_code(index_html)
    assert 'if(_rlsLeer(openMat))fire("rls_material"' in code
    assert 'if(_rlsLeer(ovT)||_rlsLeer(ovD))fire("rls_frist"' in code


def test_fristen_die_meldung_sagt_was_ausfaellt(index_html):
    i = index_html.find('fire("rls_frist"')
    assert i != -1
    t = index_html[i:i + 400]
    assert "NICHT gemeldet" in t


# ══ UMKEHRPROBE ═════════════════════════════════════════════════════════════
# Jeder Riegel oben wird gegen einen kuenstlichen Rueckbau gehalten. Ein
# Riegel, der still gruen bleibt, ist schlimmer als gar keiner (v3.9.874).

def _weg(text, alt, neu):
    z = text.replace(alt, neu, 1)
    assert z != text, "Rueckbau griff nicht an: " + alt[:70]
    return z


def test_selbsttest_die_riegel_schlagen_beim_rueckbau_an(index_html):
    import pytest

    faelle = [
        # (Rueckbau alt, Rueckbau neu, Riegel-Funktion)
        ("const _s=r.slice(0,200);try{if(r&&r.__rlsFehler)_s.__rlsFehler=r.__rlsFehler;}catch(_am){}return _s;",
         "return r.slice(0,200);",
         test_admin_der_schnitt_verliert_die_marke_nicht),
        ("const _alUnlesbar=_rlsLeer(actRows)||_rlsLeer(logRows);",
         "const _alUnlesbar=false;",
         test_admin_die_seite_weiss_dass_sie_nichts_weiss),
        ("setKontUnlesbar(_rlsLeer(data));", "",
         test_urlaub_der_ausfall_wird_markiert_und_gemerkt),
        ("onClick: ()=>{if(editKontingent&&kontUnlesbar){",
         "onClick: ()=>{if(false){",
         test_urlaub_speichern_ist_gesperrt_solange_nichts_gelesen_wurde),
        ("const _wipeUnlesbar=(!!SQ._leseFehler)||(!!PhotoQ._leseFehler);",
         "const _wipeUnlesbar=false;",
         test_wipe_liest_den_merker_aus_v912),
        ('if(_rlsLeer(ovT)||_rlsLeer(ovD))fire("rls_frist"',
         'if(false)fire("rls_frost"',
         test_fristen_der_ausfall_wird_ueber_die_glocke_gemeldet),
        ('_sbGet("tickets","select=id,title,due_date,status,assignee&due_date=lt."+_today)'
         '.catch(()=>{const _e=[];try{_e.__rlsFehler=-1;}catch(_m){}return _e;});',
         '_sbGet("tickets","select=id,title,due_date,status,assignee&due_date=lt."+_today).catch(()=>[]);',
         test_fristen_alle_drei_lesungen_markieren_ihren_ausfall),
    ]
    for alt, neu, riegel in faelle:
        kaputt = _weg(index_html, alt, neu)
        with pytest.raises(AssertionError):
            riegel(kaputt)
