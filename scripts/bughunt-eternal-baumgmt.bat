@echo off
setlocal EnableDelayedExpansion

REM ============================================================
REM EPKolar Eternal Bug Hunt - Loop-Driver (Baumanagement)
REM ============================================================
REM Pattern aus MotorLog-Setup adaptiert:
REM - Stop-Flag: T:\STOP-BUG-HUNT-BAUMGMT.flag (UNIQUE, NICHT MotorLog teilen!)
REM - Branch: cc-bug-hunt-eternal/2026-04-26
REM - 4 Sprints/Tag konservativ (Token-Pool mit MotorLog geteilt)
REM - 90 min Sleep zwischen Sprints (5400s)
REM - 4h Cooldown bei rate_limit (14400s)
REM - 14 Tage Hard-Cap
REM - 3 Failures = Halt
REM
REM Usage:
REM   bughunt-eternal-baumgmt.bat            -- normaler Lauf
REM   bughunt-eternal-baumgmt.bat --dry-run  -- nur Setup-Validation, KEIN CC-Call
REM ============================================================

REM -- Dry-Run-Flag check (FIRST!) --
set "DRY_RUN=0"
if "%~1"=="--dry-run" set "DRY_RUN=1"
if "%~1"=="-n" set "DRY_RUN=1"

set "REPO_PATH=T:\05_Claude\02_Baumanagment & Zeiterfassungs - APP\03_Repos\epkolar-app"
set "STOP_FLAG_LOCAL=T:\STOP-BUG-HUNT-BAUMGMT.flag"
set "STOP_FLAG_REMOTE_NAME=STOP-BUG-HUNT-BAUMGMT.flag"
set "STATE_FILE=scripts\bughunt-state-baumgmt.txt"
set "QUEUE_FILE=scripts\bughunt-queue-baumgmt.txt"
set "LOG_FILE=scripts\bughunt-log-baumgmt.txt"
set "OUTPUT_FILE=scripts\bughunt-last-output-baumgmt.txt"
set "REPORT_FILE=docs\bug-hunt\REPORT.md"
set "BRANCH=cc-bug-hunt-eternal/2026-04-26"
set "MASTER_PROMPT_TEMPLATE=docs\bug-hunt\MASTER_PROMPT_TEMPLATE.md"
set "SLEEP_BETWEEN_SPRINTS_SEC=5400"
set "COOLDOWN_RATE_LIMIT_SEC=14400"
set "MAX_FAIL_COUNT=3"
set "MAX_LIFETIME_DAYS=12"
set "POWERPLAN_BACKUP_FILE=scripts\powerplan-backup-baumgmt.txt"

cd /d "%REPO_PATH%"

if "%DRY_RUN%"=="1" (
  echo [DRY-RUN] Skipping power-plan change, anti-sleep heartbeat, CC-call.
  echo [DRY-RUN] Validating setup files exist...
  if not exist "%STATE_FILE%" (echo   FAIL: state file missing & exit /b 1)
  if not exist "%QUEUE_FILE%" (echo   FAIL: queue file missing & exit /b 1)
  if not exist "%MASTER_PROMPT_TEMPLATE%" (echo   FAIL: master prompt template missing & exit /b 1)
  if not exist "%REPORT_FILE%" (echo   FAIL: REPORT.md missing & exit /b 1)
  echo   OK: state, queue, template, report all present.
  echo [DRY-RUN] Stop-flag-check (local): %STOP_FLAG_LOCAL%
  if exist "%STOP_FLAG_LOCAL%" (
    echo   STOP-FLAG PRESENT - would exit immediately. Exiting dry-run.
    exit /b 0
  )
  echo   No stop flag present.
  echo [DRY-RUN] Reading first non-comment line of queue...
  set "FIRST_TOPIC="
  for /f "usebackq tokens=* delims=" %%L in ("%QUEUE_FILE%") do (
    set "LINE=%%L"
    set "FIRST_CHAR=!LINE:~0,1!"
    if "!FIRST_TOPIC!"=="" if NOT "!FIRST_CHAR!"=="#" if NOT "!LINE!"=="" set "FIRST_TOPIC=!LINE!"
  )
  echo   First topic: !FIRST_TOPIC!
  echo [DRY-RUN] Power-plan backup test ^(would write %POWERPLAN_BACKUP_FILE%^)
  powercfg /getactivescheme > "%POWERPLAN_BACKUP_FILE%"
  if exist "%POWERPLAN_BACKUP_FILE%" (
    echo   OK: powerplan backup written.
  ) else (
    echo   FAIL: powerplan backup not written
    exit /b 2
  )
  echo [DRY-RUN] All checks passed. Exiting without sprint execution.
  exit /b 0
)

REM ============================================================
REM NORMAL RUN (not dry-run)
REM ============================================================

REM -- Power-Plan Backup + High-Performance setzen --
powercfg /getactivescheme > "%POWERPLAN_BACKUP_FILE%"
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
powercfg /change monitor-timeout-ac 0
powercfg /change standby-timeout-ac 0
powercfg /change disk-timeout-ac 0

REM -- Anti-Sleep im Hintergrund (PowerShell-Heartbeat alle 60s) --
start "BUGHUNT-AntiSleep-Baumgmt" /MIN powershell -NoProfile -WindowStyle Hidden -Command ^
  "Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class P { [DllImport(\"kernel32.dll\")] public static extern uint SetThreadExecutionState(uint esFlags); }'; while ($true) { [P]::SetThreadExecutionState(0x80000000 -bor 0x00000001 -bor 0x00000040); $w = New-Object -ComObject WScript.Shell; $w.SendKeys('{SCROLLLOCK 2}'); Start-Sleep -Seconds 60 }"

REM -- State laden (oder erzeugen) --
if not exist "%STATE_FILE%" (
  echo SPRINT_COUNTER=0> "%STATE_FILE%"
  echo FAIL_COUNT=0>> "%STATE_FILE%"
  echo LAST_SUCCESS=>> "%STATE_FILE%"
  echo START_DATE=%DATE%>> "%STATE_FILE%"
  echo LIFETIME_DAYS=%MAX_LIFETIME_DAYS%>> "%STATE_FILE%"
  echo LAST_RATE_LIMIT=>> "%STATE_FILE%"
)

echo [%DATE% %TIME%] BUGHUNT-BAUMGMT started >> "%LOG_FILE%"

REM -- Hauptschleife --
:LOOP
  REM 1. Stop-Flag-Check (lokal)
  if exist "%STOP_FLAG_LOCAL%" goto :STOP_NORMAL

  REM 2. Stop-Flag-Check (remote, via git fetch main only)
  git fetch origin main --quiet
  for /f %%i in ('git ls-tree origin/main %STOP_FLAG_REMOTE_NAME% --name-only 2^>nul') do (
    if "%%i"=="%STOP_FLAG_REMOTE_NAME%" goto :STOP_NORMAL
  )

  REM 3. Lifetime-Check (Setup-Datum aus State, gegen heute)
  REM TODO: PowerShell-Snippet mit Get-Date arithmetic, halt bei MAX_LIFETIME_DAYS

  REM 4. Failure-Check
  set "FAIL=0"
  for /f "tokens=1,2 delims==" %%a in (%STATE_FILE%) do (
    if "%%a"=="FAIL_COUNT" set "FAIL=%%b"
  )
  if !FAIL! GEQ %MAX_FAIL_COUNT% goto :STOP_FAILURE

  REM 5. Cooldown-Check (LAST_RATE_LIMIT)
  REM TODO: wenn LAST_RATE_LIMIT < 4h alt -> continue mit langem sleep

  REM 6. Sprint-Counter inkrementieren + Topic aus Queue lesen
  set "NEW_SPRINT=1"
  for /f "tokens=1,2 delims==" %%a in (%STATE_FILE%) do (
    if "%%a"=="SPRINT_COUNTER" set /a NEW_SPRINT=%%b+1
  )

  REM Topic aus Queue.txt holen - Zeile NEW_SPRINT (ohne Kommentare/Leerzeilen)
  set "TOPIC="
  set "LINE_IDX=0"
  for /f "usebackq tokens=* delims=" %%L in ("%QUEUE_FILE%") do (
    set "LINE=%%L"
    set "FIRST_CHAR=!LINE:~0,1!"
    if NOT "!FIRST_CHAR!"=="#" if NOT "!LINE!"=="" (
      set /a LINE_IDX+=1
      if !LINE_IDX!==!NEW_SPRINT! set "TOPIC=!LINE!"
    )
  )

  REM Round 3+ Auto-Increment falls Topic leer
  if "!TOPIC!"=="" (
    set /a ROTATE_IDX=^(!NEW_SPRINT! - 25 - 1^) %% 25 + 1
    set /a PASS_NUM=^(!NEW_SPRINT! - 26^) / 25 + 2
    REM Re-fetch ROTATE_IDX-tes Non-Comment-Topic aus Queue als Basis
    set "BASE_TOPIC="
    set "LINE_IDX2=0"
    for /f "usebackq tokens=* delims=" %%L in ("%QUEUE_FILE%") do (
      set "LINE=%%L"
      set "FIRST_CHAR=!LINE:~0,1!"
      if NOT "!FIRST_CHAR!"=="#" if NOT "!LINE!"=="" (
        set /a LINE_IDX2+=1
        if !LINE_IDX2!==!ROTATE_IDX! set "BASE_TOPIC=!LINE!"
      )
    )
    set "TOPIC=Re-Audit !BASE_TOPIC! (Pass !PASS_NUM!, Fokus: neue Findings seit Pass !PASS_NUM!-1)"
  )

  REM 7. Master-Prompt bauen aus Template
  set "TEMP_PROMPT=%TEMP%\bughunt-prompt-baumgmt-!NEW_SPRINT!.txt"
  powershell -NoProfile -Command ^
    "(Get-Content '%MASTER_PROMPT_TEMPLATE%') -replace '\{SPRINT_ID\}','!NEW_SPRINT!' -replace '\{TOPIC\}','!TOPIC!' -replace '\{DATE\}','%DATE%' | Set-Content '!TEMP_PROMPT!'"

  REM 8. CC-Call (Claude Code via CLI - Sebastian muss Pfad ggf. anpassen)
  echo [%DATE% %TIME%] Starting Sprint !NEW_SPRINT!: !TOPIC! >> "%LOG_FILE%"

  call claude code --prompt-file "!TEMP_PROMPT!" --no-interactive > "%OUTPUT_FILE%" 2>&1
  set "EXIT_CODE=!errorlevel!"

  REM 9. Result-Parse
  findstr /C:"rate_limit" "%OUTPUT_FILE%" >nul
  if !errorlevel!==0 (
    echo [%DATE% %TIME%] RATE LIMIT - cooldown 4h >> "%LOG_FILE%"
    powershell -NoProfile -Command ^
      "(Get-Content '%STATE_FILE%') -replace 'LAST_RATE_LIMIT=.*','LAST_RATE_LIMIT=%DATE% %TIME%' | Set-Content '%STATE_FILE%'"
    timeout /t %COOLDOWN_RATE_LIMIT_SEC% /nobreak
    goto :LOOP
  )

  if !EXIT_CODE!==0 (
    REM Success - State-Update + Reset Fail-Counter
    powershell -NoProfile -Command ^
      "(Get-Content '%STATE_FILE%') -replace 'SPRINT_COUNTER=.*','SPRINT_COUNTER=!NEW_SPRINT!' -replace 'FAIL_COUNT=.*','FAIL_COUNT=0' -replace 'LAST_SUCCESS=.*','LAST_SUCCESS=%DATE% %TIME%' | Set-Content '%STATE_FILE%'"
    echo [%DATE% %TIME%] SUCCESS Sprint !NEW_SPRINT! >> "%LOG_FILE%"
  ) else (
    REM Failure - increment fail counter
    set /a FAIL+=1
    powershell -NoProfile -Command ^
      "(Get-Content '%STATE_FILE%') -replace 'FAIL_COUNT=.*','FAIL_COUNT=!FAIL!' | Set-Content '%STATE_FILE%'"
    echo [%DATE% %TIME%] FAILURE !FAIL!/!MAX_FAIL_COUNT! - Sprint !NEW_SPRINT! exit !EXIT_CODE! >> "%LOG_FILE%"
  )

  REM 10. Sleep zwischen Sprints (mit Stop-Check-Subloop alle 60s)
  set /a SLEEP_REMAIN=%SLEEP_BETWEEN_SPRINTS_SEC%
  :SLEEP_LOOP
    if exist "%STOP_FLAG_LOCAL%" goto :STOP_NORMAL
    timeout /t 60 /nobreak >nul
    set /a SLEEP_REMAIN-=60
    if !SLEEP_REMAIN! GTR 0 goto :SLEEP_LOOP

  goto :LOOP

:STOP_NORMAL
echo [%DATE% %TIME%] STOPPED via flag (normal) >> "%LOG_FILE%"
echo. >> "%REPORT_FILE%"
echo --- >> "%REPORT_FILE%"
echo STOPPED at %DATE% %TIME% via stop-flag >> "%REPORT_FILE%"
goto :CLEANUP

:STOP_FAILURE
echo [%DATE% %TIME%] STOPPED via failure-cap (%MAX_FAIL_COUNT% consecutive fails) >> "%LOG_FILE%"
echo. >> "%REPORT_FILE%"
echo --- >> "%REPORT_FILE%"
echo HALTED at %DATE% %TIME% - %MAX_FAIL_COUNT% consecutive failures >> "%REPORT_FILE%"
goto :CLEANUP

:CLEANUP
REM Power-Plan restore
if exist "%POWERPLAN_BACKUP_FILE%" (
  for /f "tokens=4" %%g in ("%POWERPLAN_BACKUP_FILE%") do powercfg /setactive %%g
)

REM Anti-Sleep-Prozess killen
taskkill /FI "WINDOWTITLE eq BUGHUNT-AntiSleep-Baumgmt*" /F >nul 2>&1

REM Final-Push
git add docs/bug-hunt/REPORT.md "%LOG_FILE%" "%STATE_FILE%"
git commit -m "hunt: stopped at sprint !NEW_SPRINT!" 2>nul
git push origin %BRANCH% 2>nul

endlocal
exit /b 0
