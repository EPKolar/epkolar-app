# -*- coding: utf-8 -*-
"""v3.9.912 - Beim Abmelden schwieg die App, wenn sie nicht lesen konnte.

    async count(){ try{ ... return q.length; } catch(e){ return 0; } }

    const logout = async()=>{ const cnt=await SQ.count(); ...
      if(cnt>0) _msg.push(...);
      if(_msg.length && !confirm("... werden VERWORFEN. Trotzdem abmelden?")) return;
      ... SQ und PhotoQ werden GELEERT ...

Faellt das Lesen der Warteschlange aus, liefert der Zaehler **0**. Die Warnung
haengt an `>0` - es kam also keine. Und direkt danach werden beide
Warteschlangen geleert.

**Wer bei vollem Geraetespeicher abmeldet, verlor seine ungesendeten
Aenderungen stumm.** Eine 0, die in Wahrheit "nicht lesbar" heisst, ist hier
nicht bloss eine falsche Auskunft - sie ist die ZUSTIMMUNG zum Loeschen.

Der Fehlerfall ist real: das Repo warnt an anderer Stelle selbst vor vollem
Geraetespeicher, wenn ein Foto nicht mehr in die Warteschlange passt.

────────────────────────────────────────────────────────────────────────────
Warum kein `return null`
────────────────────────────────────────────────────────────────────────────
Der naheliegende Griff waere gewesen, den Zaehler bei einem Fehler `null`
liefern zu lassen - so wie es v3.9.908/909/911 an den Kacheln gemacht haben.
Hier hilft das NICHT: alle vier Verbraucher fragen `>0`, und `null > 0` ist
ebenfalls falsch. Sie blieben also genauso stumm, und der Umbau haette nur
gefaehrlich ausgesehen, ohne etwas zu aendern.

Es braucht einen ZWEITEN Weg, und der wird genau dort gelesen, wo die Folge
schwer ist: beim Abmelden. Die anderen drei Verbraucher (Banner, Auto-Sync)
bleiben unangetastet - dort ist die Folge ein fehlender Hinweis, kein
Datenverlust. Ein Riegel unten haelt das fest.

Die Rueckfrage sagt ausdruecklich, dass die Zahl **unbekannt** ist, nicht null.
Genau das ist der Unterschied zwischen "nichts offen" und "nicht gemessen", den
dieser Tag in v3.9.898, 908, 909, 910 und 911 durchbuchstabiert hat.
"""
from _hilfen import nur_code


def test_die_zaehler_melden_ob_sie_lesen_konnten(index_html):
    code = nur_code(index_html)
    assert "SQ._leseFehler=false;" in code and "catch(e){SQ._leseFehler=true;return 0;}" in code, (
        "SQ.count meldet nicht mehr, ob es lesen konnte - dann ist die 0 aus "
        "dem Auffangzweig wieder ununterscheidbar von 'nichts offen'."
    )
    assert "PhotoQ._leseFehler=false;" in code, (
        "PhotoQ.count meldet nicht mehr, ob es lesen konnte."
    )


def test_der_rueckgabewert_bleibt_eine_zahl(index_html):
    """DER KERN DER ABWAEGUNG. Ein null haette hier NICHTS geholfen - alle vier
    Verbraucher fragen >0, und null>0 ist ebenfalls falsch. Der Zaehler muss
    also weiter eine Zahl liefern; die Unterscheidung laeuft ueber den
    zweiten Weg."""
    code = nur_code(index_html)
    assert "catch(e){SQ._leseFehler=true;return 0;}" in code, (
        "SQ.count liefert im Fehlerfall keine Zahl mehr - dann brechen die "
        "Verbraucher, die damit rechnen."
    )


def test_das_abmelden_fragt_nach(index_html):
    code = nur_code(index_html)
    assert "const _sqUnlesbar=!!SQ._leseFehler;" in code, (
        "Das Abmelden liest den Merker der Sync-Warteschlange nicht."
    )
    assert "const _phUnlesbar=!!PhotoQ._leseFehler;" in code, (
        "Das Abmelden liest den Merker der Foto-Warteschlange nicht."
    )
    assert "if(!_msg.length&&(_sqUnlesbar||_phUnlesbar)&&!confirm(" in code, (
        "Es gibt keine Rueckfrage mehr fuer den Fall, dass die Warteschlange "
        "nicht lesbar ist - dann wird wieder stumm geloescht."
    )


def test_die_rueckfrage_sagt_dass_die_zahl_unbekannt_ist(index_html):
    """Eine Rueckfrage, die 'keine offenen Aenderungen' behauptet, waere
    dieselbe Luege in neu. Sie muss sagen, dass NICHT GEMESSEN werden konnte."""
    i = index_html.find("if(!_msg.length&&(_sqUnlesbar||_phUnlesbar)")
    assert i != -1
    text = index_html[i:i + 520]
    assert "NICHT LESBAR" in text, (
        "Die Rueckfrage nennt den Grund nicht."
    )
    assert "laesst sich nicht feststellen" in text, (
        "Die Rueckfrage sagt nicht, dass die ANZAHL unbekannt ist - der Nutzer "
        "muss wissen, dass hier nicht gemessen wurde."
    )


def test_die_bestehende_warnung_bleibt_unveraendert(index_html):
    """GEGENPROBE: der Fall 'es sind nachweislich N Aenderungen offen' war
    schon richtig. Diese Version durfte ihn nicht anfassen - sonst haette sie
    einen funktionierenden Schutz gegen einen neuen getauscht."""
    assert ('if(_msg.length&&!confirm("⚠️ "+_msg.join(" + ")'
            '+" werden VERWORFEN. Trotzdem abmelden?"))return;') in index_html, (
        "Die bestehende Warnung fuer gezaehlte Aenderungen hat sich veraendert."
    )


def test_die_anderen_verbraucher_bleiben_unangetastet(index_html):
    """Bewusste Grenze: nur das Abmelden liest den Merker. Bei Banner und
    Auto-Sync ist die Folge eines Lesefehlers ein fehlender Hinweis, kein
    Datenverlust - dort waere eine Rueckfrage laestig statt hilfreich."""
    code = nur_code(index_html)
    # v3.9.912: hier stand zuerst eine GESAMTZAHL (== 6). Sie hat einen ECHTEN
    # Mangel gefunden - der Fehlerzweig von PhotoQ.count setzte den Merker gar
    # nicht, die Rueckfrage waere fuer Fotos also stumm geblieben. Danach ist
    # sie trotzdem entfallen: eine Summe misst die Buchhaltung, nicht die
    # Eigenschaft, und sie muss bei jeder neuen Zeile nachgezogen werden.
    # Geprueft werden jetzt die VIER Stellen namentlich - beide Zweige beider
    # Zaehler - plus die Abgrenzung, dass sonst niemand fragt.
    for stelle in ("SQ._leseFehler=false;",
                   "catch(e){SQ._leseFehler=true;return 0;}",
                   "PhotoQ._leseFehler=false;",
                   "catch(e){PhotoQ._leseFehler=true;return 0;}"):
        assert stelle in code, (
            "Diese Stelle setzt den Merker nicht: " + stelle
        )
    # Abgrenzung: nur das Abmelden LIEST ihn.
    # v3.9.914: aus 1 wird 2 - BEWUSST, nicht um den Riegel wegzuraeumen. Die
    # Abgrenzung von v912 lautete: nur dort lesen, wo Datenverlust droht. Sie
    # hat eine zweite solche Stelle uebersehen - der Knopf "Lokale Daten
    # loeschen" ruft indexedDB.deleteDatabase und loescht damit haerter als das
    # Abmelden. Beide Leser werden hier NAMENTLICH festgehalten, damit aus der
    # Zahl 2 nicht spaeter stillschweigend eine 3 an einer harmlosen Stelle wird.
    assert code.count("!!SQ._leseFehler") == 2 and code.count("!!PhotoQ._leseFehler") == 2, (
        "Der Merker wird an einer anderen Zahl von Stellen gelesen als den zwei "
        "vorgesehenen (Abmelden, Lokale-Daten-loeschen). Bei Banner und Auto-Sync "
        "ist die Folge eines Lesefehlers ein fehlender Hinweis, kein Datenverlust "
        "- dort waere eine Rueckfrage laestig statt hilfreich."
    )
    assert "const _sqUnlesbar=!!SQ._leseFehler;" in code, "Leser 1 (Abmelden) fehlt."
    assert "const _wipeUnlesbar=(!!SQ._leseFehler)||(!!PhotoQ._leseFehler);" in code, (
        "Leser 2 (Lokale Daten loeschen) fehlt - dann loescht der Knopf wieder "
        "mit dem weichen Confirm, obwohl die Anzahl nie gemessen wurde."
    )


# ══ Umkehrprobe ═════════════════════════════════════════════════════════════

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    z1 = index_html.replace("catch(e){SQ._leseFehler=true;return 0;}",
                            "catch(e){return 0;}", 1)
    assert z1 != index_html, "Rueckbau 1 griff nicht"
    assert "catch(e){SQ._leseFehler=true;return 0;}" not in nur_code(z1), (
        "Umkehrprobe: der Merker-Riegel wuerde nicht anschlagen"
    )

    z2 = index_html.replace("if(!_msg.length&&(_sqUnlesbar||_phUnlesbar)&&!confirm(",
                            "if(false&&!confirm(", 1)
    assert z2 != index_html, "Rueckbau 2 griff nicht"
    assert "if(!_msg.length&&(_sqUnlesbar||_phUnlesbar)&&!confirm(" not in nur_code(z2), (
        "Umkehrprobe: der Rueckfrage-Riegel wuerde nicht anschlagen"
    )
