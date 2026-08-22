"""
v3.9.859 — "Passwort vergessen"-Anfrage erreicht den Admin (Onboarding-Agent, P1).

Vorher: der Absende-Button (:6573) setzte `setResetMsg("✅ Anfrage gesendet an
Admin.")` VOR einem `SQ.push({url:"/api/password-reset"})`, der nie flushte —
`doSync` bricht bei `!_authToken` ab, und der Anfragende ist per Definition NICHT
eingeloggt (Passwort vergessen) → das Item blieb ewig in der Queue, der Admin
bekam nie die Notification, der User sah trotzdem grünes OK. Fix: Direkt-Send via
`_translateAndExec` + ehrliche ergebnis-basierte Meldung.
"""


def test_kein_falschgruen_vor_sq_push(index_html):
    # der alte Falschgruen-vor-SQ.push-Pfad ist weg
    assert 'setResetMsg("✅ Anfrage gesendet an Admin.");SQ.push({url:"/api/password-reset"' not in index_html


def test_direktsend_via_translateandexec(index_html):
    assert 'await _translateAndExec("/api/password-reset","POST",{username:_u});setResetMsg("✅ Anfrage an den Admin gesendet.");' in index_html
    # Fehlerfall wird ehrlich gemeldet (kein grünes OK bei Fehlschlag)
    assert 'catch(_pre){console.warn(\'[pw-reset]\',_pre&&_pre.message||_pre);setResetMsg("⚠️ Konnte nicht gesendet werden' in index_html


def test_handler_braucht_keine_user_auth(index_html):
    # Gegenprobe: der Zielhandler erzeugt Admin-Notifications (kein User-Auth-Pfad)
    assert 'if(resource==="password-reset"&&method==="POST"){' in index_html
