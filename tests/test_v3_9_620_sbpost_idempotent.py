"""v3.9.620 #17 — Idempotenz des generischen Schreib-POST (_sbPost-Pfad).

Bug: Der generische POST-Zweig in _translateAndExec nutzte Plain-INSERT (_sbPost).
Geht die HTTP-Antwort verloren (Server-Insert lief, Client sieht Timeout), löst der
Retry einen zweiten INSERT aus -> 409 -> Record-Drop + falsche Fehler-Warnung
(gleiche stiller-Misserfolg-Klasse wie #9/#14/#18, nur Schreibpfad).

Fix: Body mit stabiler Client-id (PK) -> _sbInsertIfAbsent (resolution=ignore-duplicates,
ON CONFLICT PK DO NOTHING), exakt das beim Juprowa-Pull/arbeitsscheine bewährte Muster.
Retry kollidiert auf dem PK -> idempotent, kein 409-Drop. Andere Unique-Verletzungen
(Conflict-Target = PK) propagieren weiterhin als Fehler. Body OHNE id -> unverändert
Plain-_sbPost (keine Drain-Zeit-id-Generierung, die beim Retry duplizieren würde).

Static-Source-Regression-Guards (Laufzeit-Replay ist im pytest-String-Harness nicht
abbildbar; geprüft wird die idempotente Verdrahtung + Fehler-Propagation am echten Code).
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def _txt():
    return INDEX.read_text(encoding='utf-8')


def test_generic_post_idempotent_route_for_id_bodies():
    """Der generische POST-Zweig routet Bodies mit stabiler id über _sbInsertIfAbsent (idempotent)."""
    t = _txt()
    assert 'else if(mapped&&mapped.id){await _sbInsertIfAbsent(table,mapped);' in t, \
        '#17 Regression: generischer POST mit id muss idempotent via _sbInsertIfAbsent laufen'


def test_id_less_post_stays_plain_sbpost():
    """Body OHNE id bleibt Plain-_sbPost (kein Drain-Zeit-id-Anker -> kein Retry-Duplikat)."""
    t = _txt()
    # Fallback-else direkt nach dem idempotenten Zweig
    assert re.search(
        r'else if\(mapped&&mapped\.id\)\{await _sbInsertIfAbsent\(table,mapped\);.*?\}\s*'
        r'else\{await _sbPost\(table,mapped,table==="notifications"\);',
        t, re.S), '#17: id-loser POST muss unverändert auf _sbPost fallen'


def test_sbinsertifabsent_uses_ignore_duplicates():
    """_sbInsertIfAbsent nutzt resolution=ignore-duplicates (PK-Conflict DO NOTHING)."""
    t = _txt()
    assert 'return=minimal,resolution=ignore-duplicates' in t, \
        '_sbInsertIfAbsent muss resolution=ignore-duplicates verwenden'


def test_sbinsertifabsent_propagates_real_errors():
    """Echte Insert-Fehler (4xx/5xx, kein Dedup) propagieren weiterhin als Error (kein stiller Erfolg)."""
    t = _txt()
    m = re.search(r'async function _sbInsertIfAbsent\(table,data\)\{.*?\n\}', t, re.S)
    assert m, '_sbInsertIfAbsent nicht gefunden'
    body = m.group(0)
    assert 'if(!r.ok)' in body and 'throw new Error' in body, \
        '_sbInsertIfAbsent muss bei !r.ok werfen (Fehler-Propagation, kein stiller Drop)'
