# B-E Edge-Function Plan — admin-create-user (Sebastian-Spec v3.10.0)

**Agent:** B4 | **Datum:** 2026-06-03 | **Repo:** epkolar-app | **Sprint:** 80 (Docs)

---

## 1. Problem-Analyse

### 1.1 Symptom (Sebastian-Befund B-E)
- AdminPanel `createUser` (`index.html` Z7308-7336) ruft nach lokalem State-Update den RPC `/rpc/admin_reset_password` mit **User-JWT**.
- Toast meldet "✅ Benutzer angelegt", aber **GoTrue (auth.users) hat keine neue Row**.
- DB-Konsequenz: `public.users`-Row vorhanden, aber `auth_user_id IS NULL` UND `monteur_id IS NULL` UND keine `auth.users`-Row → User kann sich **nie einloggen**, und alle role-by-auth-Joins (RLS, `login_lookup`, Settings-Tests) gehen schief.

### 1.2 Root-Cause
- `auth.admin.createUser`, `auth.admin.updateUserById`, `auth.admin.deleteUser` sind **service_role-gated**.
- User-JWT (anon-Layer) hat **keine Berechtigung**, diese Endpoints zu callen.
- Der bisherige RPC `admin_reset_password` ist eine SECURITY-DEFINER-Funktion, aber sie verlässt sich auf vorher existierende `auth.users`-Row (nur PW-Reset, kein Create). Bei Neuanlage existiert die Row nicht → RPC failt silent, lokaler State + SyncQueue-Push macht trotzdem `public.users`-INSERT → halb-angelegter User.
- Sprint 78 P2-4-Skip war **falsch** — B-E sitzt genau hier.

### 1.3 Sebastian-Spec
> "auth via Edge-Function/service_role, konsistente Verknüpfung erzwingen"

---

## 2. Edge-Function-Architektur

### 2.1 Pfad
```
supabase/functions/admin-create-user/index.ts
```

### 2.2 Aufruf-Kontrakt
**Request:**
```
POST {SUPABASE_URL}/functions/v1/admin-create-user
Headers:
  Authorization: Bearer <user-jwt>     (Admin-Caller-JWT)
  Content-Type: application/json
  apikey: <SUPABASE_ANON_KEY>
Body:
  { username, name, email, password, role, monteurId? }
```

**Response 200 (Success):**
```json
{
  "ok": true,
  "user": {
    "id": "u...",
    "username": "...",
    "name": "...",
    "email": "...",
    "role": "...",
    "monteur_id": "w..." | null,
    "auth_user_id": "<uuid>",
    "active": true,
    "locked": false
  },
  "workerCreated": true | false
}
```

**Error-Codes:**
| Status | error | Bedeutung |
|--------|-------|-----------|
| 400 | `validation` | input fehlerhaft (details enthält Feldname) |
| 401 | `unauthorized` | kein/ungültiger Caller-JWT |
| 403 | `forbidden` | Caller ist nicht active+unlocked admin |
| 405 | `method_not_allowed` | ≠ POST/OPTIONS |
| 409 | `conflict` | username oder email schon vergeben (idempotent) |
| 500 | `internal` | service-Fehler; `rolledBack:true` wenn Cleanup-Pfad gelaufen |

### 2.3 Atomarer Workflow

```
[1] CORS / OPTIONS preflight
[2] Method == POST ?                  → 405 wenn nicht
[3] Env-Check (URL, SERVICE_KEY, ANON_KEY)
[4] Caller-JWT aus Authorization-Header
[5] callerClient (anon + Bearer JWT) → auth.getUser() → caller_auth_uid
[6] adminClient (service_role) → public.users.select(*) where auth_user_id=caller_auth_uid
[7] Caller-role == 'admin' && active && !locked ?  → 403 wenn nicht
[8] body parse + validate() (alle Felder, password ≥4, email valid, role whitelisted)
[9] Conflict-Pre-Check: public.users where username=X OR email=Y  → 409 wenn match
[10] auth.admin.createUser({email, password, email_confirm:true,
                             user_metadata:{username,name,role}})  → AUTH_UUID
[11] OPTIONAL Worker-Row:
     - falls monteurId leer UND role IN ('monteur','techniker')
     - INSERT workers {id:wXXX, name, role, active:true}
     - bei Fehler: Rollback auth.users (deleteUser)  → 500 rolledBack
[12] INSERT public.users {id:uXXX, username, name, email, role,
                          monteur_id, auth_user_id, active:true, locked:false}
     - bei Fehler: Rollback auth.users + (falls workerCreated) workers  → 500 rolledBack
[13] Return 200 {ok, user, workerCreated}
```

### 2.4 Konsistenz-Constraints (Empfehlung)

Vor Deploy in Supabase verifizieren (siehe Verify-SQL §5):
- `public.users.username` UNIQUE
- `public.users.email` UNIQUE
- `public.users.auth_user_id` UNIQUE (allowing NULL für Legacy)
- nach Deploy: alle **neu angelegten** Rows haben `auth_user_id NOT NULL` (kein DB-Constraint, sondern App-Invariante).

---

## 3. Deploy-Steps für Sebastian

### 3.1 Voraussetzungen (lokal)
- Supabase-CLI installiert (`scoop install supabase` oder `npm i -g supabase`).
- Logged in: `supabase login`.
- Projekt verlinkt: `supabase link --project-ref jiggujpruejkaomgxarp` (im Repo-Root einmalig).

### 3.2 Deploy
```bash
cd "\\SRVDC02\Projekte\05_Claude\02_Baumanagment & Zeiterfassungs - APP\03_Repos\epkolar-app"
supabase functions deploy admin-create-user --no-verify-jwt
```

**Warum `--no-verify-jwt`:**
Edge-Function macht eigene Caller-Verifikation (siehe §2.3 Schritt 5+7).
Ohne `--no-verify-jwt` lehnt Supabase Calls ab, wo der JWT nicht zum Auth-User des Projekts gehört — bei uns ist Caller selbst admin, das wollen wir behalten, aber **wir prüfen die Admin-Role gegen `public.users` selbst**, nicht via GoTrue-Role. Beide Modi funktionieren; falls Sebastian `--verify-jwt` (default) bevorzugt: Caller-JWT muss ein gültiger GoTrue-Session-JWT sein (ist er bei eingeloggtem Admin sowieso) — dann reicht die Default-Verifikation und die explizite `auth.getUser()`-Prüfung in der Function ist redundant aber harmlos.

**Empfehlung:** Default lassen (`supabase functions deploy admin-create-user`), Edge-Function verifiziert zusätzlich.

### 3.3 Env-Vars
Supabase setzt **automatisch** beim Deploy:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`

Kein manuelles `supabase secrets set` nötig.

### 3.4 Smoke-Test (curl)
Im Browser-DevTools-Console eingeloggt als Admin:
```js
const sess = JSON.parse(localStorage.getItem('sb-jiggujpruejkaomgxarp-auth-token'));
const r = await fetch('https://jiggujpruejkaomgxarp.supabase.co/functions/v1/admin-create-user', {
  method:'POST',
  headers:{
    'Authorization':'Bearer '+sess.access_token,
    'apikey':'<ANON_KEY>',
    'Content-Type':'application/json'
  },
  body: JSON.stringify({
    username:'testuser1',
    name:'Test User 1',
    email:'testuser1+test@ep-kolar.at',
    password:'test1234',
    role:'monteur'
  })
});
console.log(r.status, await r.json());
```

Erwartete Antwort: `200 { ok:true, user:{...auth_user_id:"<uuid>"}, workerCreated:true }`.

---

## 4. Client-Code-Patch (NICHT applien — Sprint 79 läuft parallel)

**Ziel:** `index.html` Z7321-7333 ersetzen. **DRAFT für Sprint 80 nach Sprint 79-Merge.**

```js
// ALT (Z7321-7333):
const nid=uid();
const email=nf.email.trim();
setUsers(prev=>[...prev,{id:nid,username:nf.username,name:nf.name,email,role:nf.role,active:true,monteurId:nf.monteurId||null,lastLogin:null,created:td2(),locked:false,permsOverride:null}]);
SQ.push({url:"/api/users",method:"POST",body:{id:nid,username:nf.username,password:nf.password,name:nf.name,email,role:nf.role,monteurId:nf.monteurId||null,active:1,locked:0}});
let _pwRpcOk=true;
try{
  const _r=await _authRetry(()=>fetch(SB_REST+"/rpc/admin_reset_password",_fT({method:"POST",headers:_sbH(),body:JSON.stringify({p_email:email,p_password:nf.password})})));
  if(!_r||!_r.ok){_pwRpcOk=false;console.error('[createUser] admin_reset_password failed:',_r&&_r.status,await (_r&&_r.text().catch(()=>''))||'');}
}catch(e){_pwRpcOk=false;console.error('[createUser] admin_reset_password threw:',e&&e.message||e);}
if(!_pwRpcOk){
  window.__toast?.("⚠️ Benutzer angelegt, ABER GoTrue-Passwort-Setup fehlgeschlagen ...","warn",10000);
} else {
  window.__toast?.("✅ Benutzer angelegt");
}

// NEU (B-E Edge-Function, atomar):
const email = nf.email.trim().toLowerCase();
let resp;
try{
  resp = await _authRetry(() => fetch(`${SUPABASE_URL}/functions/v1/admin-create-user`, _fT({
    method: "POST",
    headers: { ..._sbWH(), "Content-Type": "application/json" },
    body: JSON.stringify({
      username: nf.username,
      name:     nf.name,
      email,
      password: nf.password,
      role:     nf.role,
      monteurId: nf.monteurId || null
    })
  }, 15000)));
}catch(e){
  console.error('[createUser] edge-fn threw:', e?.message || e);
  window.__toast?.("⚠️ Benutzer-Anlage fehlgeschlagen (Netzwerk)", "error", 8000);
  _creatingUser.current = false;
  return;
}
if (!resp || !resp.ok) {
  const errText = resp ? await resp.text().catch(()=>'') : '';
  console.error('[createUser] edge-fn status:', resp?.status, errText);
  window.__toast?.(`⚠️ Benutzer-Anlage fehlgeschlagen: ${resp?.status || 'no-resp'}`, "error", 8000);
  _creatingUser.current = false;
  return;
}
const payload = await resp.json();
if (!payload?.ok || !payload?.user) {
  window.__toast?.(`⚠️ Anlage fehlgeschlagen: ${payload?.details || payload?.error || 'unknown'}`, "error", 8000);
  _creatingUser.current = false;
  return;
}
const u = payload.user;
setUsers(prev => [...prev, {
  id: u.id, username: u.username, name: u.name, email: u.email, role: u.role,
  active: !!u.active, locked: !!u.locked,
  monteurId: u.monteur_id || null,
  authUserId: u.auth_user_id,
  lastLogin: null, created: td2(), permsOverride: null
}]);
window.__toast?.("✅ Benutzer angelegt + verknüpft");
setNf({username:"",password:"",name:"",email:"",role:"monteur",monteurId:""});
setShowNew(false);
_creatingUser.current = false;
```

**Wichtige Änderungen:**
- Entfernt `SQ.push({url:"/api/users",method:"POST",...})` — Edge-Function macht DB-INSERT atomar.
- Entfernt `/rpc/admin_reset_password` Aufruf — auth.admin.createUser läuft im service_role-Kontext der Function.
- `setUsers` erst **nach** erfolgreicher Function-Response (kein optimistic-update mehr — Server ist Wahrheit).
- Tracking-Field `authUserId` zusätzlich in lokaler User-Row.

**Identische Behandlung in `pwReset` (Z7618):** analog ersetzen durch eigene Edge-Function `admin-reset-password` (separat, nicht Teil von B4 — Sprint 80 Folge-Task).

---

## 5. Verify-SQL (für Sebastian, nach Deploy)

```sql
-- §5.1 Schema-Check public.users
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema='public' AND table_name='users'
  AND column_name IN ('id','username','email','auth_user_id','monteur_id','role','active','locked','created')
ORDER BY ordinal_position;

-- §5.2 UNIQUE-Constraints prüfen
SELECT conname, contype, pg_get_constraintdef(oid) AS def
FROM pg_constraint
WHERE conrelid='public.users'::regclass
  AND contype IN ('u','p');

-- §5.3 Empfehlung Constraints (falls fehlend):
-- ALTER TABLE public.users ADD CONSTRAINT users_username_key UNIQUE (username);
-- ALTER TABLE public.users ADD CONSTRAINT users_email_key    UNIQUE (email);
-- ALTER TABLE public.users ADD CONSTRAINT users_auth_uid_key UNIQUE (auth_user_id);

-- §5.4 Smoke-Test: Edge-Function-angelegter User vollständig verknüpft?
-- (nach Test-Anlage testuser1+test@ep-kolar.at via §3.4)
SELECT u.id, u.username, u.email, u.auth_user_id, u.monteur_id,
       au.id AS auth_users_id, au.email AS auth_email, au.email_confirmed_at,
       w.id AS worker_id, w.name AS worker_name
FROM public.users u
LEFT JOIN auth.users au ON au.id = u.auth_user_id
LEFT JOIN public.workers w ON w.id = u.monteur_id
WHERE u.username = 'testuser1';
-- Erwartet: 1 Zeile, alle Spalten NOT NULL (außer monteur_id wenn role ∉ monteur/techniker)

-- §5.5 Halb-angelegte Legacy-User finden (B-E Backlog)
SELECT id, username, email, auth_user_id, monteur_id, role
FROM public.users
WHERE auth_user_id IS NULL
ORDER BY created DESC;
-- Sebastian-Action: manual repair oder Bulk-Migration via Edge-Function.

-- §5.6 Cleanup nach Smoke-Test
-- (im Supabase Dashboard → Authentication → testuser1 löschen
--  ODER via service_role SQL:)
-- DELETE FROM public.users  WHERE username='testuser1';
-- (auth.users via Dashboard löschen — RLS-frei)
```

---

## 6. Konsistenz-Constraints (Soll-Zustand)

| Constraint | Tabelle | Spalte | Rationale |
|------------|---------|--------|-----------|
| UNIQUE | `public.users` | `username` | verhindert Double-Submit-Dupes (Z7305-Hint) |
| UNIQUE | `public.users` | `email` | 1:1-Mapping zu GoTrue-Identität |
| UNIQUE | `public.users` | `auth_user_id` | 1:1-Mapping zu auth.users |
| FOREIGN-KEY | `public.users.auth_user_id` | → `auth.users(id)` | optional, ON DELETE SET NULL |
| FOREIGN-KEY | `public.users.monteur_id` | → `public.workers(id)` | optional, ON DELETE SET NULL |
| App-Invariante | `public.users.auth_user_id` | NOT NULL für alle Neuanlagen | enforced in Edge-Function §2.3 |

---

## 7. Rollout-Plan

| Phase | Wer | Was | Wann |
|-------|-----|-----|------|
| 1 | Agent B4 (jetzt) | Edge-Function-Skeleton + Plan-Doc commit+push | Sprint 80 (jetzt) |
| 2 | Sebastian | Verify §5.1+§5.2, ggf. Constraints aus §5.3 setzen | nach Sprint 79-Merge |
| 3 | Sebastian | `supabase functions deploy admin-create-user` | nach Phase 2 |
| 4 | Sebastian | Smoke-Test §3.4 + Verify §5.4 | nach Phase 3 |
| 5 | Sprint 80 (Code-Sprint) | Client-Patch §4 applien | nach Phase 4 |
| 6 | Sebastian | Legacy-User §5.5 Repair-Backlog | post-launch |

---

## 8. Out-of-Scope (Folge-Tasks)

- `admin-reset-password` Edge-Function (analog, ersetzt RPC für PW-Reset bei existierenden Usern) — Sprint 80 Folge.
- `admin-delete-user` Edge-Function (analog, ersetzt direkten DELETE-Pfad) — Sprint 80 Folge.
- Bulk-Repair der Legacy-Halb-User (§5.5) — manuell oder via Repair-Script.

---

**ENDE B-E-EDGE-FUNCTION-PLAN.md**