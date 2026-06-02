# EP Kolar — Bernd Kiener User-Setup v3.9.60
# Sebastian-Spec: Auth-User via Admin-API (NICHT SQL-INSERT in auth.users) + DB-Rows
# Voraussetzung: $env:SUPABASE_SERVICE_ROLE gesetzt
#
# Usage:
#   $env:SUPABASE_SERVICE_ROLE = "eyJ..."
#   .\scripts\create_kiener_v3960.ps1
#
# Optional Override (Defaults):
#   $env:KIENER_EMAIL    = "kiener@ep-kolar.at"
#   $env:KIENER_PASSWORD = "Test1234!"

$ErrorActionPreference = 'Stop'

$PROJECT  = "jiggujpruejkaomgxarp"
$BASE_URL = "https://$PROJECT.supabase.co"
$EMAIL    = if ($env:KIENER_EMAIL) { $env:KIENER_EMAIL } else { "kiener@ep-kolar.at" }
$PASSWORD = if ($env:KIENER_PASSWORD) { $env:KIENER_PASSWORD } else { "Test1234!" }

if (-not $env:SUPABASE_SERVICE_ROLE) {
    Write-Error "Service-Role-Key nicht gesetzt. Bitte: `$env:SUPABASE_SERVICE_ROLE = '<key>'"
    exit 1
}
$SR = $env:SUPABASE_SERVICE_ROLE

$headers = @{
    "apikey" = $SR
    "Authorization" = "Bearer $SR"
    "Content-Type" = "application/json"
    "Prefer" = "return=representation"
}

function Invoke-PgRest {
    param([string]$Method, [string]$Path, [object]$Body = $null)
    $url = "$BASE_URL/rest/v1/$Path"
    if ($Body) {
        $json = $Body | ConvertTo-Json -Depth 5
        return Invoke-RestMethod -Method $Method -Uri $url -Headers $headers -Body $json
    } else {
        return Invoke-RestMethod -Method $Method -Uri $url -Headers $headers
    }
}

# ═══════════════════════════════════════════════════════════
# PHASE 0 — Vorprüfung
# ═══════════════════════════════════════════════════════════
Write-Host "`n═══ PHASE 0 — Vorprüfung ═══" -ForegroundColor Cyan

# 0.1 auth.users für kiener prüfen
Write-Host "`n0.1 auth.users-Lookup für $EMAIL ..."
$authLookup = Invoke-RestMethod -Method GET `
    -Uri "$BASE_URL/auth/v1/admin/users?email=$EMAIL" `
    -Headers $headers
$existingAuth = $authLookup.users | Where-Object { $_.email -eq $EMAIL }
if ($existingAuth) {
    Write-Host "   ⚠ Auth-User existiert: id=$($existingAuth.id)" -ForegroundColor Yellow
    Write-Host "   → STOPP. Erst löschen via:" -ForegroundColor Yellow
    Write-Host "     Invoke-RestMethod -Method DELETE -Uri '$BASE_URL/auth/v1/admin/users/$($existingAuth.id)' -Headers `$headers" -ForegroundColor Yellow
    Write-Host "   → Dann Skript erneut ausführen."
    exit 2
}
Write-Host "   ✓ Kein Auth-User mit $EMAIL — clear für Insert."

# 0.2 Nächste freie IDs ermitteln
Write-Host "`n0.2 Nächste freie IDs ..."
$existingUsers = Invoke-PgRest -Method GET -Path "users?select=id&order=id.asc"
$userIds = $existingUsers | Select-Object -ExpandProperty id
Write-Host "   Existierende users.id: $($userIds -join ', ')"

$existingWorkers = Invoke-PgRest -Method GET -Path "workers?select=id&order=id.asc"
$workerIds = $existingWorkers | Select-Object -ExpandProperty id
Write-Host "   Existierende workers.id: $($workerIds -join ', ')"

# Convention: uN/wN — finde höchste nummerische N
$maxU = ($userIds | Where-Object { $_ -match '^u(\d+)$' } | ForEach-Object { [int]($_ -replace '^u','') } | Measure-Object -Maximum).Maximum
$maxW = ($workerIds | Where-Object { $_ -match '^w(\d+)$' } | ForEach-Object { [int]($_ -replace '^w','') } | Measure-Object -Maximum).Maximum
$UID = "u$($maxU + 1)"
$WID = "w$($maxW + 1)"
Write-Host "   → :UID = $UID" -ForegroundColor Green
Write-Host "   → :WID = $WID" -ForegroundColor Green

# 0.3 Kontingent-Vorlage lesen für worker_id-Konvention
Write-Host "`n0.3 urlaubskontingent Vorlage ..."
$kontTemplate = Invoke-PgRest -Method GET -Path "urlaubskontingent?select=*&limit=1"
if ($kontTemplate -and $kontTemplate.Count -gt 0) {
    $tplRow = $kontTemplate[0]
    Write-Host "   Beispiel-Row: id=$($tplRow.id), worker_id=$($tplRow.worker_id), worker_name=$($tplRow.worker_name)"
    # worker_id-Konvention: matcht das users.id-Pattern (u*) oder workers.id-Pattern (w*)?
    $workerIdConvention = if ($tplRow.worker_id -match '^u\d+$') { $UID } elseif ($tplRow.worker_id -match '^w\d+$') { $WID } else { $UID }
    Write-Host "   → worker_id-Konvention: $workerIdConvention" -ForegroundColor Green
} else {
    $workerIdConvention = $UID  # Default users-PK
    Write-Host "   ⚠ Keine Vorlage gefunden — Default workers.id=$workerIdConvention" -ForegroundColor Yellow
}

# ═══════════════════════════════════════════════════════════
# PHASE 1 — Auth-User via Admin-API
# ═══════════════════════════════════════════════════════════
Write-Host "`n═══ PHASE 1 — Auth-User via Admin-API ═══" -ForegroundColor Cyan

$authBody = @{
    email          = $EMAIL
    password       = $PASSWORD
    email_confirm  = $true
} | ConvertTo-Json

try {
    $authResp = Invoke-RestMethod -Method POST `
        -Uri "$BASE_URL/auth/v1/admin/users" `
        -Headers $headers `
        -Body $authBody
    $AUTH_UUID = $authResp.id
    Write-Host "   ✓ Auth-User angelegt: $AUTH_UUID" -ForegroundColor Green
} catch {
    $errMsg = $_.Exception.Message
    $respBody = ""
    try { $respBody = $_.ErrorDetails.Message } catch {}
    Write-Host "   ❌ Auth-User-Erstellung FAILED:" -ForegroundColor Red
    Write-Host "      Exception: $errMsg" -ForegroundColor Red
    Write-Host "      Response : $respBody" -ForegroundColor Red
    if ($respBody -match 'Database error') {
        Write-Host "`n   STOP. Trigger/Hook auf auth.users blockt." -ForegroundColor Red
        Write-Host "   → Sebastian-Action: SELECT * FROM pg_trigger WHERE tgrelid = 'auth.users'::regclass;" -ForegroundColor Red
        Write-Host "   → Trigger melden, NICHT in auth.users hand-INSERTen." -ForegroundColor Red
    }
    exit 3
}

# ═══════════════════════════════════════════════════════════
# PHASE 2 — DB-Rows (PostgREST)
# ═══════════════════════════════════════════════════════════
Write-Host "`n═══ PHASE 2 — DB-Rows ═══" -ForegroundColor Cyan

# 2.1 workers
Write-Host "`n2.1 workers INSERT ..."
try {
    $headers["Prefer"] = "resolution=ignore-duplicates,return=representation"
    $w = Invoke-PgRest -Method POST -Path "workers" -Body @{
        id = $WID
        name = "Kiener Bernd"
        role = "monteur"
        email = $EMAIL
        active = 1
    }
    Write-Host "   ✓ workers/$WID angelegt." -ForegroundColor Green
} catch {
    Write-Host "   ❌ workers FAILED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "      Response: $($_.ErrorDetails.Message)" -ForegroundColor Red
    exit 4
}

# 2.2 users
Write-Host "`n2.2 users INSERT ..."
try {
    $u = Invoke-PgRest -Method POST -Path "users" -Body @{
        id = $UID
        username = "kiener"
        name = "Kiener Bernd"
        email = $EMAIL
        role = "monteur"
        monteur_id = $WID
        active = 1
        auth_user_id = $AUTH_UUID
    }
    Write-Host "   ✓ users/$UID angelegt mit auth_user_id=$AUTH_UUID." -ForegroundColor Green
} catch {
    Write-Host "   ❌ users FAILED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "      Response: $($_.ErrorDetails.Message)" -ForegroundColor Red
    exit 5
}

# 2.3 urlaubskontingent
Write-Host "`n2.3 urlaubskontingent INSERT ..."
try {
    $k = Invoke-PgRest -Method POST -Path "urlaubskontingent" -Body @{
        id = $UID
        worker_id = $workerIdConvention
        worker_name = "Kiener Bernd"
        jahr = 2026
        urlaub = 25
        vorjahr = 0
        stunden = 192.5
        woche = 38.5
    }
    Write-Host "   ✓ urlaubskontingent/$UID angelegt." -ForegroundColor Green
} catch {
    Write-Host "   ❌ urlaubskontingent FAILED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "      Response: $($_.ErrorDetails.Message)" -ForegroundColor Red
    exit 6
}

# ═══════════════════════════════════════════════════════════
# PHASE 3 — Verifikation
# ═══════════════════════════════════════════════════════════
Write-Host "`n═══ PHASE 3 — Verifikation ═══" -ForegroundColor Cyan

# 3.1 GoTrue Login-Test
Write-Host "`n3.1 GoTrue Login-Test ..."
$loginBody = @{ email = $EMAIL; password = $PASSWORD } | ConvertTo-Json
try {
    $loginResp = Invoke-RestMethod -Method POST `
        -Uri "$BASE_URL/auth/v1/token?grant_type=password" `
        -Headers @{ "apikey" = $SR; "Content-Type" = "application/json" } `
        -Body $loginBody
    if ($loginResp.access_token) {
        Write-Host "   ✓ Login OK — access_token erhalten (len=$($loginResp.access_token.Length))" -ForegroundColor Green
    } else {
        Write-Host "   ⚠ Login Response: $($loginResp | ConvertTo-Json -Depth 2)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Login FAILED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "      Response: $($_.ErrorDetails.Message)" -ForegroundColor Red
}

# 3.2 users-Row verify
Write-Host "`n3.2 users-Row verify ..."
$verifyUser = Invoke-PgRest -Method GET -Path "users?username=eq.kiener&select=id,username,name,auth_user_id,monteur_id,role"
if ($verifyUser -and $verifyUser.Count -gt 0) {
    $vu = $verifyUser[0]
    Write-Host "   ✓ id=$($vu.id), username=$($vu.username), auth_user_id=$($vu.auth_user_id)" -ForegroundColor Green
    if ($vu.auth_user_id -eq $AUTH_UUID) {
        Write-Host "   ✓ auth_user_id matcht :AUTH_UUID" -ForegroundColor Green
    } else {
        Write-Host "   ❌ auth_user_id MISMATCH (got $($vu.auth_user_id), expected $AUTH_UUID)" -ForegroundColor Red
    }
} else {
    Write-Host "   ❌ users-Row NICHT gefunden" -ForegroundColor Red
}

# 3.3 App-Login-Hinweis
Write-Host "`n3.3 App-Login-Hinweis:"
Write-Host "   App → Benutzername 'kiener' (NICHT email) / Passwort '$PASSWORD'" -ForegroundColor Cyan

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "FINAL REPORT v3.9.60" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  PHASE 0 (Vorprüfung)         : ✓ keine Konflikte"
Write-Host "  PHASE 1 (Auth-User)          : ✓ id=$AUTH_UUID"
Write-Host "  PHASE 2 (DB-Rows)            : ✓ workers=$WID users=$UID kontingent=$UID"
Write-Host "  PHASE 3 (Verify)             : siehe oben"
Write-Host ""
Write-Host "Variablen-Recap:"
Write-Host "  :AUTH_UUID = $AUTH_UUID"
Write-Host "  :UID       = $UID"
Write-Host "  :WID       = $WID"
Write-Host "  :KONTING.worker_id = $workerIdConvention"
