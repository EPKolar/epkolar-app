# -*- coding: utf-8 -*-
"""v3.9.131 - Hotfix: Sync-Banner steckt am Handy + #310-Diagnose + Teilzeit-no-op.

v3.9.921 - DER ERSTE RIEGEL DIESER DATEI WURDE ERSETZT. Er lautete:

    # Diagnose: alle non-auth Throws tragen den HTTP-Status
    assert index_html.count('throw new Error("HTTP"+r.status+" "+e);') == 9

Was daran falsch war, in dieser Reihenfolge:

1. DIE BEHAUPTUNG IM KOMMENTAR STIMMTE NICHT. Gemessen am Bestand (v3.9.920):
   76 `throw new Error(` insgesamt. Neben den 9 gezaehlten stehen mindestens
   zehn weitere SCHREIBWEISEN desselben Wurfs - `"HTTP"+r.status+" "+t` (7x),
   `'HTTP'+r.status+' '+t` (2x), `"HTTP"+_r.status+" "+_t` (2x),
   `"HTTP"+((r&&r.status)||'?')`, `"HTTP"+_nResp.status` - und dazu Wuerfe ganz
   ohne Status. Der Riegel sah 9 von 49 Antwortzweigen. "Alle" war er nie.

2. ER WAR BUCHHALTER, NICHT PRUEFER. Bei jeder Erweiterung wurde die Zahl um
   +1 hochgezaehlt (8 -> 9, siehe die geloeschten Kommentarzeilen). Eine Zahl,
   die man beim Bauen nachzieht, misst den Ist-Zustand - nicht die Eigenschaft.
   Sie kann nie rot werden, weil man sie anpasst, statt sie ernst zu nehmen.

3. ER HAT EINE ECHTE LUECKE FESTGEHALTEN, STATT SIE ZU FINDEN. Genau das,
   wogegen der Riegel angeblich schuetzte, steht seit v3.8.7 im Code (siehe
   _OFFENE_LUECKEN unten) - und er war die ganze Zeit gruen.

WAS JETZT GEMESSEN WIRD
-----------------------
Die Eigenschaft selbst: KEIN Wurf aus einem Antwort-Pruefzweig verliert den
HTTP-Status. "Antwort-Pruefzweig" ist mechanisch definiert, nicht per Liste -
die Bedingung des Zweigs, in dem der Wurf steht, nennt `.ok` oder `.status`.
Damit ist jede Schreibweise erfasst, auch kuenftige, und die Zahl der Stellen
darf sich frei aendern, ohne dass jemand etwas nachzieht.

AUSDRUECKLICH NICHT DAZU (und WARUM) - diese Wuerfe pruefen KEINE Antwort,
ihnen fehlt der Status also nicht, sie haben nie einen gehabt:

  * Dateipruefung vor dem Hochladen: `Invalid dataUrl`, `Ungueltige Datei`
    (3x) - `if(!blob)`, es gab noch gar keine Anfrage.
  * Angemeldet-Zustand: `Nicht angemeldet` (2x), `User not found`,
    `Falsches Passwort`, `Anmeldung fehlgeschlagen [B20-H]` - lokaler Zustand.
  * Bibliothek fehlt: `CDN not loaded`, `pdfjsLib not loaded`, `PDF not
    loaded`, `pdfjs n/a`, `bcrypt-Bibliothek nicht geladen`.
  * Antwort war ERFOLGREICH, nur der INHALT passt nicht: `unerwartete Antwort
    fuer "+table` (`!Array.isArray(j)`), `Benutzer nicht gefunden [B20-B]`,
    `Benutzer gesperrt [B20-C]`, `Account unvollstaendig [B20-F]`. Der Status
    ist hier 200 - ihn mitzuschicken wuerde nichts erklaeren.
  * Sonstiges ohne Anfrage: `malformed` (JWT-Zerlegung), `Unsupported dataUrl
    scheme`, `no crop`, `Passwort konnte nicht gespeichert werden (0 Zeilen)`.

BLINDE FLECKEN DER MECHANISCHEN REGEL - benannt, damit sie niemand fuer
Abdeckung haelt:

  a) `worker-projects: Alte Zuweisungen konnten nicht entfernt werden` haengt
     an `if(!_delOk)`. `_delOk` wird zwei Zeilen frueher aus `!_r.ok` ODER aus
     einem `catch` gesetzt; in der Bedingung des Wurfs steht deshalb weder
     `.ok` noch `.status`. Der Status geht nur ins `console.error`, nicht in
     den Wurf. Ein Anker/Ersatz-Paar dafuer liegt im Uebergabebericht.
  b) In `stempel_terminal_workers` steht ein Wurf NACH zwei `continue`-Zweigen
     ohne eigene Bedingung. Er traegt den Status ohnehin
     (`'HTTP'+r.status+' '+t`), faellt aber nicht unter die Regel.
"""
import re

from _hilfen import nur_code

_WURF = "throw new Error("

# Eine noch NICHT geschlossene Luecke: `api.login` wirft im `!rpcRes.ok`-Zweig
# eine reine Klartextmeldung. Der Status steht daneben im `console.error`, aber
# nicht im Fehler - und der Fehler ist das, was in der Anmeldemaske landet.
# Ein 403 (RLS) sieht damit aus wie ein 500 (Server weg).
#
# Der Eintrag ist KEINE Buchhaltung, sondern eine FRIST: sobald der Wurf den
# Status traegt, faellt `test_offene_luecken_laufen_ab` um und zwingt zum
# Streichen. Ein stiller Dauereintrag ist damit ausgeschlossen.
# In v3.9.921 stand hier noch "Server nicht erreichbar [B20-A]": in api.login
# ging der Status ins console.error statt in den Fehler, und der Fehler ist das,
# was in der Anmeldemaske steht - ein 403 (Rechte) sah aus wie ein 500 (Server
# weg). Behoben in derselben Version; der Eintrag ist damit GESTRICHEN, weil
# test_offene_luecken_laufen_ab genau das erzwingt. Eine Ausnahmeliste ist eine
# FRIST, keine Buchhaltung: sie faellt um, sobald ihr Eintrag keine Luecke mehr
# ist, damit sie nicht die naechste zudeckt.
_OFFENE_LUECKEN = []

# Benannte Stellen, die als Antwortzweig ERKANNT werden muessen. Ohne sie
# koennte der Scanner unbemerkt erblinden (z.B. weil eine Klammer in einem
# String die Rueckwaertssuche aus dem Tritt bringt) und waere still gruen -
# genau die Krankheit, an der `nur_code()` zweimal gelitten hat.
_MUSS_ERKANNT = [
    ("(!r.ok)", 'HTTP"+r.status+" "+e'),
    ("(r.status===403)", 'HTTP403 "+_e403'),
    ("(!r||!r.ok)", "((r&&r.status)||'?')"),
    ("(_nResp&&!_nResp.ok)", '"HTTP"+_nResp.status'),
    ("(!_bResp.ok)", "Batch-Upsert fehlgeschlagen"),
    ("(!_sc.ok)", "_sc.status"),
    ("(!rpcRes.ok)", "[B20-A]"),
]

# Benannte Stellen, die NICHT als Antwortzweig gelten duerfen. Waere die Regel
# zu weit, muesste hier ein Status hinein, den es nicht gibt - und der naechste
# Bearbeiter wuerde eine Zahl erfinden, um gruen zu werden.
_DARF_NICHT_ERKANNT = [
    "CDN not loaded",
    "Nicht angemeldet",
    "Invalid dataUrl",
    "unerwartete Antwort",
    "pdfjsLib not loaded",
]


def _wurf_text(code, i):
    """Der Wurf ab `throw new Error(` bis zur schliessenden Klammer."""
    j = code.find("(", i)
    tiefe, p = 0, j
    while p < len(code):
        c = code[p]
        if c == "(":
            tiefe += 1
        elif c == ")":
            tiefe -= 1
            if tiefe == 0:
                return code[i:p + 1]
        p += 1
    return code[i:i + 400]


def _bedingung_vor(code, p):
    """Bedingung, die unmittelbar vor Position `p` endet: `if(...)`, `catch(e)`.

    Liefert (schluessel, bedingung) oder ("", "").
    """
    q = p
    while q >= 0 and code[q] in " \t\r\n":
        q -= 1
    if q < 0 or code[q] != ")":
        return ("", "")
    tiefe, e = 0, q
    while e >= 0:
        if code[e] == ")":
            tiefe += 1
        elif code[e] == "(":
            tiefe -= 1
            if tiefe == 0:
                break
        e -= 1
    if e < 0:
        return ("", "")
    bedingung = code[e:q + 1]
    k = e - 1
    while k >= 0 and code[k] in " \t\r\n":
        k -= 1
    m = re.search(r"(if|while|for|catch|switch)$", code[max(0, k - 8):k + 1])
    return ((m.group(1) if m else "?"), bedingung)


def _waechter(code, i):
    """Die Bedingung des Zweigs, in dem der Wurf an Position `i` steht."""
    # klammerloses `if(...) throw ...`
    schluessel, bedingung = _bedingung_vor(code, i - 1)
    if schluessel == "if":
        return bedingung
    # sonst: die oeffnende Klammer des umschliessenden Blocks suchen
    tiefe, q = 0, i - 1
    while q >= 0:
        c = code[q]
        if c == "}":
            tiefe += 1
        elif c == "{":
            if tiefe == 0:
                break
            tiefe -= 1
        q -= 1
    if q < 0:
        return ""
    return _bedingung_vor(code, q - 1)[1]


def _wuerfe(index_html):
    """Alle Wuerfe mit Bedingung, Antwortzweig-Urteil und Status-Urteil."""
    code = nur_code(index_html)
    aus, i = [], code.find(_WURF)
    while i != -1:
        text = _wurf_text(code, i)
        assert len(text) < 400, (
            "Ein Wurf laesst sich nicht mehr auf die Klammer genau schneiden "
            "(%d Zeichen). Vermutlich steht eine unbalancierte Klammer in einem "
            "String-Literal des Wurfs. Anfang: %r" % (len(text), text[:120])
        )
        bedingung = _waechter(code, i)
        # Prueft der Zweig eine ANTWORT? Dann muss der Status in den Wurf.
        antwort = bool(re.search(r"\.ok\b|\.status\b", bedingung))
        # Der Status gilt als getragen, wenn der Wurf ihn ausliest (`.status`)
        # oder - bei `if(x.status===403)` - die gepruefte Zahl woertlich nennt.
        zahlen = re.findall(r"\.status\s*===?\s*(\d{3})", bedingung)
        traegt = ".status" in text or any(z in text for z in zahlen)
        aus.append({"bed": bedingung, "wurf": text,
                    "antwort": antwort, "traegt": traegt})
        i = code.find(_WURF, i + 1)
    return aus


def _luecken(index_html):
    return [w for w in _wuerfe(index_html) if w["antwort"] and not w["traegt"]]


def _kurz(w):
    return "%s -> %s" % (w["bed"][:40], w["wurf"][:90])


# == Der eigentliche Riegel ==================================================

def test_antwortzweige_tragen_den_status(index_html):
    """Kein Wurf aus einem Antwort-Pruefzweig verliert den HTTP-Status."""
    alle = _wuerfe(index_html)
    antwort = [w for w in alle if w["antwort"]]
    # Keine feste Zahl - nur die Aussage, dass ueberhaupt gemessen wurde.
    # Ein Scanner, der nichts mehr findet, ist gruen und nutzlos.
    assert len(antwort) >= 30, (
        "Nur %d von %d Wuerfen wurden als Antwortzweig erkannt. Vorher waren es "
        "49. Der Scanner misst nichts mehr - pruefe `_waechter`, bevor du diese "
        "Schranke senkst." % (len(antwort), len(alle))
    )
    neu = [w for w in _luecken(index_html)
           if not any(o in w["wurf"] for o in _OFFENE_LUECKEN)]
    assert not neu, (
        "Ein Wurf aus einem Antwortzweig verliert den HTTP-Status. Damit ist "
        "im Fehlerfall nicht mehr unterscheidbar, ob 401/403 (Berechtigung), "
        "404 (Pfad) oder 5xx (Server) vorlag:" + chr(10)
        + chr(10).join("   " + _kurz(w) for w in neu[:5])
    )


def test_offene_luecken_laufen_ab(index_html):
    """Jeder Eintrag in _OFFENE_LUECKEN muss noch eine Luecke SEIN.

    Sonst waere die Ausnahmeliste genau das, was der alte Riegel war: eine
    Zahl, die den Ist-Zustand mitschreibt."""
    offen = [w["wurf"] for w in _luecken(index_html)]
    for eintrag in _OFFENE_LUECKEN:
        assert any(eintrag in w for w in offen), (
            "%r steht in _OFFENE_LUECKEN, ist aber keine Luecke mehr (entweder "
            "behoben oder der Wurf heisst anders). Eintrag STREICHEN - sonst "
            "deckt er kuenftig eine echte Luecke zu." % (eintrag,)
        )


def test_benannte_antwortzweige_werden_erkannt(index_html):
    """Der Scanner darf nicht unbemerkt erblinden."""
    alle = _wuerfe(index_html)
    for bed, teil in _MUSS_ERKANNT:
        treffer = [w for w in alle if w["bed"] == bed and teil in w["wurf"]]
        assert treffer, (
            "Benannte Stelle nicht mehr gefunden: Bedingung %r mit %r im Wurf. "
            "Entweder wurde der Code umgebaut (dann Anker anpassen) oder der "
            "Scanner sieht sie nicht mehr (dann ist er still gruen)."
            % (bed, teil)
        )
        assert all(w["antwort"] for w in treffer), (
            "Bedingung %r gilt nicht mehr als Antwortzweig - der Riegel prueft "
            "diese Stelle nicht mehr." % (bed,)
        )


def test_nicht_antwortwuerfe_bleiben_draussen(index_html):
    """Die Regel darf nicht zu weit greifen: wo es keine Antwort gibt, darf
    auch kein Status verlangt werden."""
    alle = _wuerfe(index_html)
    for teil in _DARF_NICHT_ERKANNT:
        treffer = [w for w in alle if teil in w["wurf"]]
        assert treffer, "Benannte Stelle weg - Anker anpassen: %r" % (teil,)
        falsch = [w for w in treffer if w["antwort"]]
        assert not falsch, (
            "%r gilt jetzt als Antwortzweig, obwohl dort keine Antwort geprueft "
            "wird. Die Regel greift zu weit; der naechste Bearbeiter wuerde "
            "einen Status erfinden, um gruen zu werden: %s"
            % (teil, "; ".join(_kurz(w) for w in falsch[:3]))
        )


# == Umkehrprobe =============================================================

_RUECKBAU = [
    # (Anker, Ersatz ohne Status) - beide Anker kommen roh GENAU EINMAL vor.
    ('throw new Error("HTTP"+r.status+" Storage upload failed: "+txt)',
     'throw new Error("Storage upload failed")'),
    ('throw new Error("Batch-Upsert fehlgeschlagen ("+_bResp.status+"): "'
     '+_et.slice(0,150))',
     'throw new Error("Batch-Upsert fehlgeschlagen")'),
]


def test_umkehrprobe_verlorener_status_wird_rot(index_html):
    """Nimmt man einer benannten Stelle den Status, MUSS der Riegel anschlagen.

    Ohne diese Probe ist `test_antwortzweige_tragen_den_status` nur eine
    Behauptung - genau wie der Riegel, den er ersetzt hat."""
    vorher = len(_luecken(index_html))
    for anker, ersatz in _RUECKBAU:
        assert index_html.count(anker) == 1, (
            "Vorbedingung weg: der Anker kommt %d mal vor statt einmal."
            % index_html.count(anker)
        )
        kaputt = index_html.replace(anker, ersatz, 1)
        nachher = _luecken(kaputt)
        assert len(nachher) == vorher + 1, (
            "Umkehrprobe traegt nicht: nach dem Rueckbau muesste genau eine "
            "Luecke mehr gemeldet werden (%d statt %d)."
            % (len(nachher), vorher + 1)
        )
        assert any(ersatz in w["wurf"] for w in nachher), (
            "Umkehrprobe traegt nicht: die neue Luecke ist nicht die "
            "zurueckgebaute Stelle."
        )


def test_umkehrprobe_der_alte_riegel_haette_geschwiegen(index_html):
    """Beweis, dass der ersetzte Riegel die Luecke NICHT gesehen haette.

    Der alte Riegel zaehlte nur eine Schreibweise. Beide Rueckbauten oben
    lassen diese Zahl unveraendert - er waere gruen geblieben."""
    alt = 'throw new Error("HTTP"+r.status+" "+e);'
    for anker, ersatz in _RUECKBAU:
        kaputt = index_html.replace(anker, ersatz, 1)
        assert kaputt.count(alt) == index_html.count(alt), (
            "Der alte Riegel haette den Rueckbau doch bemerkt - dann stimmt "
            "die Begruendung dieser Datei nicht mehr."
        )


# == Unveraendert aus v3.9.131 ==============================================

def test_sync_transient_vs_permanent(index_html):
    # Banner-steckt-Fix: nur transiente Fehler behalten die Queue; 4xx/online-TypeError droppen nach Retries
    # v3.9.149: 408/429 ergänzt (retrybar)
    assert 'const _transient=!navigator.onLine||_st>=500||_st===408||_st===429||e.message===' in index_html
    assert "if(_transient){fail++;break;}" in index_html
    # die alte "jeder TypeError = network = break"-Logik ist weg
    assert "const isNetwork=!navigator.onLine||e.message==='Failed to fetch'||e.name==='TypeError';" not in index_html


def test_failed_banner_dismiss_button(index_html):
    # Banner verschwindet: "Verwerfen" leert syncQueueFailed
    assert 'const _clearFailed=async()=>{try{await ODB.save("syncQueueFailed",[]);}catch(_e){}setFailedCount(0);' in index_html
    assert '"✕ Verwerfen"' in index_html


def test_sync_drop_diagnostic_log(index_html):
    assert '"[sq] DROP nach 5 Fehlversuchen:"' in index_html
    assert "_bodyKeys:_bodyKeys" in index_html
