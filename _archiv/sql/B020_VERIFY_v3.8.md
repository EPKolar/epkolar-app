# B-020 Final-Verify · Login-Regression · v3.7.7

## Status DB-Seite (vor Run)

Sebastian bestätigte am 19.04 ~14:00: Final-Verify-Query aus `sql/B020_FIX.sql` Schritt 4 zeigte **9× OK** (alle 9 User haben email + auth_user_id + matching auth.users row). DB-Teil ist abgeschlossen.

## Login-Regression pro User

Sebastian durchläuft nach v3.8-Deploy: je User `{username}/test1234` einloggen, prüfen:

| User | Username | Email | Role | Expected Dashboard-Tabs | PASS/FAIL | Notiz |
|---|---|---|---|---|---|---|
| u1 | paschinger | paschinger@ep-kolar.at | monteur | Home, Projekte, AS, Zeit, Urlaub, Fahrzeuge, Werkzeuge, Einstellungen | __ | __ |
| u2 | barger | barger@ep-kolar.at | monteur | wie u1 | __ | __ |
| u3 | cracana | cracana@ep-kolar.at | monteur | wie u1 | __ | __ |
| u4 | pinger | pinger@ep-kolar.at | projektleiter | Home, Chef?, Projekte, AS, Planung, Zeit, Urlaub, Stunden, Fahrzeuge, Werkzeuge, MA, Auswertungen, Einstellungen | __ | __ |
| u5 | schmid | schmid@ep-kolar.at | monteur | wie u1 | __ | __ |
| u6 | guenther | guenther@ep-kolar.at | admin | alle inkl. Chef, Admin | __ | __ |
| u7 | schober | info@ep-kolar.at | buero | Home, Projekte, AS, Planung, Zeit, Urlaub, Stunden, Fahrzeuge, Werkzeuge, MA, Auswertungen, Einstellungen, Büro-Export | __ | __ |
| u8 | lindhuber | lindhuber@ep-kolar.at | buero | wie u7 | __ | __ |
| — | riedmann | ? | ? | ? | __ | __ |

## Error-Code-Assertions

### B20-A: HTTP-Fail bei login_lookup
Wird getriggert wenn Supabase REST nicht erreichbar ist. Test: DevTools → Network → throttle "Offline" → Login-Attempt → Console sollte `[B020-A] login_lookup HTTP-Fail` zeigen + Toast "Server nicht erreichbar [B20-A]".

### B20-B: Benutzer nicht gefunden
Test: falsche Username (z.B. `xyz_nonexistent`) → Toast "Benutzer nicht gefunden [B20-B]".

### B20-C: User gesperrt
Test: In DB `UPDATE users SET locked=true WHERE id='u1'` (ACHTUNG: danach wieder auf false!) → Toast "Benutzer gesperrt [B20-C]".

### B20-D: Falsches Passwort
Test: richtiges username, falsches PW → Toast "Falsches Passwort [B20-D]".

### B20-F: Empty email (sollte nach DB-Fix nicht mehr auftreten)
Test: In DB `UPDATE users SET email='' WHERE id='u1'` → Login paschinger/test1234 → Toast "Account unvollständig [B20-F]".
Danach sofort Rollback `UPDATE users SET email='paschinger@ep-kolar.at' WHERE id='u1'`.

### B20-G: Bcrypt OK aber GoTrue-Signup fail
Schwer zu triggern ohne DB-State zu verändern. Skip wenn zu riskant.

### B20-H: _authToken null nach Auth-Flow
Belt-and-braces guard. Sollte **nie** auftreten. Wenn doch: Log-Forensik in activity_log (action=react_error oder console.error).

## Token-Refresh nach 1h

Zwei Möglichkeiten:

### Option A: Warten (wenn Test-Umgebung)
1. Login als admin.
2. `localStorage.getItem('epkolar_auth')` — `exp` merken.
3. 1h warten ohne Browser-Tab zu schließen.
4. Eine _sb*-Aktion (z.B. "Projekte laden") → sollte silent refresh + request succeed.
5. Console: `[Auth] Silent re-auth OK → request recovered` erwartet.
6. Network-Tab: GENAU 1 `/auth/v1/token?grant_type=refresh_token` Call.

### Option B: Force via _forceExpireToken (ab v3.7.7 verfügbar)
1. `localStorage.setItem('__dev','1')`
2. `window._forceExpireToken()` → Toast ok.
3. Irgendein _sb*-Call (z.B. `_sbGet('projects','limit=1')`).
4. Console: `[Auth] Silent re-auth OK → request recovered`.
5. Network-Tab: 1× refresh_token, 1× retry-call mit frischem Token.
6. `window._restoreToken()` + Seite neu laden für Clean-State.

## Verify-Ergebnis

*(Nach Durchlauf ausfüllen)*

- Login-Regression 9+1 User: __/9 PASS
- Error-Codes B20-A..D getestet: __/4 PASS
- Token-Refresh (Option A oder B): PASS/FAIL
- **Gesamt-Verdict**: __
