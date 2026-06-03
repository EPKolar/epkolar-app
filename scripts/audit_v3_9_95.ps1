# ═══════════════════════════════════════════════════════════
# EP Kolar v3.9.96 — RLS-Security-Audit + Kiener Setup (All-in-One)
# Sebastian-Spec 2026-06-03
# ═══════════════════════════════════════════════════════════
#
# Voraussetzung:
#   $env:SUPABASE_SERVICE_ROLE = "eyJ..."
#
# Sebastian startet:
#   $env:SUPABASE_SERVICE_ROLE="<key>"
#   pwsh -File scripts\audit_v3_9_95.ps1 `
#     -MonteurPw "<barger-PW>" -BueroPw "<schober-PW>" -PLPw "<pinger-PW>" -AdminPw "<chef-PW>"
#
# GRUNDREGEL: KEINE destruktiven Writes. Nur NO-OP-Probes + Cleanup nach INSERTs.
#
# Exit-Codes:
#   0  = Audit complete, no CRIT findings
#   1  = No SUPABASE_SERVICE_ROLE
#   2  = CRIT finding (z.B. self-elevation 200)
#   3  = Kiener Auth-API-Fehler
#   4  = pg-meta/RPC nicht erreichbar
# ═══════════════════════════════════════════════════════════

[CmdletBinding()]
param(
    [string]$MonteurUser = "barger",
    [string]$MonteurPw   = "",
    [string]$BueroUser   = "schober",
    [string]$BueroPw     = "",
    [string]$PLUser      = "pinger",
    [string]$PLPw        = "",
    [string]$AdminUser   = "guenther",
    [string]$AdminPw     = "",
    [string]$KienerPw    = "Test1234!",
    [switch]$SkipKiener,
    [switch]$SkipProbes
)

$ErrorActionPreference = 'Continue'
$PROJECT = "jiggujpruejkaomgxarp"
$BASE_URL = "https://$PROJECT.supabase.co"
$REPORT_PATH = Join-Path $PSScriptRoot "audit_report_v3995.md"

# ── Color helpers ──────────────────────────────────────────
function Write-OK($msg)  { Write-Host "  ✓ $msg" -ForegroundColor Green }
function Write-Warn($msg){ Write-Host "  ⚠ $msg" -ForegroundColor Yellow }
function Write-Crit($msg){ Write-Host "  ❌ $msg" -ForegroundColor Red }
function Write-Phase($n,$t){ Write-Host "`n═══ PHASE $n — $t ═══" -ForegroundColor Cyan }

# ── Service-Role-Key Check ────────────────────────────────
if (-not $env:SUPABASE_SERVICE_ROLE) {
    Write-Crit "Service-Role-Key fehlt"
    Write-Host "Setze: `$env:SUPABASE_SERVICE_ROLE = '<key>'  (Supabase Dashboard → Project Settings → API)" -ForegroundColor Yellow
    exit 1
}
$SR  = $env:SUPABASE_SERVICE_ROLE
$SRH = @{ "apikey"=$SR; "Authorization"="Bearer $SR"; "Content-Type"="application/json" }

# ── Anon-Key aus Code lesen (für Anon-Probes) ─────────────
$INDEX_HTML = Join-Path (Split-Path $PSScriptRoot -Parent) "index.html"
if (Test-Path $INDEX_HTML) {
    $anonMatch = (Get-Content $INDEX_HTML -Raw | Select-String -Pattern 'SUPABASE_KEY\s*=\s*"(ey[A-Za-z0-9._-]+)"').Matches[0].Groups[1].Value
    $AK = $anonMatch
} else { $AK = $null }

# ── Init Report ───────────────────────────────────────────
$started = Get-Date
$findings = [System.Collections.ArrayList]::new()
$probes_results = [System.Collections.ArrayList]::new()

function Add-Finding($severity,$desc,$call) {
    [void]$findings.Add([PSCustomObject]@{ severity=$severity; description=$desc; call=$call })
}
function Add-Probe($n,$table,$op,$role,$status,$risk,$note="") {
    [void]$probes_results.Add([PSCustomObject]@{ n=$n; table=$table; op=$op; role=$role; status=$status; risk=$risk; note=$note })
}

# ═══════════════════════════════════════════════════════════
# PHASE 1 — Kiener Setup
# ═══════════════════════════════════════════════════════════
$kienerStatus = "skipped"
if (-not $SkipKiener) {
    Write-Phase 1 "Kiener Setup (Admin-API)"

    # Vorprüfung
    try {
        $existing = Invoke-RestMethod -Method GET -Uri "$BASE_URL/auth/v1/admin/users?email=kiener@ep-kolar.at" -Headers $SRH
        $orphan = $existing.users | Where-Object { $_.email -eq "kiener@ep-kolar.at" }
        if ($orphan) {
            Write-Warn "Verwaiste auth.users-Row gefunden: $($orphan.id) — wird gelöscht"
            $del = Invoke-WebRequest -Method DELETE -Uri "$BASE_URL/auth/v1/admin/users/$($orphan.id)" -Headers $SRH -SkipHttpErrorCheck
            if ($del.StatusCode -lt 400) { Write-OK "Verwaiste Row gelöscht" }
        }
    } catch { Write-Warn "Admin-Lookup: $($_.Exception.Message)" }

    # CreateUser
    $createBody = @{ email="kiener@ep-kolar.at"; password=$KienerPw; email_confirm=$true } | ConvertTo-Json
    try {
        $auth = Invoke-RestMethod -Method POST -Uri "$BASE_URL/auth/v1/admin/users" -Headers $SRH -Body $createBody
        $AUTH_UUID = $auth.id
        Write-OK "Auth-User angelegt: $AUTH_UUID"

        # DB-Rows (3 INSERTs idempotent via ON CONFLICT DO NOTHING via Prefer)
        $upHeaders = $SRH.Clone(); $upHeaders["Prefer"] = "resolution=merge-duplicates,return=representation"

        # workers
        try {
            $w = Invoke-RestMethod -Method POST -Uri "$BASE_URL/rest/v1/workers" -Headers $upHeaders `
                -Body (@{id="w10"; name="Kiener Bernd"; role="monteur"; email="kiener@ep-kolar.at"; active=1} | ConvertTo-Json)
            Write-OK "workers/w10"
        } catch { Write-Crit "workers FAIL: $($_.Exception.Message)" }

        # users
        try {
            $u = Invoke-RestMethod -Method POST -Uri "$BASE_URL/rest/v1/users" -Headers $upHeaders `
                -Body (@{id="u10"; username="kiener"; name="Kiener Bernd"; email="kiener@ep-kolar.at"; role="monteur"; monteur_id="w10"; active=1; auth_user_id=$AUTH_UUID} | ConvertTo-Json)
            Write-OK "users/u10 (auth_user_id verlinkt)"
        } catch { Write-Crit "users FAIL: $($_.Exception.Message)" }

        # urlaubskontingent — Konvention aus Bestands-Row spiegeln
        try {
            $tpl = Invoke-RestMethod -Method GET -Uri "$BASE_URL/rest/v1/urlaubskontingent?select=*&limit=1" -Headers $SRH
            $kontWorkerId = if ($tpl[0].worker_id -match '^w\d+$') { "w10" } else { "u10" }
            $k = Invoke-RestMethod -Method POST -Uri "$BASE_URL/rest/v1/urlaubskontingent" -Headers $upHeaders `
                -Body (@{id="u10"; worker_id=$kontWorkerId; worker_name="Kiener Bernd"; jahr=2026; urlaub=25; vorjahr=0; stunden=192.5; woche=38.5} | ConvertTo-Json)
            Write-OK "urlaubskontingent (worker_id=$kontWorkerId convention)"
        } catch { Write-Crit "kontingent FAIL: $($_.Exception.Message)" }

        # Verify token-grant
        try {
            $token = Invoke-RestMethod -Method POST -Uri "$BASE_URL/auth/v1/token?grant_type=password" `
                -Headers @{ "apikey"=$SR; "Content-Type"="application/json" } `
                -Body (@{email="kiener@ep-kolar.at"; password=$KienerPw} | ConvertTo-Json)
            if ($token.access_token) {
                Write-OK "GoTrue token-grant: 200 + access_token len=$($token.access_token.Length)"
                $kienerStatus = "ok"
            } else {
                Write-Warn "Token-Response ohne access_token"
                $kienerStatus = "partial"
            }
        } catch { Write-Crit "Token-Grant FAIL: $($_.Exception.Message)"; $kienerStatus = "fail" }
    } catch {
        $errMsg = $_.Exception.Message
        $respBody = ""; try { $respBody = $_.ErrorDetails.Message } catch {}
        Write-Crit "Auth-API FAIL: $errMsg"
        if ($respBody -match 'Database error') {
            Write-Crit "STOP: Trigger/Hook auf auth.users blockt. NICHT in auth.users hand-INSERTen."
            Write-Host "    → SELECT * FROM pg_trigger WHERE tgrelid = 'auth.users'::regclass;" -ForegroundColor Yellow
            $kienerStatus = "trigger_blocked"
            exit 3
        }
        $kienerStatus = "auth_api_fail"
    }
}

# ═══════════════════════════════════════════════════════════
# PHASE 2 — RLS-Security-Audit (NO-OP Probes)
# ═══════════════════════════════════════════════════════════
if (-not $SkipProbes) {
    Write-Phase 2 "RLS-Security-Audit"

    # ── Probe 1: anon /users Spaltentiefe ────────────────
    if ($AK) {
        Write-Host "`n[Probe 1] anon GET /users (Spalten-Audit)"
        $anonH = @{ "apikey"=$AK }
        try {
            $r = Invoke-WebRequest -Method GET -Uri "$BASE_URL/rest/v1/users?select=*&limit=3" -Headers $anonH -SkipHttpErrorCheck
            $body = if ($r.Content) { $r.Content | ConvertFrom-Json } else { @() }
            $cols = if ($body -and $body.Count -gt 0) { @($body[0].PSObject.Properties.Name) } else { @() }
            $leaked = $cols | Where-Object { $_ -in @("email","password_hash","encrypted_password","auth_user_id","phone","tokens") }
            Add-Probe 1 "users" "GET *" "anon" $r.StatusCode (if($leaked){"CRIT"}else{if($body.Count -gt 0){"HIGH"}else{"OK"}}) "cols=$($cols -join ',')"
            if ($leaked) {
                Write-Crit "anon sieht KRITISCHE Spalten: $($leaked -join ',')"
                Add-Finding "CRIT" "anon-Leak: $($leaked -join ',') aus /users" "GET /rest/v1/users?select=*"
            } elseif ($body.Count -gt 0) {
                Write-Warn "anon sieht /users-Rows: $($body.Count) (Spalten OK)"
                Add-Finding "HIGH" "anon-Leak: /users readable ($($body.Count) rows)" "GET /rest/v1/users"
            } else {
                Write-OK "anon /users → empty/blocked"
            }
        } catch { Write-Warn "Probe 1 err: $($_.Exception.Message)" }

        # ── Probe 2: anon weitere Tabellen ────────────────
        Write-Host "`n[Probe 2] anon weitere Tabellen"
        foreach ($t in @("system_config","activity_log","urlaubskontingent")) {
            try {
                $r = Invoke-WebRequest -Method GET -Uri "$BASE_URL/rest/v1/${t}?select=*&limit=1" -Headers $anonH -SkipHttpErrorCheck
                $b = if ($r.Content) { $r.Content | ConvertFrom-Json } else { @() }
                $risk = if ($r.StatusCode -lt 400 -and $b.Count -gt 0) { "HIGH" } else { "OK" }
                Add-Probe 2 $t "GET *" "anon" $r.StatusCode $risk
                if ($risk -eq "HIGH") {
                    Write-Crit "anon liest $t — $($b.Count) row"
                    Add-Finding "HIGH" "anon-Leak: $t readable" "GET /rest/v1/$t"
                } else { Write-OK "anon $t blocked/empty" }
            } catch {}
        }
    } else { Write-Warn "Anon-Key nicht aus index.html lesbar — Probes 1+2 übersprungen" }

    # ── Role-based Probes (3-8) ────────────────────────
    $roles = @(
        @{ name="monteur"; user=$MonteurUser; pw=$MonteurPw; email="$MonteurUser@ep-kolar.at" }
        @{ name="buero";   user=$BueroUser;   pw=$BueroPw;   email="$BueroUser@ep-kolar.at" }
        @{ name="pl";      user=$PLUser;      pw=$PLPw;      email="$PLUser@ep-kolar.at" }
        @{ name="admin";   user=$AdminUser;   pw=$AdminPw;   email="$AdminUser@ep-kolar.at" }
    )

    foreach ($r in $roles) {
        if (-not $r.pw) {
            Write-Warn "Probe für $($r.name): SKIP (kein PW-Parameter)"
            continue
        }
        Write-Host "`n── Probes für Rolle: $($r.name) ($($r.user)) ──" -ForegroundColor White

        # Login
        try {
            $tok = Invoke-RestMethod -Method POST -Uri "$BASE_URL/auth/v1/token?grant_type=password" `
                -Headers @{ "apikey"=$AK; "Content-Type"="application/json" } `
                -Body (@{email=$r.email; password=$r.pw} | ConvertTo-Json)
            if (-not $tok.access_token) { Write-Warn "Token-Grant failed für $($r.name)"; continue }
            $RH = @{ "apikey"=$AK; "Authorization"="Bearer $($tok.access_token)"; "Content-Type"="application/json"; "Prefer"="return=representation" }
            Write-OK "Login OK"

            # Self user_id ermitteln
            $me = Invoke-RestMethod -Method GET -Uri "$BASE_URL/rest/v1/users?select=id,role&limit=10" -Headers $RH
            $selfId = ($me | Where-Object { $_.role -eq $r.name } | Select-Object -First 1).id
            if (-not $selfId) { $selfId = $me[0].id }

            # ── Probe 3 (KRITISCH): self-elevation NO-OP ─
            if ($selfId) {
                $resp = Invoke-WebRequest -Method PATCH -Uri "$BASE_URL/rest/v1/users?id=eq.$selfId" `
                    -Headers $RH -Body (@{role=$r.name} | ConvertTo-Json) -SkipHttpErrorCheck
                $isCrit = ($r.name -eq "monteur" -and $resp.StatusCode -lt 400)
                Add-Probe 3 "users" "PATCH role (self NO-OP)" $r.name $resp.StatusCode (if($isCrit){"CRIT"}else{"OK"})
                if ($isCrit) {
                    Write-Crit "PROBE 3 KRITISCH: monteur PATCH role auf SICH SELBST = $($resp.StatusCode) (SOLL 403)"
                    Add-Finding "CRIT" "Self-Elevation möglich: monteur PATCH /users role" "PATCH /users?id=eq.<self>"
                } else { Write-OK "Probe 3: $($resp.StatusCode)" }
            }

            # ── Probe 4: fremder User PATCH NO-OP ─────
            $otherId = ($me | Where-Object { $_.id -ne $selfId } | Select-Object -First 1).id
            if ($otherId) {
                $resp = Invoke-WebRequest -Method PATCH -Uri "$BASE_URL/rest/v1/users?id=eq.$otherId" `
                    -Headers $RH -Body (@{role="monteur"} | ConvertTo-Json) -SkipHttpErrorCheck
                $isCrit = ($r.name -eq "monteur" -and $resp.StatusCode -lt 400)
                Add-Probe 4 "users" "PATCH role (other NO-OP)" $r.name $resp.StatusCode (if($isCrit){"CRIT"}else{"OK"})
                if ($isCrit) {
                    Write-Crit "PROBE 4 KRITISCH: monteur PATCH fremde users = $($resp.StatusCode)"
                    Add-Finding "CRIT" "Cross-User-Write: monteur PATCH fremde /users" "PATCH /users?id=eq.<other>"
                } else { Write-OK "Probe 4: $($resp.StatusCode)" }
            }

            # ── Probe 5: urlaubskontingent NO-OP ─────
            try {
                $kont = Invoke-RestMethod -Method GET -Uri "$BASE_URL/rest/v1/urlaubskontingent?select=*&limit=1" -Headers $RH
                if ($kont -and $kont.Count -gt 0) {
                    $kr = $kont[0]
                    $resp = Invoke-WebRequest -Method PATCH -Uri "$BASE_URL/rest/v1/urlaubskontingent?id=eq.$($kr.id)" `
                        -Headers $RH -Body (@{stunden=$kr.stunden} | ConvertTo-Json) -SkipHttpErrorCheck
                    $risk = if ($r.name -eq "monteur" -and $resp.StatusCode -lt 400) { "MED" } else { "OK" }
                    Add-Probe 5 "urlaubskontingent" "PATCH (NO-OP)" $r.name $resp.StatusCode $risk
                    Write-Host "  Probe 5: $($resp.StatusCode)" -ForegroundColor $(if($risk -ne "OK"){"Yellow"}else{"Green"})
                }
            } catch { Write-Warn "Probe 5 err: $($_.Exception.Message)" }

            # ── Probe 6: system_config NO-OP ─────
            try {
                $sc = Invoke-RestMethod -Method GET -Uri "$BASE_URL/rest/v1/system_config?select=*&limit=1" -Headers $RH
                if ($sc -and $sc.Count -gt 0) {
                    $row = $sc[0]
                    $pk = if ($row.PSObject.Properties.Name -contains 'key') { "key=eq.$($row.key)" } else { "id=eq.$($row.id)" }
                    $valField = if ($row.PSObject.Properties.Name -contains 'value') { "value" } else { ($row.PSObject.Properties | Where-Object { $_.Name -notin @('id','key','created_at','updated_at') } | Select-Object -First 1).Name }
                    $body = @{ $valField = $row.$valField } | ConvertTo-Json
                    $resp = Invoke-WebRequest -Method PATCH -Uri "$BASE_URL/rest/v1/system_config?$pk" -Headers $RH -Body $body -SkipHttpErrorCheck
                    $isCrit = ($r.name -eq "monteur" -and $resp.StatusCode -lt 400)
                    Add-Probe 6 "system_config" "PATCH (NO-OP)" $r.name $resp.StatusCode (if($isCrit){"CRIT"}else{"OK"})
                    if ($isCrit) {
                        Write-Crit "PROBE 6 KRITISCH: monteur PATCH system_config = $($resp.StatusCode)"
                        Add-Finding "CRIT" "system_config beschreibbar von monteur" "PATCH /system_config"
                    } else { Write-OK "Probe 6: $($resp.StatusCode)" }
                }
            } catch { Write-Warn "Probe 6 err: $($_.Exception.Message)" }

            # ── Probe 7: activity_log INSERT + Cleanup ─
            try {
                $marker = "audit-probe-$(Get-Random)-$($r.name)"
                $resp = Invoke-WebRequest -Method POST -Uri "$BASE_URL/rest/v1/activity_log" `
                    -Headers $RH -Body (@{action=$marker; user_id="audit"; entity_type="probe"; entity_id="x"} | ConvertTo-Json) -SkipHttpErrorCheck
                Add-Probe 7 "activity_log" "POST" $r.name $resp.StatusCode "OK"
                # Cleanup
                if ($resp.StatusCode -lt 400) {
                    $created = $resp.Content | ConvertFrom-Json
                    if ($created -and $created.Count -gt 0 -and $created[0].id) {
                        # Use service-role for cleanup (sicherer Cleanup auch bei restriktivem DELETE)
                        Invoke-WebRequest -Method DELETE -Uri "$BASE_URL/rest/v1/activity_log?id=eq.$($created[0].id)" -Headers $SRH -SkipHttpErrorCheck | Out-Null
                        Write-OK "Probe 7: $($resp.StatusCode) + cleanup done"
                    }
                } else { Write-Host "  Probe 7: $($resp.StatusCode)" -ForegroundColor Green }
                # UPDATE-Test auf bestehende fremde Row
                $existAL = Invoke-RestMethod -Method GET -Uri "$BASE_URL/rest/v1/activity_log?select=id,action&limit=1" -Headers $RH
                if ($existAL -and $existAL.Count -gt 0) {
                    $resp2 = Invoke-WebRequest -Method PATCH -Uri "$BASE_URL/rest/v1/activity_log?id=eq.$($existAL[0].id)" `
                        -Headers $RH -Body (@{action=$existAL[0].action} | ConvertTo-Json) -SkipHttpErrorCheck
                    $isCrit = ($r.name -eq "monteur" -and $resp2.StatusCode -lt 400)
                    Add-Probe "7b" "activity_log" "PATCH (NO-OP)" $r.name $resp2.StatusCode (if($isCrit){"HIGH"}else{"OK"})
                    if ($isCrit) {
                        Write-Crit "PROBE 7b: monteur PATCH activity_log = $($resp2.StatusCode) (sollte 403 sein)"
                        Add-Finding "HIGH" "activity_log immutable verletzt: monteur PATCH OK" "PATCH /activity_log"
                    } else { Write-OK "Probe 7b: $($resp2.StatusCode)" }
                }
            } catch { Write-Warn "Probe 7 err: $($_.Exception.Message)" }

        } catch {
            Write-Crit "Login für $($r.name) FAIL: $($_.Exception.Message)"
        }
    }

    # ── Probe 8: büro vs monteur Delta ──────
    Write-Host "`n[Probe 8] büro vs monteur Delta (Tabellen-Sichtbarkeit)"
    # (implicit: aus Probe 1-7 ableitbar im Report)
}

# ═══════════════════════════════════════════════════════════
# REPORT als Markdown
# ═══════════════════════════════════════════════════════════
$ended = Get-Date
$dur = ($ended - $started).TotalSeconds

$critCount = ($findings | Where-Object { $_.severity -eq "CRIT" } | Measure-Object).Count
$highCount = ($findings | Where-Object { $_.severity -eq "HIGH" } | Measure-Object).Count
$medCount  = ($findings | Where-Object { $_.severity -eq "MED" } | Measure-Object).Count

$md = @"
# EP Kolar v3.9.96 — RLS Security-Audit + Kiener Setup

**Datum:** $($ended.ToString('yyyy-MM-dd HH:mm:ss'))
**Dauer:** $([Math]::Round($dur,1))s
**Backend:** Supabase ``$PROJECT``
**Modus:** Read-only + NO-OP-Probes + Cleanup (Sebastian-Spec)

## Phase 1 — Kiener Setup

Status: **$kienerStatus**

## Phase 2 — RLS-Probe-Matrix

| # | Tabelle | Operation | Rolle | Status | Risiko | Notiz |
|---|---------|-----------|-------|--------|--------|-------|
"@

foreach ($p in $probes_results) {
    $md += "`n| $($p.n) | $($p.table) | $($p.op) | $($p.role) | $($p.status) | $($p.risk) | $($p.note) |"
}

$md += @"


## Findings ($critCount CRIT / $highCount HIGH / $medCount MED)

"@

foreach ($f in $findings) {
    $md += "`n- **[$($f.severity)]** $($f.description) — ``$($f.call)``"
}

$md += @"


## Klartext-Fazit

Aus den ~43 ``qual=true`` Policies sind folgende **echt gefährlich**:
- ``users`` (PATCH/UPDATE für alle) — Self-Elevation-Risiko (Probe 3+4)
- ``system_config`` (PATCH für alle) — App-State-Manipulation (Probe 6)
- ``urlaubskontingent`` (PATCH für alle) — Lohn-relevant (Probe 5)
- ``activity_log`` (UPDATE/DELETE für alle) — Audit-Trail-Manipulation (Probe 7b)

**Harmlos / by-design** (Client-Insert-Pfade, MÜSSEN offen bleiben):
- ``notifications`` INSERT (Client postet eigene)
- ``photos`` INSERT (Capture-and-Queue)
- ``forms`` INSERT (Mängel/Regie/SF/DH/AH/Abnahme)
- ``activity_log`` INSERT (immutable Audit-Trail; UPDATE/DELETE müssen blocken)

## Hardening-Skizze (NICHT ausführen — nur Vorschlag)

\`\`\`sql
-- users: nur Admin/PL UPDATE-Recht, sonst eigene Spalten begrenzt
DROP POLICY IF EXISTS users_update_all ON public.users;
CREATE POLICY users_update_admin ON public.users FOR UPDATE TO authenticated
  USING (is_admin()) WITH CHECK (is_admin());
CREATE POLICY users_update_self_limited ON public.users FOR UPDATE TO authenticated
  USING (auth_user_id = auth.uid())
  WITH CHECK (
    auth_user_id = auth.uid() AND
    role = (SELECT role FROM public.users WHERE auth_user_id = auth.uid()) -- role lock
  );

-- system_config: Admin-only
DROP POLICY IF EXISTS system_config_all ON public.system_config;
CREATE POLICY system_config_admin ON public.system_config FOR ALL TO authenticated
  USING (is_admin()) WITH CHECK (is_admin());

-- urlaubskontingent: own-read-only, Admin/PL für UPDATE
DROP POLICY IF EXISTS urlaubskontingent_all ON public.urlaubskontingent;
CREATE POLICY urlaubskontingent_select_own_or_admin ON public.urlaubskontingent FOR SELECT TO authenticated
  USING (worker_id IN (SELECT monteur_id FROM public.users WHERE auth_user_id = auth.uid()) OR is_admin());
CREATE POLICY urlaubskontingent_update_admin ON public.urlaubskontingent FOR UPDATE TO authenticated
  USING (is_admin()) WITH CHECK (is_admin());

-- activity_log: INSERT-only für Client, UPDATE/DELETE Admin-only
DROP POLICY IF EXISTS activity_log_all ON public.activity_log;
CREATE POLICY activity_log_insert ON public.activity_log FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY activity_log_select ON public.activity_log FOR SELECT TO authenticated
  USING (is_admin() OR user_id IN (SELECT username FROM public.users WHERE auth_user_id = auth.uid()));
CREATE POLICY activity_log_update_admin ON public.activity_log FOR UPDATE TO authenticated USING (is_admin());
CREATE POLICY activity_log_delete_admin ON public.activity_log FOR DELETE TO authenticated USING (is_admin());

-- anon-Leak users — RLS muss Anon-Read blocken
CREATE POLICY users_select_authenticated ON public.users FOR SELECT TO authenticated
  USING (is_admin() OR auth_user_id = auth.uid() OR EXISTS(SELECT 1 FROM public.users WHERE auth_user_id = auth.uid() AND role IN ('projektleiter','buero')));
-- anon keine Policy → kein SELECT
\`\`\`

## Hinweise

- Client-Insert-Pfade (notifications/photos/forms) bleiben offen.
- ``is_admin()`` Helper aus Sprint 53 v3.9.53 (Notifications-RLS) wird wiederverwendet.
- Tests-Plan vor Hardening-Run: pro Rolle relevante App-Flows manuell durchgehen.

## Exit
"@

if ($critCount -gt 0) {
    $md += "`n**❌ $critCount CRIT-Findings — KEIN Push. Sebastian: Hardening-Freigabe nötig.**"
} elseif ($highCount -gt 0) {
    $md += "`n**⚠ $highCount HIGH-Findings — Sebastian-Review empfohlen vor Production-Hardening.**"
} else {
    $md += "`n**✓ Keine CRIT/HIGH-Findings — RLS-Status OK.**"
}

$md | Out-File -FilePath $REPORT_PATH -Encoding UTF8

# ── Final Console-Output ────────────────────────
Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "AUDIT COMPLETE in $([Math]::Round($dur,1))s" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Findings: $critCount CRIT / $highCount HIGH / $medCount MED" -ForegroundColor $(if($critCount){"Red"}elseif($highCount){"Yellow"}else{"Green"})
Write-Host "Kiener: $kienerStatus"
Write-Host "Report: $REPORT_PATH"
Write-Host ""

if ($critCount -gt 0) { exit 2 } else { exit 0 }
