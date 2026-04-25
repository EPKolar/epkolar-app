"""
Statischer Test: _silentReAuth zeigt einen User-sichtbaren Toast und triggert
einen Reload, statt App in stillem broken-State weiterlaufen zu lassen.

Hintergrund: 25.04.2026 Live-Bug. Bei Supabase refresh-token-rotation 400 ist
_silentReAuth aufgerufen worden, hat _authToken+_authRefreshToken auf null
gesetzt und null returned. App-Layer hat das nicht bemerkt — nachfolgende
DB-Reads gingen mit kaputten Auth-Headers raus, RLS-Block lieferte 200 +
leere Daten, App zeigte cached IndexedDB-State.

Fix v3.8.52: _silentReAuth feuert Toast + cleart localStorage-Auth + reloadet
die Seite (2sec delay damit Toast lesbar ist).
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'

def _get_silent_reauth_body():
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'async function _silentReAuth\(\)\{(.*?)^\}', text, re.DOTALL | re.MULTILINE)
    assert m, '_silentReAuth definition not found'
    return m.group(1)

def test_silent_reauth_calls_toast():
    body = _get_silent_reauth_body()
    assert 'window.__toast' in body, '_silentReAuth muss window.__toast aufrufen damit User sieht dass Sitzung abgelaufen ist'

def test_silent_reauth_clears_localstorage():
    body = _get_silent_reauth_body()
    assert 'localStorage.removeItem' in body, '_silentReAuth muss localStorage-Auth-Keys löschen'
    assert 'epkolar_auth' in body, 'epkolar_auth-Key muss gelöscht werden'

def test_silent_reauth_triggers_reload():
    body = _get_silent_reauth_body()
    assert 'location.reload' in body, '_silentReAuth muss location.reload triggern damit App in LoginScreen kommt'
    assert 'setTimeout' in body, 'Reload muss verzögert sein (setTimeout) damit Toast lesbar bleibt'

def test_silent_reauth_still_nulls_tokens():
    body = _get_silent_reauth_body()
    assert '_authToken=null' in body, 'Token-Reset muss erhalten bleiben'
    assert '_authRefreshToken=null' in body, 'RefreshToken-Reset muss erhalten bleiben'

if __name__ == '__main__':
    test_silent_reauth_calls_toast()
    test_silent_reauth_clears_localstorage()
    test_silent_reauth_triggers_reload()
    test_silent_reauth_still_nulls_tokens()
    print("OK — _silentReAuth force-logout pattern intact")
