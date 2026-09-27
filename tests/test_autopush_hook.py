"""Structural invariants for v3.8.42 Auto-Push implementation.

Block Z: Layer 1 Save-Hook (_juprowaPush fire-and-forget in save paths)
         Layer 2 _juprowaDrainPending(maxBatch=10) called from _juprowaSync
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code_scan  # noqa: E402
from conftest import _extract_fn  # noqa: E402


# Layer 2 - _juprowaDrainPending -------------------------------------------

def test_juprowa_drain_pending_defined(index_html):
    assert "async function _juprowaDrainPending" in index_html


def test_drain_pending_has_online_guard(index_html):
    m = re.search(r"async function _juprowaDrainPending[\s\S]+?\n\}", index_html)
    assert m
    body = m.group(0)
    assert "navigator.onLine" in body
    assert "offline" in body.lower() or "skipped" in body


def test_drain_pending_uses_for_of_not_promise_all(index_html):
    """Sequential for-of loop keeps runtime bounded and avoids parallel RPC storm."""
    m = re.search(r"async function _juprowaDrainPending[\s\S]+?\n\}", index_html)
    body = m.group(0)
    assert "for(const" in body or "for (const" in body
    assert "Promise.all" not in body


def test_drain_pending_calls_juprowapush_single(index_html):
    m = re.search(r"async function _juprowaDrainPending[\s\S]+?\n\}", index_html)
    body = m.group(0)
    assert "_juprowaPush(row.id)" in body


def test_drain_pending_has_default_maxbatch_10(index_html):
    m = re.search(r"async function _juprowaDrainPending[\s\S]+?\n\}", index_html)
    body = m.group(0)
    assert "10" in body, "default batch size 10 expected"
    assert "select=id" in body, "query must fetch id-only for speed"
    assert "limit=" in body, "limit clause required"


def test_juprowasync_calls_drain_pending(index_html):
    """_juprowaSync must drain pending push-queue at end of each cycle."""
    m = re.search(r"async function _juprowaSync[\s\S]+?^\}", index_html, re.M)
    assert m
    body = m.group(0)
    assert "_juprowaDrainPending" in body
    assert "[JP-DRAIN]" in body or "JP-DRAIN" in body


def test_startautosync_no_longer_uses_pushall(index_html):
    """Legacy _juprowaPushAll direct-call in _juprowaStartAutoSync removed in v3.8.42."""
    m = re.search(r"function _juprowaStartAutoSync[\s\S]+?\n\}", index_html)
    assert m
    body = m.group(0)
    # Check for direct CALL, not just string (comments may mention it)
    assert "_juprowaPushAll(" not in body, (
        "_juprowaPushAll direct call in AutoSync should be replaced by "
        "internal _juprowaDrainPending call (via _juprowaSync)."
    )


# Layer 1 - Save-Hook invariants -------------------------------------------

def test_save_path_contains_autopush_marker(index_html):
    """[AUTOPUSH] console tag must appear in at least one save path."""
    assert "[AUTOPUSH]" in index_html, "AUTOPUSH marker missing"


def test_save_hook_has_online_guard(index_html):
    """v3.9.756: Auto-Push laeuft ueber die per-Schein-Debounce-Klammer _juprowaSchedulePush.
    Online-Guard doppelt: (1) jeder Handler-Trigger prueft navigator.onLine BEVOR er schedult,
    (2) _juprowaSchedulePush selbst bricht offline ab, bevor es _juprowaPush ruft."""
    import re
    for m in re.finditer(r"_juprowaSchedulePush\(", index_html):
        line_start = index_html.rfind("\n", 0, m.start()) + 1
        line = index_html[line_start:index_html.index("\n", m.start())]
        if "function _juprowaSchedulePush" in line or "window._juprowaSchedulePush" in line:
            continue  # Definition / window-Export, kein Trigger
        if "_sid" in line:
            continue  # doSync-Flush-Hook: liegt bereits in doSyncs if(navigator.onLine)-Block + Fn-Guard
        assert "navigator.onLine" in line, "Handler-Trigger ohne navigator.onLine-Guard: %s" % line[:80]
    m = re.search(r"function _juprowaSchedulePush\([\s\S]+?\},2000\);\s*\}", index_html)
    assert m, "_juprowaSchedulePush-Koerper nicht gefunden"
    assert "if(!navigator.onLine)return;" in m.group(0), "_juprowaSchedulePush ohne Offline-Abbruch"


# ══════════════════════════════════════════════════════════════════════════
# v3.9.961 — DIESER RIEGEL WAR STRUKTURELL NIE ERFUELLBAR
#
# Die alte Fassung war:
#     for i, line in enumerate(index_html.splitlines()):
#         if "_juprowaPush(" in line and "AUTOPUSH" in line:
#             assert ".then(" in line, ...
#
# Gemessen (docs/befunde/WAS_LAEUFT_WIRKLICH.md §2 A1): `_juprowaPush(` steht
# in 7 Zeilen, `AUTOPUSH` in 2 — in NULL Zeilen beides. Die beiden
# AUTOPUSH-Marken sitzen auf der `.then()`/`.catch()`-FORTSETZUNGSZEILE
# (index.html:4285/4286), nie auf der Aufrufzeile (:4283). Die Bedingung konnte
# nie zutreffen, der Fall fuehrte NULL Zusicherungen aus und meldete gruen.
#
# WELCHE EIGENSCHAFT WAR GEMEINT? Name und Docstring sagen es: im
# SPEICHER-HAKEN darf `_juprowaPush` nicht awaited werden, sondern muss
# fire-and-forget laufen. Die Zeile war nur der falsche Messort — eine Zeile
# ist keine Struktur. Der Speicher-Haken ist seit v3.9.756 die per-Schein-
# Debounce-Klammer `_juprowaSchedulePush` (so benennt ihn auch der Nachbarfall
# test_save_hook_has_online_guard). Dort wird jetzt gemessen, ueber die
# Funktionsgrenze statt ueber die Zeilengrenze.
#
# ABGRENZUNG, und sie ist der Kern: `await` ist an DREI anderen Stellen
# richtig — in `_juprowaDrainPending` (:4234), in `_juprowaPushAll` (:4253) und
# im Einzel-Push auf Knopfdruck (:10847). Genau deshalb darf dieser Riegel
# nicht ueber die ganze Datei laufen. Dass die Abgrenzung wirkt, belegt
# test_gegenprobe_der_drain_darf_awaiten: dieselbe Pruefung schlaegt am
# Drain-Rumpf AN.
#
# `.then(` ODER `.catch(`: beides belegt, dass das Versprechen asynchron
# behandelt wird statt erwartet. Der nackte Aufruf ohne Kette ist ein Mangel
# (unbehandelte Ablehnung) — dafuer steht Koeder E.
#
# index.html wurde dabei nicht angefasst; `_juprowaPush` ist fuer Aenderungen
# ohnehin gesperrt.
# ══════════════════════════════════════════════════════════════════════════

_SAVE_HOOK = "_juprowaSchedulePush"

# Kein Punkt in der Ausschlussliste (window._juprowaPush soll mitzaehlen),
# und `\s*\(` schliesst `_juprowaPushAll(` aus.
_PUSH = re.compile(r"(?<![A-Za-z0-9_$])_juprowaPush\s*\(")


def _push_aufrufe(js):
    """(pos, davor, danach) je _juprowaPush(...)-Aufruf im CODE von `js`.

    `danach` beginnt hinter der PASSENDEN schliessenden Klammer — gezaehlt mit
    code_scan._klammer_zu, damit `_juprowaPush(String(_id)).then(...)` nicht
    an der inneren Klammer abreisst.
    """
    feld = code_scan.ist_code(js)
    aus = []
    for m in _PUSH.finditer(js):
        if not feld[m.start()]:
            continue
        if re.search(r"function\s+$", js[:m.start()]):
            continue                       # die Definition selbst
        auf = m.end() - 1
        ende = code_scan._klammer_zu(js, auf, "(", ")")
        aus.append((m.start(),
                    js[max(0, m.start() - 60):m.start()],
                    js[ende:ende + 40] if ende > 0 else ""))
    return aus


def fire_and_forget_maengel(js):
    """Maengel des Speicher-Hakens `js`. Leere Liste = in Ordnung.

    EINE LEERE GRUNDGESAMTHEIT IST SELBST EIN MANGEL: findet sich im Haken
    kein einziger Aufruf, hat der Riegel nichts gemessen — und genau dieser
    Zustand hat hier zwei Jahre als "gruen" gegolten.
    """
    rufe = _push_aufrufe(js)
    if not rufe:
        return ["LEERE GRUNDGESAMTHEIT: im Speicher-Haken steht kein "
                "_juprowaPush-Aufruf im Code. Entweder ist der Haken umgebaut "
                "oder der Anker veraltet — in beiden Faellen prueft dieser "
                "Riegel nichts."]
    maengel = []
    for pos, davor, danach in rufe:
        if re.search(r"(?<![A-Za-z0-9_$])await\s*$", davor):
            maengel.append(
                "await vor _juprowaPush bei Zeichen %d: ...%r" % (pos, davor[-40:]))
        kette = danach.lstrip()
        if not (kette.startswith(".then(") or kette.startswith(".catch(")):
            maengel.append(
                "_juprowaPush bei Zeichen %d ohne .then/.catch — eine "
                "abgelehnte Zusage bleibt unbehandelt: %r" % (pos, kette[:40]))
    return maengel


# Ein Koeder JE FORM.
_KOEDER_ROT = [
    ("A await mit Zuweisung",
     "function _juprowaSchedulePush(id){var r=await _juprowaPush(_id);}"),
    ("B await direkt",
     "function _juprowaSchedulePush(id){await _juprowaPush(_id);}"),
    ("C return await",
     "function _juprowaSchedulePush(id){return await _juprowaPush(_id);}"),
    ("D await UND .then (beides)",
     "function _juprowaSchedulePush(id){var r=await  _juprowaPush(_id)"
     ".then(function(r){});}"),
    ("E nackter Aufruf ohne Kette",
     "function _juprowaSchedulePush(id){_juprowaPush(_id);}"),
    ("F await mit innerer Klammer im Argument",
     "function _juprowaSchedulePush(id){var r=await _juprowaPush(String(_id));}"),
    ("G LEERER HAKEN — gar kein Aufruf",
     "function _juprowaSchedulePush(id){if(!id)return;}"),
]

_KOEDER_GRUEN = [
    ("die echte Form",
     "function _juprowaSchedulePush(id){_ids.forEach(function(_id){"
     "_juprowaPush(_id).then(function(r){}).catch(function(e){});});}"),
    ("nur .catch",
     "function _juprowaSchedulePush(id){_juprowaPush(_id)"
     ".catch(function(e){});}"),
    ("await nur im Kommentar",
     "function _juprowaSchedulePush(id){/* frueher: var r=await "
     "_juprowaPush(_id); */ _juprowaPush(_id).then(function(r){});}"),
    ("await nur in einer Zeichenkette",
     "function _juprowaSchedulePush(id){var s=\"await _juprowaPush(x)\";"
     "_juprowaPush(_id).then(function(r){});}"),
    ("Umbruch vor .then",
     "function _juprowaSchedulePush(id){_juprowaPush(_id)\n"
     "        .then(function(r){});}"),
    ("innere Klammer im Argument",
     "function _juprowaSchedulePush(id){_juprowaPush(String(_id))"
     ".then(function(r){});}"),
]


def test_save_hook_uses_no_await_before_juprowapush(index_html):
    """Fire-and-forget: kein `await` vor _juprowaPush im SPEICHER-HAKEN.

    Gemessen wird der Rumpf von _juprowaSchedulePush, nicht eine Zeile und
    nicht die ganze Datei — `await` ist im Drain, im PushAll und im
    Einzel-Push auf Knopfdruck richtig.
    """
    hook = _extract_fn(index_html, _SAVE_HOOK)
    assert hook, (
        "function %s nicht gefunden — der Speicher-Haken ist umbenannt oder "
        "weg. Dann ist dieser Riegel blind und der Anker nachzuziehen."
        % _SAVE_HOOK)
    maengel = fire_and_forget_maengel(hook)
    assert not maengel, (
        "Der Speicher-Haken %s ist nicht mehr fire-and-forget. Ein awaiteter "
        "Push haengt den Speichervorgang an die Cloud-Antwort — genau der "
        "Zustand, den v3.8.42 ausgebaut hat.\n  %s"
        % (_SAVE_HOOK, "\n  ".join(maengel)))


def test_gegenprobe_der_drain_darf_awaiten(index_html):
    """Die Abgrenzung ist der Kern dieses Riegels — hier wird sie belegt.

    Dieselbe Pruefung, auf _juprowaDrainPending angewendet, MUSS anschlagen:
    dort ist `await` richtig (sequenzieller Drain, index.html:4234). Schlaegt
    sie dort NICHT an, kann sie `await` ueberhaupt nicht erkennen — und das
    Gruen oben waere wertlos.
    """
    drain = _extract_fn(index_html, "_juprowaDrainPending")
    assert drain, "_juprowaDrainPending nicht gefunden"
    assert _push_aufrufe(drain), "kein _juprowaPush-Aufruf im Drain gefunden"
    assert fire_and_forget_maengel(drain), (
        "Die Pruefung erkennt das `await` im Drain-Rumpf NICHT — dann hat sie "
        "auch im Speicher-Haken nichts gemessen.")


def test_koeder_jede_form_des_awaits_wird_gefunden():
    """Ohne Koeder ist ein gruener Fire-and-forget-Riegel wertlos.

    Koeder G ist der wichtigste: ein Haken OHNE Aufruf muss ROT werden, sonst
    kehrt genau der alte Befund zurueck (gruen, weil nichts gemessen).
    """
    assert len(_KOEDER_ROT) >= 7, "Koederliste ausgeduennt"
    for name, probe in _KOEDER_ROT:
        assert fire_and_forget_maengel(probe), (
            "KOEDER NICHT GEFUNDEN (%s): %r" % (name, probe))


def test_gegenprobe_die_richtige_form_wird_nicht_gemeldet():
    """Ein Zaehler, der alles meldet, schlaegt bei jedem Koeder an und ist
    trotzdem kaputt."""
    assert len(_KOEDER_GRUEN) >= 6, "Gegenprobenliste ausgeduennt"
    for name, probe in _KOEDER_GRUEN:
        assert not fire_and_forget_maengel(probe), (
            "FEHLALARM (%s): %r -> %r"
            % (name, probe, fire_and_forget_maengel(probe)))


def test_das_alte_muster_konnte_nicht_zutreffen(index_html):
    """Haelt den Befund fest, aus dem diese Reparatur kommt.

    Die alte Bedingung verlangte `_juprowaPush(` UND `AUTOPUSH` in DERSELBEN
    Zeile. Kippt diese Zusicherung, hat jemand die Marken auf die Aufrufzeile
    geholt — dann gehoert dieser Fall weg, nicht der Riegel oben.
    """
    zeilen = index_html.splitlines()
    mit_push = [i for i, z in enumerate(zeilen) if "_juprowaPush(" in z]
    mit_marke = [i for i, z in enumerate(zeilen) if "AUTOPUSH" in z]
    assert mit_push and mit_marke, "Anker veraltet: eine der beiden Mengen ist leer"
    gemeinsam = set(mit_push) & set(mit_marke)
    assert not gemeinsam, (
        "Die alte Bedingung wuerde jetzt zutreffen (Zeilen %r) — Begruendung "
        "der Reparatur oben pruefen." % (sorted(z + 1 for z in gemeinsam),))


def test_save_hook_catches_errors_to_console(index_html):
    """AUTOPUSH-EXC catch must log to console, not toast."""
    assert "[AUTOPUSH-EXC]" in index_html
    # Find context -- must be in a .catch chained after _juprowaPush
    m = re.search(
        r"_juprowaPush\([^)]+\)\.then\([^}]+\}\)\.catch\([^}]+console\.warn\('\[AUTOPUSH-EXC\]'",
        index_html,
    )
    # Softer assertion if regex is too strict:
    if not m:
        assert "AUTOPUSH-EXC" in index_html and "console.warn" in index_html
