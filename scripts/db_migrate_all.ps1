# EP Kolar — All-in-One DB-Migration + Kiener-Setup
# Sebastian-Action: ein Skript, alle 4 SQL-Migrations + Bernd Kiener User-Setup + Verify
#
# Voraussetzung:
#   $env:SUPABASE_SERVICE_ROLE = "eyJ..."
#
# Optional Override:
#   $env:SUPABASE_PROJECT_REF = "jiggujpruejkaomgxarp"  # default
#   $env:KIENER_EMAIL    = "kiener@ep-kolar.at"
#   $env:KIENER_PASSWORD = "Test1234!"
#   $env:SKIP_KIENER     = "1"  # nur die 3 RLS/View-Migrations, kein Kiener-Setup
#   $env:SKIP_WHATSAPP   = "1"  # WhatsApp-Tables überspringen
#
# Usage:
#   $env:SUPABASE_SERVICE_ROLE = '<paste-here>'
#   pwsh -File scripts\db_migrate_all.ps1

$ErrorActionPreference = 'Stop'

$PROJECT  = if ($env:SUPABASE_PROJECT_REF) { $env:SUPABASE_PROJECT_REF } else { "jiggujpruejkaomgxarp" }
$BASE_URL = "https://$PROJECT.supabase.co"
$EMAIL    = if ($env:KIENER_EMAIL) { $env:KIENER_EMAIL } else { "kiener@ep-kolar.at" }
$PASSWORD = if ($env:KIENER_PASSWORD) { $env:KIENER_PASSWORD } else { "Test1234!" }

if (-not $env:SUPABASE_SERVICE_ROLE) {
    Write-Error @"
Service-Role-Key nicht gesetzt.

Setze:
  `$env:SUPABASE_SERVICE_ROLE = '<eyJ...>'

Key bekommst du in Supabase Dashboard → Project Settings → API → service_role (Geheim!)
"@
    exit 1
}
$SR = $env:SUPABASE_SERVICE_ROLE

$headers = @{
    "apikey"        = $SR
    "Authorization" = "Bearer $SR"
    "Content-Type"  = "application/json"
}

# Path-Konfiguration
$REPO_ROOT = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$SQL_DIR   = Join-Path $REPO_ROOT "sql"

$SQL_FILES = @(
    @{ Name = "Notifications RLS";          File = "migrate_notifications_rls_v3953.sql";    Required = $true  }
    @{ Name = "Supplier-Articles Safe-View"; File = "migrate_supplier_articles_safe_v3954.sql"; Required = $true  }
    @{ Name = "WhatsApp Tables";             File = "migrate_whatsapp_v3919.sql";            Required = $false; SkipEnv = "SKIP_WHATSAPP" }
)

function Invoke-Sql {
    param([string]$Sql, [string]$Label)
    # Supabase exposiert SQL nicht direkt via REST. Wir nutzen die `pg-meta` Endpoint:
    #   POST /pg/query  body: { query: "..." }
    # Aber pg-meta ist nicht im public-API. Alternative: Direkter Postgres-Connect.
    #
    # Für PSv7+: PostgreSQL-Direct-Call via Npgsql wäre ideal.
    # Pragmatischer Ansatz: Nutze pg-meta wenn verfügbar, sonst FALLBACK.
    try {
        $body = @{ query = $Sql } | ConvertTo-Json -Depth 5
        $resp = Invoke-RestMethod -Method POST `
            -Uri "$BASE_URL/pg-meta/query" `
            -Headers $headers `
            -Body $body
        return @{ ok = $true; rows = $resp }
    } catch {
        # Fallback: REST-Edge-Function (existiert wahrscheinlich nicht)
        return @{ ok = $false; err = $_.Exception.Message; respBody = $_.ErrorDetails.Message }
    }
}

function Try-DirectPgConnect {
    # Check ob psql verfügbar ist (Sebastian hat möglicherweise lokal psql installiert)
    $psql = (Get-Command psql -ErrorAction SilentlyContinue)
    if ($psql) {
        return $psql.Source
    }
    return $null
}

# ═══════════════════════════════════════════════════════════
# Strategy-Detection: pg-meta API vs. psql CLI vs. manual-only
# ═══════════════════════════════════════════════════════════

Write-Host "`n═══ STRATEGY-DETECTION ═══" -ForegroundColor Cyan

$testQuery = Invoke-Sql -Sql "SELECT 1 as test" -Label "Connection Test"
if ($testQuery.ok) {
    Write-Host "✓ pg-meta API erreichbar" -ForegroundColor Green
    $STRATEGY = "pg-meta"
} else {
    Write-Host "✗ pg-meta API nicht erreichbar (Response: $($testQuery.err))" -ForegroundColor Yellow
    $psqlPath = Try-DirectPgConnect
    if ($psqlPath) {
        Write-Host "✓ psql CLI gefunden: $psqlPath" -ForegroundColor Green
        Write-Host "  HINWEIS: psql braucht DB-URL. Nicht der service-role-key, sondern der Postgres-Connection-String." -ForegroundColor Yellow
        Write-Host "  Supabase Dashboard → Project Settings → Database → Connection-String → URI" -ForegroundColor Yellow
        if (-not $env:SUPABASE_DB_URL) {
            Write-Host ""
            Write-Error "Setze auch `$env:SUPABASE_DB_URL für psql-Modus."
            exit 2
        }
        $STRATEGY = "psql"
    } else {
        Write-Host "✗ Weder pg-meta noch psql verfügbar." -ForegroundColor Red
        Write-Host ""
        Write-Host "FALLBACK: Manuelle Ausführung via Supabase Dashboard SQL Editor:" -ForegroundColor Yellow
        Write-Host "  1. https://supabase.com/dashboard/project/$PROJECT/sql/new" -ForegroundColor Cyan
        Write-Host "  2. Für jede Datei: Inhalt einfügen → Run" -ForegroundColor Cyan
        Write-Host "     - sql/migrate_notifications_rls_v3953.sql" -ForegroundColor Cyan
        Write-Host "     - sql/migrate_supplier_articles_safe_v3954.sql" -ForegroundColor Cyan
        Write-Host "     - sql/migrate_whatsapp_v3919.sql (optional)" -ForegroundColor Cyan
        Write-Host "  3. Danach: pwsh -File scripts/create_kiener_v3960.ps1 für User-Setup" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Siehe Runbook: sql/RUNBOOK_v3953-v3959.md" -ForegroundColor Cyan
        exit 3
    }
}

# ═══════════════════════════════════════════════════════════
# PHASE A: SQL-Migrations
# ═══════════════════════════════════════════════════════════

Write-Host "`n═══ PHASE A — SQL-Migrations ($STRATEGY) ═══" -ForegroundColor Cyan

foreach ($mig in $SQL_FILES) {
    $sqlPath = Join-Path $SQL_DIR $mig.File
    if (-not (Test-Path $sqlPath)) {
        Write-Host "  ✗ Datei fehlt: $sqlPath" -ForegroundColor Red
        if ($mig.Required) { exit 4 }
        continue
    }
    if ($mig.SkipEnv -and [Environment]::GetEnvironmentVariable($mig.SkipEnv)) {
        Write-Host "  ⏭ $($mig.Name) SKIP (`$env:$($mig.SkipEnv) gesetzt)" -ForegroundColor Yellow
        continue
    }
    Write-Host "`n  ▶ $($mig.Name): $($mig.File)" -ForegroundColor White
    $sqlContent = Get-Content $sqlPath -Raw -Encoding UTF8

    if ($STRATEGY -eq "pg-meta") {
        $result = Invoke-Sql -Sql $sqlContent -Label $mig.Name
        if ($result.ok) {
            Write-Host "  ✓ erfolgreich" -ForegroundColor Green
        } else {
            Write-Host "  ✗ FEHLER: $($result.err)" -ForegroundColor Red
            Write-Host "    Response: $($result.respBody)" -ForegroundColor Red
            if ($mig.Required) { exit 5 }
        }
    } elseif ($STRATEGY -eq "psql") {
        $tmpFile = [System.IO.Path]::GetTempFileName() + ".sql"
        $sqlContent | Out-File -FilePath $tmpFile -Encoding UTF8 -NoNewline
        try {
            & psql $env:SUPABASE_DB_URL -f $tmpFile 2>&1 | ForEach-Object { "    $_" } | Write-Host
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✓ erfolgreich" -ForegroundColor Green
            } else {
                Write-Host "  ✗ psql exit code $LASTEXITCODE" -ForegroundColor Red
                if ($mig.Required) { exit 6 }
            }
        } finally {
            Remove-Item $tmpFile -Force -ErrorAction SilentlyContinue
        }
    }
}

# ═══════════════════════════════════════════════════════════
# PHASE B: Kiener User-Setup (delegiert an create_kiener_v3960.ps1)
# ═══════════════════════════════════════════════════════════

if ($env:SKIP_KIENER) {
    Write-Host "`n═══ PHASE B — Kiener SKIP (`$env:SKIP_KIENER) ═══" -ForegroundColor Yellow
} else {
    Write-Host "`n═══ PHASE B — Bernd Kiener User-Setup ═══" -ForegroundColor Cyan
    $kienerScript = Join-Path $PSScriptRoot "create_kiener_v3960.ps1"
    if (-not (Test-Path $kienerScript)) {
        Write-Host "  ✗ Kiener-Skript fehlt: $kienerScript" -ForegroundColor Red
        exit 7
    }
    & $kienerScript
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n  ✗ Kiener-Setup FAIL (exit $LASTEXITCODE) — siehe Output oben" -ForegroundColor Red
        exit 8
    }
}

# ═══════════════════════════════════════════════════════════
# PHASE C: Verify
# ═══════════════════════════════════════════════════════════

Write-Host "`n═══ PHASE C — Verify ═══" -ForegroundColor Cyan

# C.1 Notifications RLS Policies
Write-Host "`nC.1 Notifications RLS Policies"
try {
    $polRes = Invoke-RestMethod -Method GET `
        -Uri "$BASE_URL/rest/v1/rpc/get_table_policies?tbl=notifications" `
        -Headers $headers -ErrorAction SilentlyContinue
    Write-Host "  → $($polRes | ConvertTo-Json -Depth 2 -Compress)"
} catch {
    Write-Host "  ⏭ RPC get_table_policies nicht verfügbar (OK falls Migration trotzdem grün)" -ForegroundColor Yellow
}

# C.2 Supplier-Articles Safe-View
Write-Host "`nC.2 supplier_articles_safe Existenz"
try {
    $svRes = Invoke-RestMethod -Method GET `
        -Uri "$BASE_URL/rest/v1/supplier_articles_safe?select=id&limit=1" `
        -Headers $headers
    Write-Host "  ✓ View vorhanden + select OK" -ForegroundColor Green
} catch {
    Write-Host "  ✗ View NICHT erreichbar: $($_.Exception.Message)" -ForegroundColor Red
}

# C.3 WhatsApp Tables (wenn nicht skipped)
if (-not $env:SKIP_WHATSAPP) {
    Write-Host "`nC.3 WhatsApp Tables"
    foreach ($t in @("whatsapp_config", "whatsapp_templates", "whatsapp_messages")) {
        try {
            $r = Invoke-RestMethod -Method GET `
                -Uri "$BASE_URL/rest/v1/${t}?select=id&limit=1" `
                -Headers $headers
            Write-Host "  ✓ $t" -ForegroundColor Green
        } catch {
            Write-Host "  ✗ $t : $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# ═══════════════════════════════════════════════════════════
# FINAL
# ═══════════════════════════════════════════════════════════

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "MIGRATION + DB-SETUP COMPLETE" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Smoke-Test Empfehlung (App https://epkolar.github.io/epkolar-app/):"
Write-Host "  1. Kiener-Login: 'kiener' / '$PASSWORD'"
Write-Host "  2. Notifications: 'Alle gelesen' → bleibt 0 nach 60s (RLS-Fix)"
Write-Host "  3. Material-Katalog: ek_preis NULL (B-006-Fix)"
Write-Host "  4. Material zeigt nur Elektro-Gruppen (Gewerk-Filter)"
Write-Host "  5. Sidebar: Riedmann sieht KEIN Mehr-Button (Sprint 49)"
Write-Host ""
Write-Host "Bei Fehler: siehe sql/RUNBOOK_v3953-v3959.md → Rollback-Sektion"
