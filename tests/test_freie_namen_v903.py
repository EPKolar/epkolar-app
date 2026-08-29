# -*- coding: utf-8 -*-
"""v3.9.903 - Vier freie Namen, dieselbe Bombe wie der Live-Absturz von v899.

Gefunden mit einem echten Parser (espree + eslint-scope, die Maschine hinter
ESLints no-undef) ueber die ganze Datei, abgesichert durch eine Mutationsprobe:
40 zufaellig verteilte Referenzen kuenstlich verbogen, 40 erkannt. Danach meldet
der Scanner fuer index.html: KEINE freie Variable.

Alle vier waren derselbe Fehler wie `f` in v899: **ein Name aus einer anderen
Funktion kopiert, ohne ihn anzupassen.** Zwei davon sind stille Denkmaeler - ein
`catch` faengt den ReferenceError, und der Kommentar daneben verspricht eine
Wirkung, die es seit der Einfuehrung nie gab.

────────────────────────────────────────────────────────────────────────────
1 - `ev` im Bild-Zweig des Plan-Uploads
────────────────────────────────────────────────────────────────────────────
    compressPhoto(file,4000,0.92).then(ph=>{ ...
      try{_planCachePut(np.id,_dataUrlToBlob(ev.target.result));}catch(_pu){}

Der Rueckruf heisst `ph`. `ev` gibt es nur im PDF-Zweig darueber, aus dem die
Zeile kopiert wurde. AUSLOESER: jeder Plan-Upload, der kein PDF ist - also Foto,
JPG, PNG, auf der Baustelle der haeufigere Fall.

FOLGE: kein Absturz, keine Meldung - das `catch` schluckt alles. Aber
**v3.9.890 hat fuer Bild-Plaene nie gewirkt**: die Bytes, die der Kommentar
daneben zu behalten verspricht, waren beim naechsten Pull weg. Ein Fix, der
seit seiner Einfuehrung kein einziges Mal gelaufen ist.

────────────────────────────────────────────────────────────────────────────
2 - `_built` im Geo-Prefetch von ArbeitsscheinView
────────────────────────────────────────────────────────────────────────────
`_built` lebt in `DispoPanel`, einer ANDEREN Komponente. AUSLOESER: jeder offene
Arbeitsschein bei jedem Lauf. Auch hier faengt das `catch` und liefert
`a.kundPlz` - also exakt den Zustand VOR v3.9.888. Der Kommentar daneben sagt,
der Prefetch habe "NIE echte Kilometer" geliefert; sein Fix lief nie.

REPARIERT MIT EINER QUELLE, nicht mit einer zweiten Rechnung: der Ort-Index
wurde bisher nur in `_dispoBuildInput` gebaut. Ihn hier ein zweites Mal
auszuschreiben waere die naechste Groesse mit zwei Rechnungen gewesen - deshalb
`_ortIdxAus(geo)` als gemeinsamer Helfer, den beide Stellen rufen.

────────────────────────────────────────────────────────────────────────────
3 - `_user` im Selbsttest T-110 "Monteur sieht nur eigene AS"
────────────────────────────────────────────────────────────────────────────
`_user` ist ein `let` in der IIFE von `window.API`. Der Runner faengt die
Ausnahme, also stand dort "exception" statt eines Ergebnisses.

Das Tueckische: fuer JEDE andere Rolle steigt der Test eine Zeile vorher als
"skip" aus. Wer als Admin prueft, sieht "skip" und haelt den Riegel fuer in
Ordnung. **Der RLS-Riegel fuer Monteure hat nie gemessen** - und genau fuer die
war er gebaut.

────────────────────────────────────────────────────────────────────────────
4 - `A` in HBarChart auf der Startseite
────────────────────────────────────────────────────────────────────────────
    background: it.color||A

`A` ist ein `var` aus einer anderen Funktion. UNGEFANGEN, mitten im React-Render
der Startseite. Heute nicht ausloesbar, weil der einzige Aufrufer die Farbe fest
setzt und der Kurzschluss `A` nie erreicht.

**Eine geladene Waffe.** Sobald jemand HBarChart ein zweites Mal benutzt oder
die Farbe aus Daten kommt, ist es v899 noch einmal: weisser Schirm auf der
Startseite. Strukturell identisch - ein freier Name hinter einem
datenabhaengigen Kurzschluss.
"""
from _hilfen import nur_code


# ══ 1 - Plan-Upload ═════════════════════════════════════════════════════════

def test_der_bild_zweig_liest_seine_eigene_quelle(index_html):
    assert ("takenAt:ph.takenAt};" in index_html
            and "_dataUrlToBlob(ph.dataUrl)" in index_html), (
        "Der Bild-Zweig des Plan-Uploads liest nicht mehr ph.dataUrl - dann ist "
        "der freie Name zurueck und v3.9.890 wirkt fuer Bild-Plaene wieder nie."
    )


def test_der_pdf_zweig_bleibt_wie_er_war(index_html):
    """GEGENPROBE: dort war `ev` von Anfang an richtig deklariert. Ein
    Suchen-und-Ersetzen ueber beide Zweige haette ihn kaputtgemacht."""
    assert "_dataUrlToBlob(ev.target.result)" in index_html, (
        "Der PDF-Zweig liest nicht mehr ev.target.result - dort war der Name "
        "korrekt, diese Reparatur durfte ihn nicht anfassen."
    )


# ══ 2 - Ort-Index ═══════════════════════════════════════════════════════════

def test_es_gibt_genau_eine_quelle_fuer_den_ortindex(index_html):
    code = nur_code(index_html)
    assert "function _ortIdxAus(geo){" in code, (
        "Der gemeinsame Helfer fehlt - dann baut jede Stelle den Ort-Index "
        "wieder selbst, und das ist eine Groesse mit zwei Rechnungen."
    )
    assert code.count("Object.keys(geo||{}).map(function(p){return {plz:p,") == 1, (
        "Der Ort-Index wird an mehr als einer Stelle aufgebaut."
    )


def test_beide_verbraucher_rufen_den_helfer(index_html):
    assert "var _ortIdx=_ortIdxAus(_geo);" in index_html, (
        "_dispoBuildInput baut den Index wieder selbst."
    )
    assert "_ortIdxAus(geoMap)).plz)" in index_html, (
        "Der Geo-Prefetch in ArbeitsscheinView liest den Index nicht - dann "
        "greift er wieder auf ein _built zu, das es dort nicht gibt, und der "
        "Fix aus v3.9.888 laeuft erneut kein einziges Mal."
    )


def test_kein_zugriff_auf_built_ausserhalb_des_dispo_panels(index_html):
    """Der Kern: `_built` darf nur dort vorkommen, wo es auch deklariert ist."""
    code = nur_code(index_html)
    i = code.find("var _built")
    assert i != -1, "_built-Deklaration nicht gefunden"
    davor = code[:i]
    assert "_built.ortIdx" not in davor, (
        "Es wird VOR der Deklaration auf _built.ortIdx zugegriffen - das ist "
        "ein freier Name in einer anderen Komponente."
    )


# ══ 3 - Selbsttest T-110 ════════════════════════════════════════════════════

def test_der_rls_selbsttest_liest_den_echten_benutzer(index_html):
    assert "const _cu=window._curUser();" in index_html, (
        "T-110 holt den Benutzer nicht mehr ueber window._curUser() - dann "
        "steht dort wieder ein freier Name, und der Riegel meldet fuer Monteure "
        "'exception' statt eines Ergebnisses."
    )
    assert "const mid=_cu&&_cu.monteurId;" in index_html, (
        "Die monteurId kommt nicht aus demselben Benutzer wie die Rolle."
    )


def test_der_alte_freie_name_ist_weg(index_html):
    code = nur_code(index_html)
    assert "const mid=_user&&_user.monteurId;" not in code, (
        "Der freie Name _user ist zurueck. Der Test steigt fuer jede andere "
        "Rolle vorher als 'skip' aus - der Ausfall faellt niemandem auf."
    )


# ══ 4 - HBarChart ═══════════════════════════════════════════════════════════

def test_der_balken_hat_eine_echte_ersatzfarbe(index_html):
    assert "background:it.color||V.ac," in index_html, (
        "Die Ersatzfarbe des Balkens ist keine Themenfarbe mehr."
    )


def test_die_geladene_waffe_ist_entladen(index_html):
    code = nur_code(index_html)
    assert "it.color||A," not in code, (
        "it.color||A ist zurueck - ein freier Name, UNGEFANGEN im Render der "
        "Startseite. Sobald die Farbe aus Daten kaeme: weisser Schirm."
    )


# ══ Umkehrprobe ═════════════════════════════════════════════════════════════

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    z1 = index_html.replace("_dataUrlToBlob(ph.dataUrl)",
                            "_dataUrlToBlob(ev.target.result)", 1)
    assert z1 != index_html, "Rueckbau 1 griff nicht"
    assert "_dataUrlToBlob(ph.dataUrl)" not in z1, (
        "Umkehrprobe: der Bild-Zweig-Riegel wuerde nicht anschlagen"
    )

    z2 = index_html.replace("_ortIdxAus(geoMap)).plz)",
                            "(_built&&_built.ortIdx)).plz)", 1)
    assert z2 != index_html, "Rueckbau 2 griff nicht"
    assert "_ortIdxAus(geoMap)).plz)" not in z2, (
        "Umkehrprobe: der Geo-Riegel wuerde nicht anschlagen"
    )

    z3 = index_html.replace("const mid=_cu&&_cu.monteurId;",
                            "const mid=_user&&_user.monteurId;", 1)
    assert z3 != index_html, "Rueckbau 3 griff nicht"
    assert "const mid=_user&&_user.monteurId;" in nur_code(z3), (
        "Umkehrprobe: der Selbsttest-Riegel wuerde nicht anschlagen"
    )

    z4 = index_html.replace("background:it.color||V.ac,", "background:it.color||A,", 1)
    assert z4 != index_html, "Rueckbau 4 griff nicht"
    assert "it.color||A," in nur_code(z4), (
        "Umkehrprobe: der HBarChart-Riegel wuerde nicht anschlagen"
    )
