"""v3.9.154 — Security: Portal-Token crypto-Random (statt Math.random 4-stellig)."""


def test_token_uses_crypto(index_html):
    assert 'window.crypto.getRandomValues(new Uint8Array(6))' in index_html
    assert 'const _alpha="ABCDEFGHJKMNPQRSTUVWXYZ23456789";' in index_html
    # alte schwache Variante weg
    assert 'String(Math.floor(1000+Math.random()*9000))' not in index_html
