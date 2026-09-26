# -*- coding: utf-8 -*-
"""v3.9.952 - jede ENTSCHEID-Stelle des Austritts auf die eine Regel.

WARUM DAS DER TEUERSTE FUND DER SERIE WAR
─────────────────────────────────────────
Der Austritt wurde an 22 Stellen direkt gelesen, in drei Schreibweisen. Eine
davon (`!String(m.austritt||'').trim()`) schloss JEDEN mit gesetztem Datum
aus - auch einen, der erst naechsten Monat geht - und stand in der
Kapazitaetsliste des ChefDashboards. Wer zum Monatsletzten kuendigt,
verschwand ab dem Tag der Eintragung aus der Disposition, waehrend er noch
zehn Tage arbeitete. Das ist keine Anzeigesache.

v3.9.950 hat die zwei Stellen dieser dritten Form behoben. Was fehlte, war der
Beleg, dass es wirklich EINE Regel ist: es standen weiter fuenf Stellen mit der
ausgeschriebenen Umkehrung im Code - gleichwertig, aber vier zusaetzliche
Gelegenheiten, sie beim naechsten Mal falsch abzuschreiben.

DIE EINORDNUNG ALLER 22 ZUGRIFFE - keiner fehlt
───────────────────────────────────────────────
DATEN (bleiben, sie bilden das Feld ab):
    _mapWorker        Serverfeld -> Objekt
    App               Saat-Nutzlast
    MitarbeiterView   Anlegen (lokal und Warteschlange), Datumsfeld
ANZEIGE (bleiben, sie zeigen das Datum oder faerben danach):
    MitarbeiterView   "Ausgetreten <Datum>" - die Bedingung davor ist bereits
                      _maEhemalig(m)
    MitarbeiterView   Faerbung und Text im Bearbeitungsformular des Admins.
                      NUANCE, benannt statt verschwiegen: bei einem
                      ZUKUENFTIGEN Austritt steht dort rot das Datum statt
                      "aktiv". Im Bearbeitungsformular ist das richtig - der
                      Admin soll sehen, DASS ein Datum gesetzt ist. Abgeleitet
                      wird daraus nichts.
SORTIER: keine. Es gibt im Code keine Sortierung nach austritt.
ENTSCHEID (alle fuenf umgestellt):
    _dispoBuildInput  wer ist fuer die Dispo verfuegbar
    _fit              wer erscheint in der Monteurliste
    AdminPanel        wer braucht noch einen Login
    WeekPlan          wer ist im Wochenplan waehlbar
    ZeiterfassungView wer ist in der Zeiterfassung waehlbar
"""
import io
import json
import re
import subprocess
import tempfile
import os

import pytest

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]


def _roh():
    return io.open(str(WURZEL / "index.html"), encoding="utf-8",
                   newline="").read()


def _code_feld(roh):
    import sys
    sys.path.insert(0, str(WURZEL / "scripts"))
    from code_scan import ist_code, eichen
    ok, gefunden, erwartet = eichen(roh)
    assert ok, ("Eichung von code_scan gescheitert (%d von %d) - ohne sie "
                "sagt keine Zaehlung hier etwas." % (gefunden, erwartet))
    return ist_code(roh)


# ── Die Ausnahmeliste: NAMENTLICH, nicht als Muster ───────────────────────
# Jede erlaubte Stelle steht mit ihrer Kennung hier. Kommt eine NEUE dazu,
# wird dieser Riegel rot - und wer sie eintraegt, muss sie einordnen. Genau
# das ist der Zweck: ein Muster wie "alles in MitarbeiterView ist erlaubt"
# wuerde die naechste Entscheid-Stelle dort durchlassen.
ERLAUBT = {
    # DATEN
    '.austritt||"",stundensatz:parseFlo': "DATEN _mapWorker: Serverfeld -> Objekt",
    '.austritt,active:1}));}catch(e){co': "DATEN App: Saat-Nutzlast",
    '.austritt||""}]);     setMonteurP': "DATEN MitarbeiterView: Anlegen, lokal",
    '.austritt||""}});     /* 2) Login': "DATEN MitarbeiterView: Anlegen, Warteschlange",
    '.austritt||"", onChange: e=>setNf(': "DATEN MitarbeiterView: Datumsfeld neu",
    '.austritt||"", onChange: e=>updMon': "DATEN MitarbeiterView: Datumsfeld bearbeiten",
    # ANZEIGE
    '.austritt)):null;   // v3.8.94 Sp': "ANZEIGE MitarbeiterView: 'Ausgetreten <Datum>', Bedingung ist _maEhemalig",
    '.austritt?COLORS.ERROR:V.dm}}, sel': "ANZEIGE MitarbeiterView: Faerbung im Bearbeitungsformular",
    '.austritt?fdt(selM.austritt):"akti': "ANZEIGE MitarbeiterView: Datum oder 'aktiv'",
    '.austritt):"aktiv")             )': "ANZEIGE MitarbeiterView: dieselbe Stelle, zweiter Zugriff",
    # DIE DEFINITION SELBST
    '.austritt&&String(m.austritt).slic': "DEFINITION _maIstEhemalig",
    '.austritt).slice(0,10)<h); } /* ': "DEFINITION _maIstEhemalig, zweiter Zugriff",
}


def test_jeder_direkte_zugriff_steht_in_der_ausnahmeliste():
    """Der eigentliche Riegel. Eine NEUE Stelle macht ihn rot, und wer sie
    eintraegt, muss sie einordnen."""
    roh = _roh()
    feld = _code_feld(roh)
    gefunden = {}
    for m in re.finditer(r"\.austritt\b", roh):
        if not feld[m.start()]:
            continue
        kennung = roh[m.start():m.start() + 34].replace("\r\n", " ")
        gefunden[kennung] = roh.count("\n", 0, m.start()) + 1

    assert gefunden, (
        "KOEDER STUMM: kein einziger .austritt-Zugriff im Code gefunden. Dann "
        "prueft dieser Riegel nichts - und der Austritt waere aus der App "
        "verschwunden, was ein viel groesserer Befund waere.")

    neu = {k: v for k, v in gefunden.items() if k not in ERLAUBT}
    assert not neu, (
        "NEUE direkte .austritt-Zugriffe (Kennung -> Zeile): %s\n"
        "Jeder Zugriff muss eingeordnet werden:\n"
        "  DATEN   - bildet das Feld ab, entscheidet nichts -> in ERLAUBT\n"
        "  ANZEIGE - zeigt das Datum oder faerbt danach     -> in ERLAUBT\n"
        "  SORTIER - ordnet danach                          -> in ERLAUBT\n"
        "  ENTSCHEID - leitet ab, OB jemand ausgetreten ist -> auf "
        "_maIstEhemalig umstellen, NICHT eintragen.\n"
        "Der teure Fall war eine ENTSCHEID-Stelle, die wie eine harmlose "
        "Existenzpruefung aussah." % neu)

    weg = {k: v for k, v in ERLAUBT.items() if k not in gefunden}
    assert not weg, (
        "Diese eingetragenen Stellen gibt es nicht mehr: %s. Wenn sie "
        "absichtlich entfernt wurden, gehoert der Eintrag hier weg - sonst "
        "schuetzt die Liste etwas, das es nicht gibt, und waechst blind."
        % list(weg))


def test_kein_direkter_datumsvergleich_ausserhalb_der_regel():
    """Ein Vergleich auf `austritt` mit <, >, <= oder >= ist eine ENTSCHEIDUNG.
    Erlaubt ist er nur in `_maIstEhemalig` selbst."""
    roh = _roh()
    feld = _code_feld(roh)
    i_def = roh.index("function _maIstEhemalig(m,heute){")
    j_def = roh.index("}", roh.index("return !!(m&&m.austritt", i_def)) + 1

    # Das Muster darf das `=>` einer Pfeilfunktion NICHT als Vergleich lesen -
    # mein erster Versuch tat das und meldete zwei Datumsfelder als
    # Entscheid-Stellen (`austritt||"", onChange: e=>`). Ein `>` direkt hinter
    # einem `=` ist ein Pfeil, kein Vergleich.
    VERGLEICH = re.compile(r"austritt[^;\n]{0,40}?(?:(?<!=)>=?|<=?)")
    treffer = []
    for m in VERGLEICH.finditer(roh):
        if not feld[m.start()]:
            continue
        if i_def <= m.start() < j_def:
            continue
        treffer.append((roh.count("\n", 0, m.start()) + 1, m.group(0)[:50]))
    assert not treffer, (
        "Direkte Datumsvergleiche auf austritt ausserhalb von "
        "_maIstEhemalig: %s. Das ist eine zweite Regel, und zwei Regeln "
        "widersprechen sich irgendwann - in v3.9.950 taten sie es bei einem "
        "Austritt in der Zukunft." % treffer)


def test_koeder_der_vergleichssucher_findet_die_definition():
    """Gegenprobe zum Riegel darueber: der Sucher MUSS den Vergleich in der
    Definition finden. Findet er ihn nicht, ist seine Null kein Befund."""
    roh = _roh()
    feld = _code_feld(roh)
    i_def = roh.index("function _maIstEhemalig(m,heute){")
    j_def = roh.index("}", roh.index("return !!(m&&m.austritt", i_def)) + 1
    drin = [m.start() for m in re.finditer(r"austritt[^;\n]{0,40}?\)?\s*[<>]=?", roh)
            if feld[m.start()] and i_def <= m.start() < j_def]
    assert drin, (
        "KOEDER STUMM: der Sucher findet den Datumsvergleich in "
        "_maIstEhemalig nicht. Dann sagt seine Null ueber den Rest des "
        "Dokuments nichts.")


def test_die_fuenf_entscheid_stellen_benutzen_die_regel():
    """Namentlich, damit eine Rueckumstellung auffaellt."""
    roh = _roh()
    for name, marke in (
        ("Dispo", "!_maIstEhemalig(m,_heute)"),
        ("Monteurliste", "!_maIstEhemalig(m,todayStr)"),
        ("Login noetig", "!_maIstEhemalig(w,_hkNL)"),
        ("Wochenplan", "!_maIstEhemalig(m,_hkMA)"),
        ("Zeiterfassung", "!_maIstEhemalig(m,_hkZE)"),
    ):
        assert marke in roh, (
            "Die ENTSCHEID-Stelle '%s' benutzt `%s` nicht mehr. Steht dort "
            "wieder eine eigene Datumsrechnung, ist die eine Regel wieder "
            "vier." % (name, marke))


# ── Der Grenzfall, gepinnt: heute ist der erste Tag DANACH ────────────────

@pytest.fixture(scope="module")
def kapazitaet():
    """Faehrt die Kapazitaetsliste des ChefDashboards unter Node.

    Geschnitten werden `_maIstEhemalig`, `_kapNonField` und der
    `_kapMont`-Ausdruck WOERTLICH aus index.html. Ein Riegel, der nur
    Zeichenketten vergleicht, koennte nicht zeigen, WER in der Liste landet -
    und genau darum geht es: eine Person, die noch da ist, verschwand aus der
    Disposition.
    """
    roh = _roh()
    i = roh.index("function _maIstEhemalig(m,heute){")
    j = roh.index("}", roh.index("return !!(m&&m.austritt", i)) + 1
    fn = roh[i:j]

    # Bis `};` schneiden, nicht bis zum ersten Semikolon: `_kapNonField` ist
    # eine Pfeilfunktion mit einem `;` IM Koerper, und mein erster Schnitt
    # endete mitten darin - Node meldete "Unexpected end of input".
    i2 = roh.index("const _kapNonField=")
    j2 = roh.index("};", i2) + 2
    nonfield = roh[i2:j2]
    assert nonfield.count("{") == nonfield.count("}"), nonfield

    i3 = roh.index("const _kapMont=monteure.filter(")
    j3 = roh.index(";", i3) + 1
    kapmont = roh[i3:j3]
    assert "_maIstEhemalig" in kapmont, kapmont

    prog = """
function _ezHeuteISO(){ return "2026-09-26"; }
__FN__
__NONFIELD__
function lauf(monteure){
  __KAPMONT__
  return _kapMont.map(function(m){return m.id;});
}
const FAELLE = {
  ohne_datum:        [{id:"A", r:"Monteur", austritt:""}],
  austritt_gestern:  [{id:"B", r:"Monteur", austritt:"2026-09-25"}],
  austritt_heute:    [{id:"C", r:"Monteur", austritt:"2026-09-26"}],
  austritt_morgen:   [{id:"D", r:"Monteur", austritt:"2026-09-27"}],
  austritt_monatsende:[{id:"E", r:"Monteur", austritt:"2026-09-30"}],
  nichtfeldrolle:    [{id:"F", r:"Backoffice", austritt:""}]
};
const aus = {};
for (const [name, liste] of Object.entries(FAELLE)) aus[name] = lauf(liste);
process.stdout.write(JSON.stringify(aus));
""".replace("__FN__", fn).replace("__NONFIELD__", nonfield) \
   .replace("__KAPMONT__", kapmont)

    tmp = tempfile.NamedTemporaryFile(suffix=".js", delete=False, mode="w",
                                      encoding="utf-8")
    try:
        tmp.write(prog)
        tmp.close()
        r = subprocess.run(["node", tmp.name], capture_output=True, text=True,
                           timeout=60)
        assert r.returncode == 0, "Node: %s" % (r.stderr[-900:],)
        return json.loads(r.stdout)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def test_wer_morgen_geht_ist_heute_in_der_kapazitaetsliste(kapazitaet):
    """DER TEURE FALL, gepinnt.

    Wer zum Monatsletzten kuendigt, arbeitet noch zehn Tage. Er gehoert in die
    Kapazitaetsplanung dieser zehn Tage.
    """
    assert kapazitaet["austritt_morgen"] == ["D"], (
        "Ein Mitarbeiter mit Austritt MORGEN fehlt heute in der "
        "Kapazitaetsliste: %r. Das war der Fehler aus v3.9.950."
        % kapazitaet["austritt_morgen"])
    assert kapazitaet["austritt_monatsende"] == ["E"], (
        "Ein Mitarbeiter mit Austritt zum Monatsende fehlt heute in der "
        "Kapazitaetsliste: %r." % kapazitaet["austritt_monatsende"])


def test_wer_gestern_ging_ist_nicht_mehr_drin(kapazitaet):
    assert kapazitaet["austritt_gestern"] == [], (
        "Ein Mitarbeiter mit Austritt GESTERN steht noch in der "
        "Kapazitaetsliste: %r." % kapazitaet["austritt_gestern"])


def test_der_austrittstag_selbst_zaehlt_noch_als_aktiv(kapazitaet):
    """🔴 HIER WEICHT DER CODE VON DER BESCHREIBUNG AB - UM EINEN TAG.

    Der Auftrag zu diesem Riegel sagte: "mit austritt = heute nicht (heute ist
    der erste Tag danach - so ist die Regel definiert, und so soll sie
    bleiben)". GEMESSEN ist sie anders definiert:

        _maIstEhemalig:  String(m.austritt).slice(0,10) < h
        austritt = heute:  "2026-09-26" < "2026-09-26"  ->  FALSCH
        also: am Austrittstag selbst gilt der Mensch noch als AKTIV,
              ehemalig wird er erst am Tag DANACH.

    Dieser Riegel pinnt den GEMESSENEN Stand, nicht die Beschreibung - wer
    beides gleichsetzt, hat einen stillen Fehler von einem Tag.

    WELCHE VARIANTE RICHTIG IST, IST EINE FACHFRAGE und steht bei Sebastian:
      * Ist das Austrittsdatum der LETZTE Arbeitstag, dann ist der Code richtig
        (an diesem Tag arbeitet der Mensch noch, er gehoert in die Kapazitaet).
      * Ist es der ERSTE Tag der Abwesenheit, dann fehlt in _maIstEhemalig ein
        `<=` statt `<`.
    In Oesterreich ist das Austrittsdatum ueblicherweise der letzte Tag des
    Dienstverhaeltnisses - das spricht fuer den Code. Aber das ist eine
    Auslegung und keine Messung, und geaendert wird hier nichts:
    `_maIstEhemalig` ist eine der sieben byte-identisch zu haltenden
    Funktionen, und die Aenderung wuerde alle 17 Aufrufstellen betreffen.
    """
    assert kapazitaet["austritt_heute"] == ["C"], (
        "Ein Mitarbeiter mit Austritt HEUTE steht NICHT mehr in der "
        "Kapazitaetsliste: %r. Damit ist die Regel von `<` auf `<=` gewandert "
        "- das ist eine Verschiebung um einen Tag fuer ALLE 17 Aufrufstellen "
        "und gehoert nicht nebenbei gemacht." % kapazitaet["austritt_heute"])


def test_koeder_der_gutfall_und_die_rollenabgrenzung(kapazitaet):
    """Ohne diese beiden Zeilen koennte die Liste einfach immer leer sein und
    alle Aussagen oben waeren wertlos."""
    assert kapazitaet["ohne_datum"] == ["A"], (
        "Ein Mitarbeiter OHNE Austrittsdatum steht nicht in der "
        "Kapazitaetsliste: %r - dann misst diese Datei nichts."
        % kapazitaet["ohne_datum"])
    assert kapazitaet["nichtfeldrolle"] == [], (
        "Eine Nicht-Feldrolle (Backoffice) steht in der Kapazitaetsliste: %r. "
        "Die zweite Haelfte der Abgrenzung (_kapNonField) wirkt nicht mehr."
        % kapazitaet["nichtfeldrolle"])
