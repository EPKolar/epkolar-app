"""v3.9.9 Sprint-15 S15-3: SQ.push & PhotoQ.add nutzen crypto.randomUUID() mit Date.now()-Fallback.

Regression-Guards für die UUID-Migration: Beide Offline-Queues müssen statt der alten
`Date.now()+Math.random()`-Kombination jetzt `crypto.randomUUID()` mit Safety-Fallback verwenden,
damit IDs kollisionssicher und kryptographisch zufällig sind.
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def _sq_push_block(text: str) -> str:
    """Extrahiert den SQ.push-Body (zwischen `const SQ={` und schließendem `};`)."""
    m = re.search(r'const\s+SQ\s*=\s*\{[\s\S]*?\n\};', text)
    assert m, 'v3.9.9 S15-3 Regression: SQ-Object nicht gefunden (const SQ={...};)'
    sq_body = m.group(0)
    push_m = re.search(r'async\s+push\s*\(\s*action\s*\)\s*\{[\s\S]*?\n\s*\},', sq_body)
    assert push_m, 'v3.9.9 S15-3 Regression: SQ.push-Methode nicht im SQ-Object gefunden'
    return push_m.group(0)


def _photoq_add_block(text: str) -> str:
    """Extrahiert den PhotoQ.add-Body (zwischen `const PhotoQ={` und Methode add)."""
    m = re.search(r'const\s+PhotoQ\s*=\s*\{[\s\S]*?\n\};', text)
    assert m, 'v3.9.9 S15-3 Regression: PhotoQ-Object nicht gefunden (const PhotoQ={...};)'
    pq_body = m.group(0)
    add_m = re.search(r'async\s+add\s*\(\s*photo\s*\)\s*\{[\s\S]*?\n\s*\},', pq_body)
    assert add_m, 'v3.9.9 S15-3 Regression: PhotoQ.add-Methode nicht im PhotoQ-Object gefunden'
    return add_m.group(0)


def test_syncqueue_uses_crypto_randomuuid():
    """SQ.push muss crypto.randomUUID() mit Date.now()-Fallback für die action.id verwenden."""
    text = INDEX.read_text(encoding='utf-8')
    push_body = _sq_push_block(text)
    assert re.search(r'crypto\.randomUUID\(\)', push_body), (
        'v3.9.9 S15-3 Regression: SQ.push muss crypto.randomUUID() verwenden — '
        'kollisionssichere UUID-IDs sind Pflicht für Offline-Queue-Dedup.'
    )
    assert re.search(r'Date\.now\(\)', push_body), (
        'v3.9.9 S15-3 Regression: SQ.push muss Date.now() als Fallback behalten — '
        'iOS <15.4 und ältere Browser haben kein crypto.randomUUID().'
    )


def test_photoqueue_uses_crypto_randomuuid():
    """PhotoQ.add muss crypto.randomUUID() für die photo.id verwenden (mit photo.id-Override)."""
    text = INDEX.read_text(encoding='utf-8')
    add_body = _photoq_add_block(text)
    assert re.search(r'crypto\.randomUUID\(\)', add_body), (
        'v3.9.9 S15-3 Regression: PhotoQ.add muss crypto.randomUUID() verwenden — '
        'kollisionssichere UUID-IDs sind Pflicht für Foto-Offline-Queue-Dedup.'
    )
    # Fallback-Kette: photo.id || crypto.randomUUID() || Date.now()+Math.random()
    assert re.search(r'photo\.id\s*\|\|', add_body), (
        'v3.9.9 S15-3 Regression: PhotoQ.add muss photo.id-Override behalten (photo.id||...)'
    )


def test_fallback_pattern_preserved():
    """Beide Stellen müssen typeof-crypto-Safety-Check behalten (iOS <15.4 Compat)."""
    text = INDEX.read_text(encoding='utf-8')
    push_body = _sq_push_block(text)
    add_body = _photoq_add_block(text)
    pattern = r'typeof\s+crypto\s*!==?\s*["\']undefined["\']'
    assert re.search(pattern, push_body), (
        'v3.9.9 S15-3 Regression: SQ.push muss `typeof crypto!=="undefined"`-Safety behalten — '
        'sonst crasht der Code in alten WebViews ohne crypto-API.'
    )
    assert re.search(pattern, add_body), (
        'v3.9.9 S15-3 Regression: PhotoQ.add muss `typeof crypto!=="undefined"`-Safety behalten — '
        'sonst crasht der Code in alten WebViews ohne crypto-API.'
    )
    # Beide Stellen müssen den Fallback-Pfad (Date.now+Math.random) als safety-net behalten
    assert len(re.findall(r'Date\.now\(\)\+["\']?_?["\']?\+?Math\.random', push_body + add_body)) >= 2, (
        'v3.9.9 S15-3 Regression: Date.now()+Math.random()-Fallback muss in beiden Queues erhalten bleiben.'
    )
