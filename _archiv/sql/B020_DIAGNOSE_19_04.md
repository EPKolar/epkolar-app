# B-020 Diagnose — UI-Login silent fail · 19.04.2026

## Ist-Zustand
Sebastian berichtet: Login mit `schober / test1234` → Screen bleibt leer, kein Dashboard, kein Error-Toast.

## Code-Analyse

### Login-Handler (index.html line 1204-1240)

```
async function login(u, p) {
  const rpcRes = await fetch(SB_REST+"/rpc/login_lookup", {...p_username:u});  // line 1207
  if(!rpcRes.ok) throw "Server nicht erreichbar";                                // line 1208
  const user = await rpcRes.json();                                               // line 1209
  if(!user || !user.id) throw "Benutzer nicht gefunden";                          // line 1210
  if(user.locked) throw "Benutzer gesperrt";                                      // line 1211
  const email = user.email || (u+"@epkolar.local");                               // line 1212
  // GoTrue try
  try { _sbAuthLogin(email, p); _storeAuth(authData); gotrue=true; }             // line 1215
  catch(authErr) {
    // bcrypt fallback
    if(!bcrypt.compareSync(p, user.password_hash)) throw "Falsches Passwort";    // line 1218-1219
    // Try GoTrue auto-signup
    fetch(SB_AUTH+"/signup", {...email,password:p});                             // line 1222
    ...
  }
  return { token: 'supabase-session', user: userData };                          // line 1239
}
```

### UI-Caller (index.html line 2887-2922, LoginScreen)

```
const tryLogin = async () => {
  if(!user.trim()||!pw) { setErr("Benutzername und Passwort"); return; }
  setLoading(true); setErr("");
  try {
    const data = await API.login(user, pw);   // line 2901
    API.setToken(data.token);                 // line 2902
    await ODB.set(...);                        // line 2903
    onLogin(data.user);                       // line 2904 — setCurUser(u)
  } catch(e) {
    if(!navigator.onLine) { ...offline fallback... }
    else setErr(e.message || "Login fehlgeschlagen");   // line 2917 — err IS rendered
    setShake(true);
  }
  setLoading(false);
};
```

`err` wird gerendert bei line 2948 (`err && React.createElement('div', ..., "⚠️ "+err)`). Also sollte ein Error-Toast sichtbar sein — **es sei denn der Login wirft keine Exception aber curUser wird trotzdem nicht gesetzt**.

## Reproducer (für Sebastian)

1. App öffnen → Login-Maske
2. Username "schober", Passwort "test1234"
3. Submit
4. F12 Console öffnen vor Submit — achten auf:
   - Network-Tab: `login_lookup` RPC-Call → Status 200? Body = `[{...}]` (Array) oder `{...}` (Object)?
   - Console: JS-Fehler oder stack trace?
   - React: re-rendert `LoginScreen` weiter mit err="" oder err="irgendwas"?

## Hypothesen (priorisiert)

### H1 (WAHRSCHEINLICHSTE): RPC `login_lookup` liefert Array statt Single-Row
Wenn die SQL-Funktion `login_lookup(p_username)` mit `RETURNS TABLE(...)` oder `RETURNS SETOF users` definiert ist, liefert Supabase REST ein Array (z.B. `[{id:"u7", ...}]`). Dann:
- Line 1209: `user = [{...}]` (Array)
- Line 1210: `!user` → false, `!user.id` → true (Array hat kein `.id`) → `throw "Benutzer nicht gefunden"`
- Error-Toast MÜSSTE erscheinen.

→ **Aber**: Sebastian sieht KEIN Error-Toast. Widerspruch — es sei denn der Error wird zwischen setErr und render geworfen.

### H2: `_storeAuth` akzeptiert broken Response silent, `_authToken` bleibt null
Line 615: `if(!_isJwtShape(d.access_token)) { console.warn(...); return; }` — ohne throw.
Wenn GoTrue 200 OK mit broken payload liefert:
- `_storeAuth` logged warn, returniert
- `_authToken` bleibt null
- `gotrue=true` ist NICHT gesetzt (liegt VOR `_storeAuth`-Call in line 1215)
- catch(authErr) wird nicht betreten (kein throw)
- → Code läuft weiter ohne `_authToken`

→ userData wird trotzdem gebaut (line 1235), `onLogin(data.user)` wird aufgerufen → curUser gesetzt.
→ Dashboard sollte rendern. KEIN blank-screen durch diesen Pfad.

### H3: Session-Fortschaltung: login succeeds → dashboard render crasht → ErrorBoundary zeigt NICHTS weil err="..." aber boundary rendert oberhalb
Die `EpkErrorBoundary` (line 15307) zeigt UI bei Render-Crash. Wenn sie korrekt fängt, sieht User die "App-Fehler aufgetreten"-UI — nicht blank.
→ Nicht plausibel als Erklärung für "blank screen".

### H4: Login-Erfolg, setState läuft, aber WEBWORKER-Konflikt / StrictMode oder SW-Update-Kollision löscht curUser wieder
Wenn ServiceWorker-Update mitten im Login feuert (postMessage `SW_UPDATED`) könnte ein Race entstehen. Unwahrscheinlich für "ersten" Login-Versuch.

### H5: schober-User hat irgendwas Kaputtes in auth.users (wie info@/office@ in B-018)
Analog zu prev Handoff-Note "Auth-500 bei info@/office@": schober's `auth.users`-Row könnte NULL-Traps haben.
- GoTrue login wirft → catch
- bcrypt fallback: `user.password_hash` könnte NULL/invalid sein → `bcrypt.compareSync` catched Error, valid=false → `throw "Falsches Passwort"`
- Error müsste im UI sichtbar sein.

## Wahrscheinlichste Realität

Der beobachtete "blank screen" + "kein Error" ist ohne Browser-DevTools-Session nicht belegbar. **Der Code-Pfad zeigt keinen Ausweg ohne Error-Toast oder ohne setCurUser**. Daher ist die nächste Action:

### Empfohlene nächste Schritte für Sebastian (5 min in Browser)
1. F12 öffnen, Console + Network aktiv
2. Login-Attempt mit schober/test1234
3. Screenshot/Paste:
   - RPC `login_lookup` Response-Body (Array oder Object?)
   - Console-Errors (falls JS-Throw)
   - LocalStorage-State (`epkolar_token`, `epkolar_refresh`, `epkolar_user`)
4. Dann in nächster Session gezielt patchen.

## Fix-Vorschlag (falls H1 bestätigt wird)

Line 1209-1210 ersetzen:
```js
const userData = await rpcRes.json();
const user = Array.isArray(userData) ? userData[0] : userData;
if(!user || !user.id) throw new Error("Benutzer nicht gefunden");
```

## Status
**STATUS: in-progress** — Diagnose committed, kein Patch (Ursache ohne DB/Browser-Session nicht eindeutig).

Nächster Schritt: Sebastian liefert F12-Artefakte, dann gezielter Fix in nächstem Schuss.
