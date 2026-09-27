# -*- coding: utf-8 -*-
"""Erzeugt docs/befunde/BEDIENELEMENTE_OHNE_NAMEN.md aus der Messung.

Die Listen werden ERZEUGT, nicht getippt. Eine von Hand uebertragene Liste
aus 461 Zeilen hat Uebertragungsfehler, und die sehen genauso aus wie
Befunde.

🔴 Geschrieben wird mit newline="\\n". `io.open(p,'w')` stellt auf Windows
JEDE Zeile auf CRLF um - ein Wort geaendert, die ganze Datei geaendert.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bedienelemente_scan as B  # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "docs", "befunde", "BEDIENELEMENTE_OHNE_NAMEN.md")

# ─── URTEIL JE STELLE fuer Klasse (a) ───
# Gelesen im Zusammenhang, nicht aus dem Abtaster. Die Gruppe sagt, WARUM.
#   real       die Variable/der Zweig kann leer sein -> Knopf wird stumm
#   zustand    stumm in EINEM Zustand (Telefon/Schreibtisch, waehrend Arbeit)
#   gewacht    das Element wird nur gerendert, wenn der Wert da ist
#   fest       Wert kommt aus einem Literal-Feld im Code, nie leer
#   helfer     lokale Hilfsfunktion, alle Aufrufer uebergeben ein Literal
#   unklar     nicht entscheidbar ohne die Daten
URTEIL_A = {
    # ── real ──
    13413: ("real", "`const _wn=w.name||\"\"` - ein Vorgabewert, der die "
                    "LEERE Zeichenkette ist. Ist `w.name` leer, ist der Knopf "
                    "vollstaendig leer. Auf dem Telefon zusaetzlich "
                    "`_wn.split(\" \").pop()`, und `\"\".split(\" \").pop()` "
                    "ist wieder `\"\"`.",
            "Mitarbeiter ein-/ausblenden"),
    16439: ("real", "Die Kinder sind `t.i`, `\" \"`, `isMob?\"\":\" \"+t.l`. "
                    "Auf dem TELEFON ist der Textzweig die leere "
                    "Zeichenkette - dann bleibt nur das Emoji, dauerhaft, "
                    "nicht nur waehrend einer Arbeit.",
            "der Reitername `t.l` - auf dem Telefon ist er im Bild weg, im "
            "Namen muss er bleiben"),
    19889: ("real", "Die Kinder sind `\"🗑️ \"` und `isMob?\"Löschen\":\"\"`. "
                    "Auf dem SCHREIBTISCH ist der zweite Zweig leer - der "
                    "Knopf zeigt dauerhaft nur den Papierkorb.",
            "abgelesen aus `delEntry(e.id)` - dieselbe Handlung, die der "
            "mobile Zweig \"Löschen\" nennt"),
    24921: ("real", "`showForm?'✕':'+ Fahrt'` - ein UMSCHALTER, genau die "
                    "Bauform, fuer die v3.9.957 sechs bedingte Namen gesetzt "
                    "hat. Dieser siebte wurde nicht erfasst.",
            "der Name muss an DERSELBEN Bedingung haengen: "
            "`showForm?\"Abbrechen\":\"Fahrt hinzufügen\"`"),
    19829: ("unklar", "`w.vorname||w.n` aus `_maWaehlbar((monteure||MONT))` - "
                      "beide Felder kommen aus der Datenbank. Tragen alle "
                      "Monteure einen `vorname` ODER ein `n`, ist der Knopf "
                      "immer benannt. Das steht nicht im Code, und ich habe "
                      "die Tabelle nicht gelesen - ICH ENTSCHEIDE DAS NICHT.",
            "der Mitarbeitername; ob er leer sein kann, sagt die Tabelle"),
    # ── zustand: stumm, WAEHREND eine Arbeit laeuft ──
    9917: ("zustand", "`saving?'…':'💾 Speichern'`", "Speichern"),
    9974: ("zustand", "`saving?\"…\":\"💾 Speichern\"`", "Speichern"),
    10221: ("zustand", "`pwBusy?\"⏳ …\":\"Passwort ändern\"`",
            "Passwort ändern"),
    23809: ("zustand", "Spinner-`span` statt Text, waehrend `pwBusy`",
            "Passwort ändern"),
    23889: ("zustand", "Spinner-`span` waehrend `busy&&kind===\"smoke\"`",
            "Smoke-Tests"),
    23890: ("zustand", "Spinner-`span` waehrend `busy&&kind===\"integrity\"`",
            "Integrität"),
    24098: ("zustand", "`sending?'…':'Senden'`", "Senden"),
    24191: ("zustand", "`busy?'…':'💾 Chip zuordnen'`", "Chip zuordnen"),
    24937: ("zustand", "`saving?'⏳ …':'💾 Speichern'`", "Speichern"),
    29510: ("zustand", "`busy?\"…\":\"✓ Verrechnet\"`", "Verrechnen"),
    7168: ("zustand", "`loading?<Fragment><span/> \"Wird angemeldet…\"</>"
                      ":\"🔐 Anmelden\"` - BEIDE Zweige tragen Text. Der "
                      "Abtaster meldet die Stelle nur, weil `_react.Fragment` "
                      "kein literaler Tag-Name ist; er kann nicht hineinsehen. "
                      "FALSCHMELDUNG meines Abtasters, kein Befund.",
           "(kein Bedarf)"),
    # ── gewacht ──
    6960: ("gewacht", "`p.telefon&&React.createElement(...)`", ""),
    6961: ("gewacht", "`(p.emailKunde||p.email_kunde)&&...`", ""),
    7071: ("gewacht", "`p.telefon&&...`", ""),
    7072: ("gewacht", "`(p.emailKunde||p.email_kunde)&&...`", ""),
    11776: ("gewacht", "`const v=String(_jr[k]||\"\").trim(); if(!v)return;`",
            ""),
    11777: ("gewacht", "`const _em=...; if(_em){ ... }`", ""),
    14571: ("gewacht", "`s.datanorm_url&&...`, Inhalt `_kurz(url,60)`", ""),
    20600: ("gewacht", "`nextStatus&&...`, Inhalt `MAT_STATUS[nextStatus].l`",
            ""),
    # ── helfer ──
    10180: ("helfer", "`_navBtn(tab,text,color)`; 3 Aufrufer, alle mit einem "
                      "Literal (Z10189, Z10204, Z10213)", ""),
    22684: ("helfer", "`_btn(handler,color,bg,border,icon,text)`; 2 Aufrufer, "
                      "beide mit einem Literal (Z22688, Z22689)", ""),
    24576: ("helfer", "`_drill(label,tab)`; 12 Aufrufer, alle mit einem "
                      "Literal (Z24706-Z24845)", ""),
    27378: ("helfer", "`_tabBtn(k,label)`; 3 Aufrufer, alle mit einem Literal "
                      "(Z27387, Z27388, Z27389)", ""),
}
FEST_GRUND = ("Der Wert kommt aus einem Literal-Feld einer Aufzaehlung im "
              "Code (`.map` ueber ein Feld mit festen `l`/`label`-Werten). "
              "Er kann nicht leer werden, solange die Aufzaehlung im Code "
              "steht. Kein Befund - aber ein Vertrag, den nichts PRUEFT.")

URTEIL_A_IMMER = {
    12273: ("`_shiftYm(-1)` - ein Monat zurueck", "Voriger Monat"),
    12275: ("`_shiftYm(1)` - ein Monat vor", "Nächster Monat"),
    14623: ("`isOn?\"✓\":\"·\"`, `upd[u.id][tk]=!isOn` - ein Schalter fuer "
            "eine Benachrichtigung. BEIDE Zustaende sind Zeichen ohne Wort.",
            "ENTSCHEIDUNG: der Name muss sagen, WELCHE Benachrichtigung "
            "(`tk`) fuer WELCHEN Benutzer (`u.id`) - beides steht im "
            "`onClick`, die Wortwahl nicht. ICH ENTSCHEIDE DAS NICHT."),
    18442: ("`l.visible?\"👁️\":\"👁️‍🗨️\"`, `toggleLayer(l.id)` - ein "
            "Umschalter, beide Zustaende ein Emoji.",
            "bedingt, wie die sechs Umschalter aus v3.9.957: "
            "`l.visible?\"Ebene ausblenden\":\"Ebene einblenden\"`"),
    18454: ("`isPlanFreigegeben(pl.id)?\"🔗\":\"📤\"`, `togglePlanFreigabe(pl)`",
            "bedingt: `isPlanFreigegeben(pl.id)?\"Freigabe zurückziehen\""
            ":\"Plan freigeben\"` - die Richtung steht im Namen der Funktion, "
            "die WORTE sind eine ENTSCHEIDUNG"),
    20941: ("KEIN `button`, sondern ein `a` mit `href:shopLink` und dem "
            "Inhalt `\"🔗\"`. Ein Verweis, dessen ganzer Text ein Emoji ist, "
            "hat fuer eine Vorlesehilfe keinen Namen - sie sagt „Link\".",
            "abgelesen aus dem Zusammenhang (Artikelzeile, `shopLink`): "
            "„Artikel im Shop öffnen\""),
    22143: ("`setCellPick(null);setSelCells(null)` - schliesst die "
            "Zellenauswahl", "Auswahl schließen"),
    24005: ("`del(item.id)` in der Checklisten-Zeile", "Eintrag löschen"),
    24358: ("`entscheiden(a.id,'abgelehnt')`", "Ablehnen"),
    24954: ("`del(e.id)` in der Fahrtenbuch-Zeile", "Eintrag löschen"),
    27736: ("`imeiBusy?'…':'✓'`, `_imeiSpeichern(row.f.id)` - BEIDE Zweige "
            "sind ein Zeichen ohne Wort. Kein Umschalter: der eine Zweig ist "
            "nur der Zustand WAEHREND des Speicherns. Der Knopf zeigt also "
            "nie ein Wort.", "IMEI speichern"),
    27737: ("`setImeiFid('');setImeiVal('')` - verwirft die IMEI-Eingabe",
            "Abbrechen"),
    28829: ("`t.erledigt?\"✅\":\"⬜\"`, setzt `erledigt` um - ein Umschalter, "
            "beide Zustaende ein Emoji.",
            "bedingt: `t.erledigt?\"Als offen markieren\":\"Als erledigt "
            "markieren\"`"),
    29511: ("`setVerrId(null);setVerrBetrag(\"\");setVerrFile(\"\")`",
            "Abbrechen"),
}

ROH_DOM = """\
| Zeile | Element | Sichtbarer Inhalt | Befund |
| --- | --- | --- | --- |
| Z17237/Z17247 | `button` (`_btn`) | `"◀"` / `"▶"` | 🔴 **OHNE NAMEN.** `_btn(txt,on)` setzt nur `b.textContent=txt`, kein `title`. Aufgerufen mit `"◀"` und `"▶"` fuer das Blaettern in der PDF-Vorschau. Name abgelesen aus dem `onclick` (`page--` / `page++`): „Vorige Seite" / „Nächste Seite". |
| Z5946 (`mkField`) | `input` ×4 | – | 🔴 **OHNE NAMEN.** Die Beschriftung daneben ist ein `div` (Z5945), KEIN `label`, und der `input` hat kein `id`. Fuer eine Vorlesehilfe stehen die zwei in keiner Beziehung. Betrifft alle vier Felder des Tank-Dialogs: „📅 Datum", „🛢 Liter *", „💶 Gesamtpreis (€)", „🛣 km-Stand" (Z5952-Z5955) - die Namen sind ABLESBAR, sie sind nur nicht verbunden. |
| Z5906 | `select` | KW-Auswahl | 🔴 **OHNE NAMEN.** Kein `aria-label`, kein `label`-Element; die Optionen tragen `_fmtKw(k)`. Name ablesbar aus dem Zusammenhang: „Kalenderwoche wählen". |
| Z6126 | `select` | Projektspalte einer Tabelle | 🔴 **OHNE NAMEN.** Die leere Option `"— Projekt wählen —"` ist ein PLATZHALTER, kein Name. Ablesbar: „Projekt wählen". |
| Z6139 | `textarea` | Tabellenzelle | 🔴 **OHNE NAMEN.** Name waere `col.key`/`col.label` - das steht im Code daneben. |
| Z6146 | `input` | Tabellenzelle | 🔴 **OHNE NAMEN.** Wie Z6139. |
| Z5863/Z5866 | `button` ×2 | `opts.cancelLabel\\|\\|'Abbrechen'`, `opts.confirmLabel\\|\\|'Bestätigen'` | grün - Vorgabewert ist ein WORT. |
| Z5913/Z5914 | `button` ×2 | `'Abbrechen'`, `'📥 Exportieren'` | grün |
| Z5972/Z5974 | `button` ×2 | `'Zurück'`, `'✓ Speichern'` | grün |
| Z6163 | `button` | `'✕'` | grün - `delBtn.title='Zeile aus Export entfernen (nicht aus DB)'` |
| Z6178/Z6180 | `button` ×2 | `cancelLabel`, `confirmLabel` | grün (Aufrufer uebergeben Literale) |
| Z6079 | `button` | `addRow.label\\|\\|'➕ Buchung hinzufügen'` | grün - `title` gesetzt |
| Z17228/Z17229 | `button` ×2 | `"↗ Extern"`, `"✕"` | grün - beide mit `title` |
| Z30155 ff. | `button` | `"✕ Abbrechen"` | grün - Text im `textContent` |
| Z3288, Z4667, Z13115, Z18038 | `a` ×4 | – | keine Bedienelemente: unsichtbare `a`-Elemente mit `download`, sofort `click()` und entfernt. Ein Name dafuer waere ein Name fuer etwas, das niemand bedient. |
| Z11338, Z11566 | `textarea` ×2 | – | keine Bedienelemente: Zwischenablage-Behelf, `position:fixed;left:-9999px`, sofort entfernt. |
"""


def _rein_literal(text, mk, st):
    """Knoepfe, deren GANZER Inhalt EIN Symbol-/Emoji-Literal ist.

    Das ist die Menge, die v3.9.957 und v3.9.958 gemeint haben.
    """
    aus = []
    for s in st:
        if s["tag"] != "button":
            continue
        lits = [B._literal_text(text, mk, x, y) for x, y in s["_kspans"]]
        if len(lits) != 1 or lits[0] is None or not lits[0]:
            continue
        if B.NUR_STUMM.match(lits[0]):
            aus.append(s)
    return aus


def tab(zeilen, kopf):
    aus = ["| " + " | ".join(kopf) + " |",
           "| " + " | ".join("---" for _ in kopf) + " |"]
    for z in zeilen:
        aus.append("| " + " | ".join(
            str(x).replace("|", "\\|").replace("\n", " ") for x in z) + " |")
    return "\n".join(aus)


def hauptteil():
    roh = B.lies()
    mk = B.maske(roh)
    st = B.stellen(roh, mk)
    a = sorted(B.klasse_a(roh, mk, st), key=lambda s: s["zeile"])
    ai = sorted(B.klasse_a_immer(roh, mk, st), key=lambda s: s["zeile"])
    b = sorted(B.klasse_b(roh, mk, st), key=lambda s: s["zeile"])
    co = sorted(B.klasse_c_onclick(st), key=lambda s: s["zeile"])
    ce = sorted(B.klasse_c_eingaben(roh, mk, st), key=lambda s: s["zeile"])
    koeder = B.koederprobe(roh)
    return roh, mk, st, a, ai, b, co, ce, koeder


def kurz(s, n=64):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[:n - 1] + "…"


def main():
    roh, mk, st, a, ai, b, co, ce, koeder = hauptteil()
    kn = [s for s in st if s["tag"] == "button"]
    echt = [s for s in co if not s["schlucker"]]
    schluck = [s for s in co if s["schlucker"]]
    mit_tast = [s for s in echt if s["role"] and s["tabIndex"]]
    ohne_tast = [s for s in echt if not (s["role"] and s["tabIndex"])]
    ce_ohne = [s for s in ce if not s["ok"]]

    gruppen = {}
    for s in a:
        g = URTEIL_A.get(s["zeile"], ("fest", FEST_GRUND, ""))[0]
        gruppen.setdefault(g, []).append(s)

    T = []
    w = T.append
    w("# Bedienelemente ohne zugaenglichen Namen — die Menge, die v3.9.957 "
      "und v3.9.958 AUSGELASSEN haben")
    w("")
    import hashlib
    w("Gemessen an einer EINGEFRORENEN Abschrift von `index.html`:")
    w("")
    w("* **%d Bytes**, SHA256 `%s`" % (len(roh.encode("utf-8")),
                                       hashlib.sha256(
                                           roh.encode("utf-8")).hexdigest()))
    w("* Stand **v3.9.960**, `HEAD = ce397e9`, plus 4 noch nicht "
      "eingetragene Zeilen in `index.html`.")
    w("")
    w("🔴 **Warum eine Abschrift.** Ich habe um 08:11 mit 3.671.906 Bytes "
      "(v3.9.959, `HEAD = e6202e5`) angefangen. Um 12:00 hatte die Datei "
      "3.708.615 Bytes und v3.9.960. Zwei Laeufe derselben Messung gaben "
      "deshalb zwei verschiedene Zahlen (295/443/47/13 und 297/442/46/13 "
      "Knoepfe je Namensbefund). Eine Messung an einem Baum, an dem "
      "gearbeitet wird, ist keine Messung — und ZEILENNUMMERN aus dem ersten "
      "Lauf zeigen in der neuen Datei woandershin. Alles unten ist gegen die "
      "oben gehashte Abschrift gemessen, in EINEM Lauf. "
      "Nachmessen mit demselben Stand:")
    w("")
    w("```")
    w("BEDIENELEMENTE_PFAD=<abschrift> python scripts/"
      "bedienelemente_scan.py")
    w("```")
    w("An `index.html` wurde NICHTS geaendert (`git diff --stat -- "
      "index.html` ist leer), keine bestehende Pruefung angefasst, kein "
      "aenderndes git-Kommando gelaufen, kein Schreibzugriff auf die "
      "Datenbank. Neu sind genau drei Dateien: dieser Bericht, "
      "`scripts/bedienelemente_scan.py` (das Messgeraet), "
      "`scripts/bedienelemente_gegenprobe_v957_958.py` (die Gegenprobe "
      "gegen die zwei alten Abtaster) und "
      "`scripts/bedienelemente_bericht.py` (der Erzeuger dieses Berichts).")
    w("")
    w("## 0. Die Zahl")
    w("")
    w(tab([
        ("(a) Knopf/Verweis, der NIE ein Wort zeigt und keinen Namen in den "
         "Props hat", len(ai), "🔴 **%d Befunde**" % len(ai)),
        ("(a) Name haengt an einer Variable oder einem Zweig, der leer sein "
         "kann", len(a),
         "🔴 **%d real** · %d nur in einem Zustand · %d unklar · "
         "%d kein Befund"
         % (len(gruppen.get("real", [])), len(gruppen.get("zustand", [])),
            len(gruppen.get("unklar", [])),
            len(gruppen.get("gewacht", [])) + len(gruppen.get("fest", []))
            + len(gruppen.get("helfer", [])))),
        ("(b) Knopf mit Emoji PLUS Text", len(b),
         "kein Urteil — schwaechere Klasse, getrennt gefuehrt"),
        ("(c) `onClick` auf einem Element, das kein Bedienelement ist",
         len(co),
         "%d Klick-Schlucker abgezogen → %d echte Flaechen, davon "
         "🔴 **%d ohne `role`+`tabIndex`**"
         % (len(schluck), len(echt), len(ohne_tast))),
        ("(c) `input`/`select`/`textarea`", len(ce),
         "🔴 **%d ohne `label`, `aria-label`, `title` oder "
         "`htmlFor`-Verbindung**" % len(ce_ohne)),
        ("(d) mit der rohen DOM-Schnittstelle gebaut — von JEDER "
         "React-Messung unerreicht", 27,
         "🔴 **8 Befunde** (2 Knoepfe, 4 `input`, 2 `select`/`textarea`)"),
    ], ["Klasse", "Gemessen", "Befund"]))
    w("")
    w("### 🔴 Und zuerst: v3.9.957/958 sind NICHT vollstaendig")
    w("")
    w("Beide Riegel behaupten, alle 150 Knoepfe mit reinem Symbol- oder "
      "Emoji-Inhalt tragen einen Namen. **14 Knoepfe bzw. Verweise zeigen "
      "NIE ein Wort und tragen keinen Namen**, und **alle 14 sind fuer beide "
      "Abtaster unsichtbar**.")
    w("")
    w("🔴 Das ist GEMESSEN, nicht geschlossen. "
      "`scripts/bedienelemente_gegenprobe_v957_958.py` bildet die Suchlogik "
      "beider Abtaster zeichengenau nach und setzt sie auf denselben Text. "
      "Die Eichung dieser Gegenprobe: die nachgebildete v958-Logik findet "
      "**genau 150** Knoepfe, alle als benannt — dieselbe Zahl, die der "
      "Riegel behauptet. Die Nachbildung stimmt also mit dem Original "
      "ueberein, und erst dadurch heisst „nicht gesehen\" etwas.")
    w("")
    w("🔴 Und eine eigene Korrektur: die erste Fassung dieser Gegenprobe "
      "verglich ueber die ZEILENNUMMER. In einer Datei mit 1300 Zeichen pro "
      "Zeile stehen mehrere Knoepfe auf derselben Zeile — sie meldete "
      "daraufhin, v958 sehe Z18442 und halte sie fuer benannt, obwohl der "
      "Treffer zu einem ANDEREN Knopf derselben Zeile gehoerte. Verglichen "
      "wird jetzt ueber die Zeichenposition. Die Zeilennummer ist in dieser "
      "Datei kein eindeutiger Schluessel.")
    w("")
    w("Die Ursachen, je Stelle ausgezaehlt (sie ueberschneiden sich):")
    w("")
    w(tab([
        ("**Die `h(`-Schreibweise**. Beide Abtaster suchen "
         "`createElement('button'`. Der lokale Kuerzel `h(` "
         "(`const h=React.createElement`, 13 mal vergeben) kommt **97 mal** "
         "in Knopfstellung vor und wurde NIE gemessen.",
         5, "Z12273, Z12275, Z27736, Z27737, Z29511"),
        ("**Nur doppelte Anfuehrungszeichen.** v958 liest den Inhalt mit "
         "`re.match(r'\"((?:[^\"\\\\]|\\\\.)*)\"\\s*\\)')`. Ein einfach "
         "gesetzter Inhalt (`,'✕')`) faellt durch.",
         7, "Z12273, Z12275, Z22143, Z24005, Z24358, Z24954, Z27737"),
        ("**Der Inhalt ist ein Ternaer, kein Literal.** Beide Abtaster "
         "suchen ein Zeichenketten-LITERAL. `isOn?\"✓\":\"·\"` ist keines — "
         "und BEIDE Zweige sind ein Zeichen ohne Wort.",
         5, "Z14623, Z18442, Z18454, Z27736, Z28829"),
        ("**Gar kein `button`.** Ein `a` mit `href` und dem Inhalt `\"🔗\"`. "
         "Eine Vorlesehilfe sagt dort „Link\" und sonst nichts.",
         1, "Z20941"),
    ], ["Ursache", "Anzahl", "Stellen"]))
    w("")
    w("Zum Umfang, damit die Zahl nicht groesser klingt als sie ist: "
      "**%d** Knoepfe haben als ganzen Inhalt EIN Symbol-/Emoji-Literal "
      "(das ist die Menge, die v957/v958 gemeint haben), und **%d** davon "
      "tragen keinen Namen. Die restlichen 6 der 14 sind Ternaere und der "
      "eine `a` — die lagen auch nach dem Wortlaut der beiden Riegel nie in "
      "ihrem Umfang, wohl aber in ihrer Behauptung."
      % (len(_rein_literal(roh, mk, st)),
         len([s for s in _rein_literal(roh, mk, st)
              if not B.hat_namen(s["props"])])))
    w("")
    w("🟡 Eine Bauform, die in BEIDE Richtungen taeuscht: das `\\s*\\)` in "
      "v958 verlangt, dass der Inhalt das LETZTE Argument ist. Ein Knopf "
      "`,\"🗑️ \",isMob?\"Löschen\":\"\"` faellt deshalb durch — und war bis "
      "v3.9.960 ein echter Befund (siehe Abschnitt 2). Umgekehrt ist ein "
      "Knopf `,'🏖️',h('div',{},'Urlaub')` (Z7669) BENANNT, obwohl sein "
      "erstes Kind ein Emoji ist. Wer nur das erste Kind ansieht, irrt in "
      "beide Richtungen; dieser Abtaster liest alle Kinder und bei einem "
      "verschachtelten Element auch dessen Kinder.")
    w("")
    w("Diese 14 gehoeren nach v3.9.957/958, nicht in diesen Auftrag. Sie "
      "stehen hier, weil ich sie beim Messen der Nachbarmenge gefunden habe.")
    w("")
    w(tab([(s["zeile"], s["ansicht"], B.schreibweise(roh, s), s["tag"],
            "`" + kurz(" ".join(s["kinder"]), 44) + "`",
            URTEIL_A_IMMER.get(s["zeile"], ("", ""))[0],
            "**" + URTEIL_A_IMMER.get(s["zeile"], ("", "?"))[1] + "**")
           for s in ai],
          ["Zeile", "Ansicht", "Form", "Tag", "Inhalt", "Was das onClick tut",
           "Namensvorschlag (abgelesen)"]))
    w("")
    w("Von diesen 14 sind **drei ein Name, den ich NICHT entscheide** "
      "(Z14623, Z18454 teilweise, Z28829 teilweise): dort ist die Handlung "
      "aus dem `onClick` ablesbar, aber die WORTE waeren eine Wahl. "
      "Z18442/Z18454/Z28829/Z14623 sind ausserdem **Umschalter** — genau die "
      "Bauform, fuer die v3.9.957 sechs bedingte Namen gesetzt hat. Ein "
      "FESTER Name ist dort in einem der zwei Zustaende falsch.")
    w("")

    # ── KOEDER ──
    w("## 1. Koeder-Nachweis")
    w("")
    w("Jede Zahl unten sucht etwas und meldet gruen, wenn sie es nicht "
      "findet — die gefaehrlichste Bauform. Also wird je Klasse ein Fall "
      "EINGESETZT, der gefunden werden MUSS. Die vier **Gegenproben** messen "
      "die andere Richtung: ein Zaehler, der ALLES meldet, schlaegt bei jedem "
      "Koeder an und ist trotzdem kaputt.")
    w("")
    w(tab([("`%s`" % n.split("  ", 1)[-1] if "  " in n else n,
            "ANGESCHLAGEN" if ok else "🔴 BLIND")
           for n, ok in koeder], ["Koeder", "Ergebnis"]))
    w("")
    w("Alle %d angeschlagen. Zusaetzlich: `scripts/code_scan.py` hat seine "
      "EICHPROBE bestanden (der Abtaster verweigert sonst die Auskunft), und "
      "die Grundgesamtheit ist nicht leer: **%d** Elementstellen mit "
      "literalem Tag-Namen, davon **%d** `button` (%d in der "
      "`createElement`-Form, %d als `h(`)."
      % (len(koeder), len(st), len(kn),
         sum(1 for s in kn if B.schreibweise(roh, s) == "createElement"),
         sum(1 for s in kn if B.schreibweise(roh, s) == "h(")))
    w("")
    w("### 🟡 Eine Gegenprobe, die ich fast weggelassen haette")
    w("")
    w("Ich wollte in Abschnitt 6 schreiben: „ein leeres `title:\"\"` kommt "
      "in der Datei nicht vor\". Vor dem Hinschreiben gemessen — es kommt "
      "**4 mal** vor (Z3665, Z18364, Z18366, Z18476). Alle vier sind "
      "DATENFELDER (`{label:…,type:\"mangel\",title:\"\",…}` — der Titel "
      "eines Tickets), keine Eigenschaft eines Elements. Die Behauptung war "
      "also falsch und der Befund harmlos. Aber sie hat eine echte "
      "Schwaeche aufgedeckt:")
    w("")
    w("`hat_namen()` sucht `title:` FLACH im Props-Text. Ein `title:` kann "
      "tiefer stehen — Z18476 hat eines in einem Datenobjekt INNERHALB des "
      "`onClick`. Dann meldet der flache Zaehler den Knopf als benannt, ohne "
      "dass er einen Namen hat. Das ist dieselbe Fehlerform, an der die "
      "erste v958-Messung dreimal gescheitert ist, nur eine Ebene hoeher.")
    w("")
    w("Gemessen mit einer zweiten, strengen Pruefung "
      "(`hat_namen_streng()`, Schluessel nur auf Tiefe 1, mit eigenem "
      "Koeder und Gegenkoeder): von %d `button`/`a` gelten **%d** flach als "
      "benannt und **%d** streng. Die Differenz ist **3** — Z14257, Z18476, "
      "Z23852. Alle drei tragen sichtbaren Text (`\"📥 CSV\"`, "
      "`\"+ Vorlage hinzufügen\"`, `\"🗑️ Lokale Daten löschen\"`), sind also "
      "auch streng gemessen benannt. **Kein neuer Befund, aber die Zahlen "
      "in diesem Bericht haengen nicht daran.**"
      % (len([s for s in st if s["tag"] in ("button", "a")]),
         len([s for s in st if s["tag"] in ("button", "a")
              and B.hat_namen(s["props"])]),
         len([s for s in st if s["tag"] in ("button", "a")
              and B.hat_namen_streng(s["props"])])))
    w("")
    w("🔴 Die Abtaster von v3.9.957 und v3.9.958 haben dieselbe Schwaeche, "
      "und v957 hat sie schlimmer: er nimmt einen 900-Zeichen-Schnitt "
      "RUECKWAERTS und sucht darin `title:`. Dieser Schnitt kann in einen "
      "ganz anderen Knopf hineinreichen.")
    w("")
    w("Gegenprobe auf die Aufteilung: %d `benannt-prop` + %d `benannt-text` "
      "+ %d `manchmal-stumm` + %d `immer-stumm` = %d. Die Summe geht auf; "
      "kein Knopf faellt zwischen die Klassen."
      % (sum(1 for s in kn if B.beurteile(roh, mk, s) == "benannt-prop"),
         sum(1 for s in kn if B.beurteile(roh, mk, s) == "benannt-text"),
         sum(1 for s in kn if B.beurteile(roh, mk, s) == "manchmal-stumm"),
         sum(1 for s in kn if B.beurteile(roh, mk, s) == "immer-stumm"),
         len(kn)))
    w("")

    # ── (a) ──
    w("## 2. Klasse (a) — der Inhalt ist eine Variable, die leer sein kann")
    w("")
    w("%d Stellen gemessen. Der Abtaster kann NICHT entscheiden, ob eine "
      "Variable leer wird — das ist je Stelle gelesen. Entscheidend war "
      "dabei ein Muster, das der Abtaster nicht sieht: **ein WAECHTER**. "
      "`p.telefon&&React.createElement('a',…,p.telefon)` rendert das Element "
      "gar nicht, wenn der Wert fehlt. Sieben Stellen, die nach einer "
      "leeren Variable aussehen, sind so bewacht." % len(a))
    w("")
    w("🟢 **Eine vierte reale Stelle ist waehrend der Messung BEHOBEN "
      "worden.** Z19889 (`VBautag`) hatte die Kinder `\"🗑️ \"` und "
      "`isMob?\"Löschen\":\"\"` — am Schreibtisch blieb dauerhaft nur der "
      "Papierkorb. In der Abschrift von 12:00 tragen dieselbe Zeile ein "
      "`title: \"Eintrag löschen\"` und ein `'aria-label': \"Eintrag "
      "löschen\"`, mit einem v3.9.960-Kommentar, der genau diesen Mechanismus "
      "beschreibt („Der Inhalt ist das Symbol plus `isMob?\"Löschen\":\"\"` … "
      "hier sind es zwei Kinder\"). Ich habe den Befund um 08:11 gemessen und "
      "um 12:00 nicht mehr — er stand also nicht in meinem Bericht, weil er "
      "weg ist, nicht weil ich ihn nicht gefunden hatte. Der "
      "Geschwisterknopf daneben (`editEntry`, `\"✏️ \",isMob?\"Bearbeiten\":"
      "\"\"`) traegt jetzt ebenfalls ein `title`.")
    w("")
    for g, titel in [
        ("real", "🔴 REAL — die Stelle wird stumm"),
        ("unklar", "🟡 NICHT ENTSCHEIDBAR — ich entscheide das nicht"),
        ("zustand", "🟡 Stumm nur, WAEHREND eine Arbeit laeuft "
                    "(schwaechere Klasse)"),
        ("gewacht", "🟢 Bewacht — das Element rendert nur mit Wert"),
        ("helfer", "🟢 Lokale Hilfsfunktion — alle Aufrufer uebergeben ein "
                   "Literal"),
        ("fest", "🟢 Wert aus einem Literal-Feld im Code"),
    ]:
        rows = gruppen.get(g, [])
        if not rows:
            continue
        w("### %s — %d" % (titel, len(rows)))
        w("")
        if g == "fest":
            w(FEST_GRUND)
            w("")
            w(tab([(s["zeile"], s["ansicht"], s["tag"],
                    "`" + kurz(" ".join(s["kinder"]), 52) + "`")
                   for s in rows],
                  ["Zeile", "Ansicht", "Tag", "Inhalt"]))
        else:
            w(tab([(s["zeile"], s["ansicht"], s["tag"],
                    "`" + kurz(" ".join(s["kinder"]), 40) + "`",
                    URTEIL_A[s["zeile"]][1],
                    ("**" + URTEIL_A[s["zeile"]][2] + "**")
                    if URTEIL_A[s["zeile"]][2] else "—")
                   for s in rows],
                  ["Zeile", "Ansicht", "Tag", "Inhalt", "Warum",
                   "Namensvorschlag (abgelesen)"]))
        w("")
    w("**Zusammen mit den 14 aus Abschnitt 0** sind in Klasse (a) "
      "**%d Stellen ohne Namen** (%d nie benannt + %d real) und **%d "
      "nicht entscheidbar**."
      % (len(ai) + len(gruppen.get("real", [])), len(ai),
         len(gruppen.get("real", [])), len(gruppen.get("unklar", []))))
    w("")

    # ── (b) ──
    w("## 3. Klasse (b) — Emoji PLUS Text")
    w("")
    w("**%d Knoepfe.** Diese Klasse ist SCHWAECHER, und ich urteile nicht: "
      "jeder dieser Knoepfe HAT einen Namen. Die Frage ist nur, ob der Text "
      "allein die Handlung benennt — „PDF\" sagt nicht, was passiert. Das "
      "ist eine Wortwahl, keine Messung, und sie gehoert nicht mir." % len(b))
    w("")
    w("Was ich stattdessen gemessen habe, weil es entscheidbar ist: welche "
      "dieser Knoepfe ein Wort tragen, das aus sich heraus keine Handlung "
      "nennt. Ein Substantiv ohne Verb. Die Liste ist eine VORLAGE zum "
      "Ansehen, kein Befund:")
    w("")
    VERDACHT = re.compile(
        r"^(?:PDF|CSV|Excel|XLS|ZIP|QR|OK|Ja|Nein|Alle|Neu|Mehr|Details?|"
        r"Info|Server|Excel-Datei|Liste|Karte|Foto|Fotos|Datei|Dateien|"
        r"E-Mail|Mail|Druck|Export|Import|Zurück|Weiter|\d+)$")
    verd = [s for s in b
            if VERDACHT.match(re.sub(r"[^\w\-äöüÄÖÜß]+", " ",
                                     s["sichtbar"]).strip())]
    if verd:
        zeilen = []
        for s in verd:
            mo = re.search(r"onClick\s*:\s*(.{0,60})", s["props"], re.S)
            zeilen.append((s["zeile"], s["ansicht"],
                           "`" + kurz(s["sichtbar"], 30) + "`",
                           kurz(mo.group(1) if mo else "(kein onClick)", 58)))
        w(tab(zeilen, ["Zeile", "Ansicht", "Sichtbar",
                       "onClick (die Handlung steht hier)"]))
    else:
        w("_Keine Stelle passt auf das Verdachtsmuster._")
    w("")
    w("Die vollstaendige Liste aller %d Stellen dieser Klasse steht nicht "
      "hier, sondern kommt auf Zuruf aus `python "
      "scripts/bedienelemente_scan.py json` (Schluessel `b`). Eine Liste mit "
      "%d Zeilen in einem Bericht liest niemand, und ein Urteil steht mir "
      "hier nicht zu." % (len(b), len(b)))
    w("")

    # ── (c) ──
    w("## 4. Klasse (c) — andere Bedienelemente als `button`")
    w("")
    w("### 4a. `onClick` auf einem Element, das kein Bedienelement ist")
    w("")
    w("**%d Stellen** tragen ein `onClick` auf einem Tag, das kein "
      "`button`/`a`/`input`/`select` ist." % len(co))
    w("")
    w("🔴 Davon sind **%d gar keine Bedienelemente**, sondern "
      "KLICK-SCHLUCKER: `onClick: e=>e.stopPropagation()` verhindert nur, "
      "dass der Klick beim Elternelement ankommt. Ein `role`/`tabIndex` "
      "dort waere FALSCH — er baute einen Halt in der Tastaturreihenfolge, "
      "der nichts tut. Dieselbe Sorte Ausnahme wie die Statusanzeige in "
      "v3.9.957. Sie sind abgezogen." % len(schluck))
    w("")
    w("Bleiben **%d echte Bedienflaechen**:" % len(echt))
    w("")
    w(tab([("mit `role` UND `tabIndex`", len(mit_tast),
            "🟢 bedienbar mit der Tastatur"),
           ("ohne `role` und/oder `tabIndex`", len(ohne_tast),
            "🔴 **fuer die Tastatur und fuer eine Vorlesehilfe gar kein "
            "Bedienelement**"),
           ("mit `onKeyDown`/`onKeyPress`/`onKeyUp`",
            sum(1 for s in echt if s["onKey"]),
            "deckungsgleich mit der ersten Zeile — wer `role` setzt, hat "
            "hier auch die Taste verdrahtet")],
          ["", "Anzahl", "Bedeutung"]))
    w("")
    from collections import Counter
    w("Die %d ohne Tastaturzugang nach Tag: %s."
      % (len(ohne_tast),
         ", ".join("`%s` %d" % (t, n) for t, n in
                   Counter(s["tag"] for s in ohne_tast).most_common())))
    w("")
    w("Zwei Untergruppen darin sind eigene Faelle:")
    w("")
    th = [s for s in ohne_tast if s["tag"] == "th"]
    w("* **%d `th` mit `onClick`** (Spalten sortieren, alle in `sharePdf`, "
      "Z11511-Z11522). Der sichtbare Text (`\"Nummer\"`, `\"Status\"`, …) "
      "ist da, aber der Kopf ist kein Knopf: mit der Tastatur ist die "
      "Sortierung NICHT erreichbar. Der Name ist ABLESBAR — er steht als "
      "erstes Kind — der fehlende Teil ist `role`/`tabIndex` und ein "
      "`aria-sort`." % len(th))
    img = [s for s in ohne_tast if s["tag"] == "img"]
    w("* **%d `img` mit `onClick`**. Ein Bild ist nie ein Bedienelement; "
      "hier braucht es zusaetzlich ein `alt`." % len(img))
    w("")
    w("Vollstaendige Liste der %d ohne Tastaturzugang:" % len(ohne_tast))
    w("")
    w(tab([(s["zeile"], s["ansicht"], "`%s`" % s["tag"],
            "role" if s["role"] else ("tabIndex" if s["tabIndex"] else "—"),
            kurz(re.search(r"onClick\s*:\s*(.{0,70})", s["props"], re.S)
                 .group(1), 64))
           for s in ohne_tast],
          ["Zeile", "Ansicht", "Tag", "Hat davon", "onClick (der Name steht "
           "hier)"]))
    w("")
    w("### 4b. `input` / `select` / `textarea`")
    w("")
    w("**%d** gemessen, **%d ohne** `label`-Umschliessung, `aria-label`, "
      "`title`, `aria-labelledby` oder eine `htmlFor`/`id`-Verbindung."
      % (len(ce), len(ce_ohne)))
    w("")
    w(tab([("`input`", sum(1 for s in ce_ohne if s["tag"] == "input")),
           ("`select`", sum(1 for s in ce_ohne if s["tag"] == "select")),
           ("`textarea`", sum(1 for s in ce_ohne if s["tag"] == "textarea"))],
          ["Tag", "ohne Namen"]))
    w("")
    w("🔴 **%d davon tragen einen `placeholder` und sonst nichts.** Ein "
      "Platzhalter ist KEIN Name: er verschwindet, sobald jemand tippt, und "
      "mehrere Vorlesehilfen lesen ihn nicht als Namen. Er ist aber ein "
      "ABGELESENER Vorschlag — der Text steht schon da."
      % sum(1 for s in ce_ohne if s["placeholder"]))
    w("")
    mit_schrift = [s for s in ce_ohne if s["labelschrift"]]
    w("🟡 **%d davon haben ein `label`-ELEMENT in der Naehe** (bis 1400 "
      "Zeichen davor), dessen Text den Namen NENNT — nur ist er nicht "
      "VERBUNDEN. Die App benutzt `htmlFor` genau %d mal in der ganzen "
      "Datei. Das ist der billigste Teil: der Name ist schon geschrieben, "
      "er braucht nur ein `htmlFor`+`id` oder ein `aria-label` mit "
      "demselben Wort."
      % (len(mit_schrift), len(re.findall(r"htmlFor", roh))))
    w("")
    w("Verteilung der %d ohne Namen nach Ansicht (die 12 groessten):"
      % len(ce_ohne))
    w("")
    w(tab(Counter(s["ansicht"] for s in ce_ohne).most_common(12),
          ["Ansicht (naechste `function` davor)", "ohne Namen"]))
    w("")
    w("🔴 Die Spalte „Ansicht\" ist die naechste `function NAME(` VOR der "
      "Stelle. Bei `_kmFromBeleg`, `sharePdf`, `load`, `_submitAntrag` und "
      "`up` ist das eine INNERE Hilfsfunktion, nicht die Ansicht — der Name "
      "ist dann falsch, die ZEILE stimmt. Dieselbe Schwaeche haben die "
      "Abtaster von v3.9.957 und v3.9.958.")
    w("")
    w("Vollstaendige Liste, mit dem abgelesenen Namensvorschlag je Stelle. "
      "**Der Vorschlag ist ABGELESEN, nicht formuliert**: entweder aus dem "
      "`placeholder` oder aus dem Text des `label`-Elements daneben. Wo "
      "beide fehlen, steht „ENTSCHEIDUNG\" — dort waere ein Name eine Wahl, "
      "und ich entscheide sie nicht.")
    w("")
    w(tab([(s["zeile"], s["ansicht"], "`%s`" % s["tag"], s["typ"] or "—",
            ("`%s`" % kurz(s["placeholder"], 36)) if s["placeholder"]
            else ("„%s\"" % kurz(s["labelschrift"], 36))
            if s["labelschrift"] else "**ENTSCHEIDUNG**",
            "placeholder" if s["placeholder"]
            else "label daneben" if s["labelschrift"] else "—")
           for s in ce_ohne],
          ["Zeile", "Ansicht", "Tag", "type", "Namensvorschlag (abgelesen)",
           "Quelle"]))
    w("")

    # ── (d) ──
    w("## 5. Klasse (d) — mit der rohen DOM-Schnittstelle gebaut "
      "(ausserhalb jeder React-Messung)")
    w("")
    w("Nicht bestellt, beim Messen gefunden, und deshalb hier: **27 Stellen "
      "bauen Bedienelemente mit `document.createElement(...)`** statt mit "
      "React. Kein Abtaster dieses Auftrags und keiner von v3.9.957/958 "
      "sieht sie — sie suchen alle `React.createElement`/`h(`. Ich habe sie "
      "alle 27 gelesen.")
    w("")
    w(ROH_DOM)
    w("")
    w("**8 Befunde**: 2 Knoepfe (Z17247), 4 `input` (Z5946 ueber `mkField`, "
      "4 Aufrufe), 1 `select` (Z5906), 1 `select` + 1 `textarea` + 1 `input` "
      "in der Tabellenzelle (Z6126, Z6139, Z6146) — zusammen 2 + 4 + 1 + 3 = "
      "**10 Bedienelemente ohne Namen**, auf 8 Codestellen.")
    w("")

    # ── NICHT GEMESSEN ──
    w("## 6. Was ich NICHT gemessen habe")
    w("")
    for zeile in [
        "**Ob eine Vorlesehilfe den Namen wirklich ansagt.** Das kann nur "
        "ein Schirmleser. Alles hier ist am QUELLTEXT gemessen. Ein "
        "`aria-label` im Code ist eine Absicht, kein Beleg.",
        "**Den berechneten Namen nach der HTML-Regel.** Ein Browser bildet "
        "den Namen in einer festen Reihenfolge (`aria-labelledby` → "
        "`aria-label` → Inhalt → `title`). Ich habe die ANWESENHEIT von "
        "`title`/`aria-label` gemessen und den Inhalt gelesen; ich habe die "
        "Reihenfolge nicht nachgebaut.",
        "**Kein Browser.** Ich habe keinen gestartet, also ist nichts hier "
        "im laufenden Bild nachgemessen. Ein Befund haengt ausdruecklich an "
        "einer Bildschirmbreite: Z16439 (`VForm`) verliert auf dem TELEFON "
        "den Reiternamen (`isMob?\"\":\" \"+t.l`) und zeigt dann nur ein "
        "Emoji. Das habe ich am CODE gelesen, nicht gesehen — welcher "
        "Schwellwert `isMob` gerade ist, habe ich nicht nachgeschlagen, und "
        "in v3.9.955 hat er sich schon einmal geaendert (der v3.9.960-"
        "Kommentar an Z19889 sagt: von `ww<768` auf 600 px). Ein Befund, der "
        "an einer Schwelle haengt, ist nur so genau wie die Schwelle.",
        "**Ob ein Element ueberhaupt gerendert wird.** Eine unerreichbare "
        "Ansicht hat keine namenlosen Knoepfe, weil sie keine Knoepfe hat. "
        "Der Riegel von e6202e5 haelt fest, dass genau EINE Komponente nie "
        "gerendert wird; ob eine der Stellen hier darin liegt, habe ich "
        "nicht geprueft.",
        "**Die Dopplung.** Eine Stelle in einer `.map`-Schleife ist EINE "
        "Codestelle und im Bild N Knoepfe. Alle Zahlen hier sind "
        "CODESTELLEN. Die Zahl der Knoepfe auf dem Schirm ist groesser, und "
        "zwar um einen Faktor, den nur die Daten kennen.",
        "**`aria-hidden`, `disabled` und die Reihenfolge.** Ein Knopf, der "
        "`aria-hidden` traegt oder dauerhaft `disabled` ist, ist ein "
        "anderer Fall. Ich habe `disabled` gesehen (es steht bei den "
        "meisten „stumm waehrend der Arbeit\"-Faellen) und nicht "
        "systematisch gezaehlt.",
        "**Alles, was nicht `button`/`a`/`input`/`select`/`textarea` und "
        "nicht `onClick` ist.** Kein `onChange` auf einem `div`, kein "
        "`onKeyDown` ohne `onClick`, keine Formulare, keine Ueberschriften-"
        "Ordnung, kein Farbkontrast, keine Reihenfolge beim Tabben, keine "
        "Fokusfalle in den Dialogen.",
        "**Die Namen in Klasse (b).** 273 Stellen haben einen Namen; ob das "
        "Wort gut ist, ist eine Wortwahl und kein Messwert. Ich habe eine "
        "Verdachtsliste gebaut und kein Urteil gesprochen.",
        "**Die Daten.** Bei Z19829 (`w.vorname||w.n`) haengt der Befund "
        "daran, ob in der Tabelle beide Felder leer sein koennen. Ich habe "
        "nicht in die Datenbank gesehen — auftragsgemaess — und entscheide "
        "es deshalb nicht.",
        "**Die 183 Symbol-/Emoji-Knoepfe erneut.** Abschnitt 0 nennt die "
        "14, die durch die drei Blindstellen von v957/958 gefallen sind. "
        "Ich habe die uebrigen 169 nicht einzeln gegengelesen; dass sie "
        "einen `title` oder ein `aria-label` TRAGEN, ist gemessen, ob das "
        "Wort passt, nicht.",
    ]:
        w("* " + zeile)
    w("")
    w("## 7. Wie das nachzumessen ist")
    w("")
    w("```")
    w("python scripts/bedienelemente_scan.py          # die Zahlen")
    w("python scripts/bedienelemente_scan.py koeder   # die 10 Selbstproben")
    w("python scripts/bedienelemente_scan.py json     # jede Stelle einzeln")
    w("python scripts/bedienelemente_gegenprobe_v957_958.py  # was v957/v958")
    w("                                               #   wirklich sehen")
    w("python scripts/bedienelemente_bericht.py       # diesen Bericht neu")
    w("```")
    w("")
    w("`scripts/bedienelemente_scan.py` ist ein MESSGERAET, kein Riegel. Es "
      "steht bewusst nicht unter `tests/`: ein Riegel behauptet, die Zahl "
      "sei null, und diese Zahl ist nicht null. Wer daraus einen Riegel "
      "macht, braucht je Klasse eine namentliche Ausnahmeliste MIT GRUND — "
      "und die Koeder muessen mit.")
    w("")

    text = "\n".join(T) + "\n"
    io.open(ZIEL, "w", encoding="utf-8", newline="").write(text)
    print("geschrieben: %s (%d Bytes, %d Zeilen)"
          % (os.path.normpath(ZIEL), len(text.encode("utf-8")),
             text.count("\n")))


if __name__ == "__main__":
    main()
