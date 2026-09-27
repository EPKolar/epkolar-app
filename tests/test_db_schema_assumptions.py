"""v3.8.61 MEGA-C Phase 7.1: DB-Schema-Annahmen.

Verhindert Schema-Drift-Bugs wie v3.8.55→56 (file_url) und v3.8.57→59
(xPct/yPct/page silent fail). Statische Tests gegen index.html-Patterns.
"""
import os
import re
import sys
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import code_scan  # noqa: E402


def test_AS_GRP_OFFEN_includes_underscore_variant():
    """Lehre v3.8.55: scheinstatus="in_bearbeitung" (snake) muss matchen."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'AS_GRP_OFFEN\s*=\s*\[([^\]]+)\]', text)
    assert m, 'AS_GRP_OFFEN nicht gefunden'
    assert 'in_bearbeitung' in m.group(1)


def test_no_plaene_table_call():
    """plaene-Tabelle existiert nicht — DB-Tabelle heisst 'plans'."""
    text = INDEX.read_text(encoding='utf-8')
    assert "_sbGet('plaene'" not in text
    assert '_sbGet("plaene"' not in text


def test_no_projekte_table_call():
    """projekte-Tabelle existiert nicht — DB-Tabelle heisst 'projects'."""
    text = INDEX.read_text(encoding='utf-8')
    assert "_sbGet('projekte'" not in text
    assert '_sbGet("projekte"' not in text


# ══════════════════════════════════════════════════════════════════════════
# v3.9.961 — DIESER RIEGEL HAT NULL ZUSICHERUNGEN AUSGEFUEHRT
#
# Die alte Fassung war:
#     matches = re.findall(r"_sbPatch\(\s*['\"]tickets['\"][^)]+\{([^}]+)\}", text)
#     for m in matches:
#         assert 'xPct' not in m ...
#
# Sie hatte ZWEI Fehler, von denen jeder einzeln schon toedlich ist. Beide
# sind laufzeitgemessen belegt (docs/befunde/WAS_LAEUFT_WIRKLICH.md §2 B):
#
# 1. LEERE GRUNDGESAMTHEIT. `tickets` wird ueber _sbPatch gar nicht
#    geschrieben, `matches` ist leer, die Schleife laeuft NIE. Gemessen: der
#    Fall fuehrte NULL Zusicherungen aus und meldete gruen. Damit sah der
#    Riegel im Zustand "alles in Ordnung" genau so aus wie im Zustand "mein
#    Regex ist kaputt" — und das ist der Grund, warum Fehler 2 zwei Jahre
#    unbemerkt blieb. EINE LEERE GRUNDGESAMTHEIT BESTEHT KEINE PROBE.
#
# 2. BRUECHIGES MUSTER. `[^)]+` kann die schliessende Klammer eines Aufrufs
#    IM ARGUMENT nicht ueberqueren. Belegt: gegen
#        _sbPatch("tickets", String(t.id), {xPct:1})
#    findet das alte Muster NULL Treffer. Eine echte Rueckkehr in genau
#    dieser Schreibweise waere unsichtbar geblieben.
#
# Was jetzt anders ist:
#   * Klammern werden GEZAEHLT statt verboten — mit code_scan._klammer_zu,
#     derselben Zaehlung, die auch die Knopf-/Element-Abtaster benutzen
#     (nicht nachgebaut: sie ueberspringt Zeichenketten, sonst laeuft die
#     Bilanz an jeder Klammer in einem Text aus dem Tritt).
#   * Kommentare und Zeichenketten sind ueber code_scan.ist_code ausgenommen.
#     Ohne das erfuellt der Erklaerkommentar zum Ausbau den Riegel selbst —
#     im Bestand sind 3 der 23 _sbPatch-Nennungen Kommentar (Z3085, Z29983,
#     Z30001).
#   * Der Riegel BELEGT ZUERST SEINE GRUNDGESAMTHEIT (20 _sbPatch-Aufrufe im
#     Code, darunter die Tabelle `fahrzeuge`) und behauptet ERST DANN eine
#     Abwesenheit. Faellt der Auszieher aus, wird der Riegel ROT statt gruen.
#   * Geprueft werden SCHLUESSEL, nicht Vorkommen: `{x: xPct*w}` liest xPct
#     als Wert und schreibt keine xPct-Spalte — das darf nicht anschlagen.
#   * Ein KOEDER JE FORM (KOEDER_ROT), nicht einer fuer den Zaehler, plus
#     Gegenproben (KOEDER_GRUEN), die NICHT gemeldet werden durften.
#
# Derselbe Auszieher wird von tests/test_tickets_xy_schema.py benutzt (der
# zweite Fall mit demselben Befund) — EINE Definition, nicht zwei Kopien mit
# zwei Rechnungen.
# ══════════════════════════════════════════════════════════════════════════

# Kein Punkt in der Ausschlussliste: `window._sbPatch(` soll mitzaehlen,
# `_xsbPatch(` nicht.
_SBPATCH = re.compile(r"(?<![A-Za-z0-9_$])_sbPatch\s*\(")

# Untergrenze der Grundgesamtheit. Gemessen am 27.09.2026: 20 Aufrufe im Code.
# Nicht `== 20`, weil ein neuer _sbPatch-Aufruf irgendwo in der App diesen
# Riegel nicht rot machen soll; nicht `>= 1`, weil ein halb ausgefallener
# Auszieher, der genau einen Aufruf findet, damit durchkaeme.
_MIND_AUFRUFE = 15


def sbpatch_aufrufe(text):
    """(pos, tabelle_oder_None, argumenttext) je _sbPatch-Aufruf im CODE.

    `tabelle` ist der Wert des ersten Arguments, wenn es ein
    Zeichenketten-Literal ist, sonst None (z.B. `_sbPatch(table,...)`).
    """
    feld = code_scan.ist_code(text)
    aus = []
    for m in _SBPATCH.finditer(text):
        if not feld[m.start()]:
            continue
        auf = m.end() - 1                      # zeigt auf die '('
        ende = code_scan._klammer_zu(text, auf, "(", ")")
        if ende < 0:
            aus.append((m.start(), None, ""))
            continue
        args = text[auf + 1:ende - 1]
        t = re.match(r"\s*(['\"])([^'\"]*)\1", args)
        aus.append((m.start(), t.group(2) if t else None, args))
    return aus


def objektliterale(args):
    """Jedes AEUSSERE Objektliteral im Argumenttext, mit Klammern.

    "Aeusser" heisst: nicht innerhalb eines anderen `{}`. Ein verschachteltes
    Objekt (`{pos:{a:1}}`) ist damit Teil seines Vaters und kein eigener
    Rumpf — seine Schluessel sind keine Spalten.

    🔴 Runde Klammern werden dabei bewusst NICHT als Grenze gezaehlt. Meine
    erste Fassung nahm nur Literale auf der obersten Argumentebene und war
    damit blind fuer
        _sbPatch('tickets', t.id, _mapBody({xPct:1}))
    — und genau diese Schreibweise steht im Bestand:
        _sbPatch("arbeitsscheine",existing.id,_mapBody(upd))   (index.html:3950)
    Ein Riegel, der eine im Repo VORHANDENE Schreibweise nicht kennt, ist
    dieselbe Krankheit, gegen die er gebaut wurde. Koeder J haelt die Form
    fest.
    """
    aus = []
    i, n = 0, len(args)
    while i < n:
        c = args[i]
        if c in "\"'`":
            i = code_scan._zeichenkette_ueberspringen(args, i)
            continue
        if c == "{":
            e = code_scan._klammer_zu(args, i, "{", "}")
            if e < 0:
                break
            aus.append(args[i:e])
            i = e
            continue
        i += 1
    return aus


def schluessel(literal):
    """Die SCHLUESSEL der obersten Ebene eines Objektliterals.

    Erkennt `{a:1}`, `{"a":1}`, `{'a':1}` und die Kurzschreibung `{a}`.
    Ein Name, der nur als WERT vorkommt (`{x: xPct}`), ist kein Schluessel —
    genau das trennt eine Umrechnung von einem Schreibversuch.
    """
    aus = []
    i, n, tiefe = 0, len(literal), 0
    erwartet = False
    while i < n:
        c = literal[i]
        if c in "\"'`":
            ende = code_scan._zeichenkette_ueberspringen(literal, i)
            if erwartet and tiefe == 1 and re.match(r"\s*:", literal[ende:]):
                aus.append(literal[i + 1:ende - 1])
            erwartet = False
            i = ende
            continue
        if c in "{([":
            tiefe += 1
            erwartet = (tiefe == 1 and c == "{")
            i += 1
            continue
        if c in "})]":
            tiefe -= 1
            erwartet = False
            i += 1
            continue
        if c == "," and tiefe == 1:
            erwartet = True
            i += 1
            continue
        if erwartet and tiefe == 1:
            m = re.match(r"\s*([A-Za-z_$][\w$]*)\s*[:,}]", literal[i:])
            if m:
                aus.append(m.group(1))
                i += m.end(1)
                erwartet = False
                continue
            if c in " \t\r\n":
                i += 1
                continue
            erwartet = False
        i += 1
    return aus


def spaltenschreiber(text, tabelle, spalten):
    """(pos, spalte, literal) je _sbPatch-Aufruf, der `spalten` auf `tabelle`
    schreibt. Leere Liste = kein Verstoss.

    Sagt NICHTS ueber die Grundgesamtheit — die wird getrennt belegt, damit
    "keine Verstoesse" und "nichts gemessen" nicht dieselbe Antwort geben.
    """
    aus = []
    for pos, tab, args in sbpatch_aufrufe(text):
        if tab != tabelle:
            continue
        for lit in objektliterale(args):
            sch = schluessel(lit)
            for sp in spalten:
                if sp in sch:
                    aus.append((pos, sp, lit[:120]))
    return aus


# Ein Koeder JE FORM. Jede Zeile ist eine Schreibweise, in der die Regression
# zurueckkehren koennte; C ist die, an der das alte Muster nachweislich
# vorbeilief.
KOEDER_ROT = [
    ("A einfach", "_sbPatch('tickets', id, {xPct:1,yPct:2})"),
    ("B innere Klammer im Wert",
     "_sbPatch('tickets', t.id, {xPct: pct(e.x), yPct: 2})"),
    ("C innere Klammer im 2. Argument — hier lief das alte Muster vorbei",
     '_sbPatch("tickets", String(t.id), {xPct:1})'),
    ("D Aufruf ueber zwei Zeilen", "_sbPatch('tickets',\n  t.id,\n  {xPct:1})"),
    ("E nur yPct", '_sbPatch("tickets", id, {yPct:9})'),
    ("F verschachteltes Objekt davor",
     "_sbPatch('tickets', id, {pos:{a:1}, xPct:1})"),
    ("G ueber window", "window._sbPatch('tickets', id, {xPct:1})"),
    ("H Schluessel in Anfuehrungszeichen",
     "_sbPatch('tickets', id, {\"xPct\":1})"),
    ("I Kurzschreibung", "_sbPatch('tickets', id, {xPct})"),
    ("J Rumpf durch einen Abbilder gereicht — diese Form steht im Bestand "
     "(index.html:3950)",
     "_sbPatch('tickets', t.id, _mapBody({xPct:1}))"),
    ("K Rumpf in runden Klammern",
     "_sbPatch('tickets', t.id, ({yPct:1}))"),
]

# Ein Zaehler, der ALLES meldet, schlaegt bei jedem Koeder an und ist trotzdem
# kaputt. Diese Faelle duerfen NICHT gemeldet werden.
KOEDER_GRUEN = [
    ("andere Tabelle", "_sbPatch('fahrzeuge', id, {xPct:1})"),
    ("richtige Spalten", "_sbPatch('tickets', id, {x:1,y:2})"),
    ("Tabellenname als Praefix", '_sbPatch("tickets_log", id, {xPct:1})'),
    ("nur im Kommentar", "// alt: _sbPatch('tickets', id, {xPct:1})\nvar a=1;"),
    ("nur in einer Zeichenkette",
     "var s=\"_sbPatch('tickets', id, {xPct:1})\";"),
    ("aehnlicher Funktionsname", "_xsbPatch('tickets', id, {xPct:1})"),
    ("xPct nur als WERT gelesen",
     "_sbPatch('tickets', id, {x: xPct*w, y: yPct*h})"),
    ("Lesen statt Schreiben", "_sbGet('tickets', 'plan_id=eq.'+pid)"),
    ("xPct als Schluessel eines VERSCHACHTELTEN Objekts (keine Spalte)",
     "_sbPatch('tickets', id, {meta:{xPct:1}})"),
    ("anderer Tabelle ihr Abbilder-Rumpf",
     "_sbPatch('fahrzeuge', id, _mapBody({xPct:1}))"),
]

_SPALTEN = ("xPct", "yPct")


def test_no_xPct_yPct_in_tickets_patch():
    """v3.8.59 Schema-Reality: tickets-DB hat KEINE xPct/yPct-Spalten.

    Zuerst die Grundgesamtheit belegen, dann die Abwesenheit behaupten.
    """
    text = INDEX.read_text(encoding='utf-8')
    # (a) Der Abtaster ist geeicht — sonst ist jede Zahl von ihm wertlos.
    geeicht, gef, erw = code_scan.eichen(text)
    assert geeicht, (
        'code_scan-Eichung gescheitert (%d von %d) — der Abtaster irrt sich, '
        'die Aussage unten waere wertlos.' % (gef, erw))
    # (b) WAS wurde geprueft? Ohne diese Zusicherung ist "0 Verstoesse" von
    #     "0 gemessen" nicht zu unterscheiden.
    rufe = sbpatch_aufrufe(text)
    assert len(rufe) >= _MIND_AUFRUFE, (
        'Nur %d _sbPatch-Aufrufe im Code gefunden (erwartet >=%d). Entweder '
        'ist der Schreibweg umgebaut oder der Auszieher ausgefallen — in '
        'beiden Faellen prueft dieser Riegel nichts mehr.'
        % (len(rufe), _MIND_AUFRUFE))
    tabellen = sorted({t for _, t, _ in rufe if t})
    assert 'fahrzeuge' in tabellen, (
        'Der Auszieher liest keine Tabellennamen mehr aus echten Aufrufen '
        '(gefunden: %r). Damit koennte er auch "tickets" nicht erkennen.'
        % (tabellen,))
    # (c) Erst jetzt die Behauptung.
    verstoesse = spaltenschreiber(text, 'tickets', _SPALTEN)
    assert not verstoesse, (
        '_sbPatch schreibt xPct/yPct auf tickets — die Tabelle hat diese '
        'Spalten nicht, PostgREST verwirft den Rumpf STILL (v3.8.57→59). '
        'Fundstellen: %r' % (verstoesse,))


def test_koeder_jede_schreibweise_der_regression_wird_gefunden():
    """Ohne Koeder ist die 0 aus dem Riegel oben wertlos.

    Jede Form einzeln — nicht eine fuer den Zaehler. Genau daran sind
    v3.9.957/958 gescheitert: eine Schreibweise fehlte, 17 Maengel blieben
    unsichtbar.
    """
    assert len(KOEDER_ROT) >= 11, 'Koederliste ausgeduennt — %d Formen' % len(KOEDER_ROT)
    for name, probe in KOEDER_ROT:
        assert spaltenschreiber(probe, 'tickets', _SPALTEN), (
            'KOEDER NICHT GEFUNDEN (%s): %r — der Riegel oben wuerde diese '
            'Regression durchwinken.' % (name, probe))


def test_gegenprobe_der_tickets_riegel_meldet_nichts_falsches():
    """Ein Zaehler, der alles meldet, schlaegt bei jedem Koeder an und ist
    trotzdem kaputt."""
    assert len(KOEDER_GRUEN) >= 10, 'Gegenprobenliste ausgeduennt'
    for name, probe in KOEDER_GRUEN:
        assert not spaltenschreiber(probe, 'tickets', _SPALTEN), (
            'FEHLALARM (%s): %r wurde gemeldet, obwohl nichts falsch ist.'
            % (name, probe))


def test_selbstprobe_der_auszieher_meldet_eine_leere_menge_als_leer():
    """Die Wache aus (b) muss eine ausgefallene Messung erkennen koennen.

    Waere `sbpatch_aufrufe` blind, gaebe es keinen Unterschied zwischen
    "sauber" und "nichts gemessen" — genau der Zustand, in dem dieser Riegel
    zwei Jahre stand.
    """
    assert sbpatch_aufrufe('var a=1;/* _sbPatch("tickets",id,{xPct:1}) */') == [], (
        'Der Auszieher findet Aufrufe in einem Text, der keine im Code hat.')
    assert len(sbpatch_aufrufe("_sbPatch('a',1,{b:2})")) == 1, (
        'Der Auszieher findet einen echten Aufruf nicht — dann wuerde die '
        'Grundgesamtheits-Wache oben zu Recht rot.')


def test_das_alte_muster_war_bruechig_und_bleibt_es():
    """Haelt den Grund fest, warum das Muster ersetzt wurde.

    Kippt diese Zusicherung, hat jemand das alte `[^)]+`-Muster reparieren
    koennen — dann gehoert dieser Fall weg, nicht der Riegel.
    """
    alt = re.compile(r"_sbPatch\(\s*['\"]tickets['\"][^)]+\{([^}]+)\}")
    probe = '_sbPatch("tickets", String(t.id), {xPct:1})'
    assert alt.findall(probe) == [], (
        'Das alte Muster findet diese Form inzwischen doch — Begruendung '
        'oben pruefen.')
    assert spaltenschreiber(probe, 'tickets', _SPALTEN), (
        'Der neue Auszieher findet sie nicht — dann ist nichts gewonnen.')


def test_projects_table_used_via_sbGet():
    """projects-Tabelle existiert (3 Rows DB-verifiziert) — Code muss sie nutzen."""
    text = INDEX.read_text(encoding='utf-8')
    matches = re.findall(r'_sbGet\(\s*[\'"]projects[\'"]', text)
    assert len(matches) >= 1, f'projects-Tabelle muss via _sbGet aufgerufen werden, gefunden: {len(matches)}'


def test_plans_table_used_via_sbGet():
    """plans-Tabelle existiert (1 Row DB-verifiziert) — Code muss sie nutzen."""
    text = INDEX.read_text(encoding='utf-8')
    matches = re.findall(r'_sbGet\(\s*[\'"]plans[\'"]', text)
    assert len(matches) >= 1, 'plans-Tabelle muss via _sbGet aufgerufen werden'


def test_finkzeit_worker_id_has_lookup_not_raw():
    """finkzeit pendingDetails muss Worker-Name-Lookup machen (nicht raw u1/w1 anzeigen).
    Akzeptiert monteure.find ODER users.find ODER window._allUsers — Lookup-Quelle ist
    aktuell monteure (Workers w1-w9), kann später auf users (u1-u9) umgestellt werden
    falls Reminder-Plan-Block-2 noch implementiert wird."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'_pendingByMonth\s*=\s*\{\}[\s\S]{0,800}pendingDetails\s*=', text)
    assert m, 'pendingDetails-Builder nicht gefunden'
    body = m.group(0)
    has_lookup = 'monteure.find' in body or 'users.find' in body or 'window._allUsers' in body or 'usersMap' in body
    assert has_lookup, 'Lookup muss aus monteure/users sein, nicht raw worker_id-Display'


def test_camelcase_to_snakecase_mapper_exists():
    """_toSnake + _mapBody muessen existieren (camelCase-Frontend → snake_case-DB)."""
    text = INDEX.read_text(encoding='utf-8')
    assert 'function _toSnake' in text
    assert 'function _mapBody' in text


def test_planSrc_resolver_handles_file_url():
    """v3.8.56 Lehre: PlanViewerCanvas muss file_url als Fallback haben."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'_planSrc\s*=\s*([^;]+);', text)
    assert m
    assert 'file_url' in m.group(1)


def test_planLoadPdf_handles_storage_url():
    """_planLoadPdf muss https-URLs (Supabase Storage) akzeptieren."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'async function _planLoadPdf[\s\S]*?pdfjsLib\.getDocument', text)
    assert m
    assert 'http:' in m.group(0) or 'https:' in m.group(0)
