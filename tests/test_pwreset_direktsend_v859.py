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
    # v3.9.1056 Auth-Pruefung Fund 4: der Direkt-Send aus v3.9.859 war selbst ein Falschgruen - der Handler las
    # users ANONYM (RLS: immer leer) und meldete trotzdem "gesendet". Jetzt ruft die Maske die RPC
    # passwort_hilfe_anfragen ueber _passwortHilfeAnfragen; Erfolg nur bei ok:true. Gemessen wird das in
    # tests/test_auth_haertung_v1056.py (Node fuehrt die echte Funktion aus).
    assert 'r=await _passwortHilfeAnfragen(_u)' in index_html
    assert 'setResetMsg("✅ Anfrage an den Admin gesendet.")' not in index_html
    # Fehlerfall wird ehrlich gemeldet (kein grünes OK bei Fehlschlag)
    assert 'Bitte wende dich direkt an das Büro oder den Admin.' in index_html


def test_handler_braucht_keine_user_auth(index_html):
    # Gegenprobe: der Zielhandler erzeugt Admin-Notifications (kein User-Auth-Pfad)
    assert 'if(resource==="password-reset"&&method==="POST"){' in index_html
