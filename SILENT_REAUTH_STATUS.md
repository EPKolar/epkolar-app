# Silent Re-Auth Status nach v3.8.35 L1-Removal · 2026-04-25

**Analyse-Basis:** HEAD `282c3de` (v3.8.38).
**Methode:** `grep -n 'epkolar_gc\|_silentReAuth\|silent.*auth' index.html`
**Zweck:** VORAB-Check für Overnight #2 — dokumentieren, **nicht** fixen.

## TL;DR

`_silentReAuth` existiert noch, ist aber seit v3.8.35 **ein Stub**: loggt eine Warnung, nullt `_authToken/_authRefreshToken`, gibt `null` zurück. Kein tatsächlicher Re-Auth-Pfad aktiv. Die Fallback-Kette für abgelaufene Sessions ist **einzig `refresh_token`** (7 Tage Lifetime). Wenn Refresh scheitert → User wird ausgeloggt, muss neu einloggen.

## `_silentReAuth` Funktion (L1152-1161)

```js
async function _silentReAuth(){
  // v3.8.35: Silent re-auth via cached plaintext-password (epkolar_gc = {e:btoa,p:btoa})
  // wurde komplett entfernt. base64 ist reversibel → effektiv Klartext-PW in localStorage.
  // Fallback war "App loggt sich automatisch wieder ein wenn refresh_token stirbt"; der
  // refresh_token hat 7 Tage Default-Lifetime, der überbrückt die meisten realen
  // Szenarien. Bei echtem Ablauf: User loggt sich neu ein — das ist normale Web-UX.
  console.warn("[Auth] Silent re-auth not available (epkolar_gc removed v3.8.35) — user re-login required");
  _authToken=null;_authRefreshToken=null;
  return null;
}
```

**Verhalten:** immer `null` + Warn-Log. Nullt Token-Variablen.

## Aufrufer-Analyse

| Line | Kontext | Was passiert wenn null zurückkommt? |
|-----:|---------|-------------------------------------|
| 1143 | `_sbAuthRefresh` — kein `_authRefreshToken` | Return `null` aus `_sbAuthRefresh` → Aufrufer kriegt `null`, hangeln sich weiter |
| 1145 | `_sbAuthRefresh` — Refresh-HTTP failed | Gleich wie 1143, HTTP-Fehler wird geswallowed |
| 1147 | `_sbAuthRefresh` — Refresh-HTTP throw | Dto. |
| 1183 | `_restoreAuth` — JWT-Shape ungültig | `_authToken` bleibt null; App verhält sich wie ausgeloggt |
| 1186 | `_restoreAuth` — Token älter als 50 min | Wie 1183 |
| 1187 | `_restoreAuth` — Parse-error | Wie 1183 |

**Alle Aufrufer** behandeln `null` defensiv. Keine Crashes.

## Konsequenzen für den User

1. **Aktive Session (Token frisch):** Nix geändert. Funktioniert.
2. **Token expired (1h), refresh_token valid (<7 Tage):** `_sbAuthRefresh` → `/token?grant_type=refresh_token` succeeds → neuer access+refresh. Normal.
3. **refresh_token revoked oder >7 Tage alt:** `_sbAuthRefresh` → 4xx → ruft `_silentReAuth` → `null` → `_authToken=null`. Der nächste `_authRetry` liefert dann ebenfalls 401 und UI sollte einen Login-Prompt zeigen. (Genau dieser Flow ist über das ganze System verteilt und wurde durch L1 nicht beschädigt.)
4. **Offline:** Betroffen ist nur `_sbAuthRefresh` (Netzwerk-Call) — Offline-Login nutzt `_OFFPW.verify` gegen IDB und ist unabhängig von Silent-Re-Auth.

## Gegen-Check 1: Nutzt irgendwer `epkolar_gc` noch lesend?

```
L540 _selfTest (smoke) → invertiert (erwartet NICHT vorhanden)
L1166 _sbAuthLogout → defensive removeItem (historical residue)
L4337 logout-handler → defensive removeItem (v3.8.34 QW1+QW2)
```

**Kein Leser mehr.** Alle aktiven Referenzen sind defensive Cleanups oder Stub-Kommentare.

## Gegen-Check 2: Wird `epkolar_gc` noch irgendwo geschrieben?

Pytest: `tests/test_security.py::test_no_epkolar_gc_setitem` — regression guard, läuft in CI-Suite durch. Kein `localStorage.setItem('epkolar_gc', ...)` mehr im File.

## Beurteilung

**Funktional:** Silent Re-Auth **existiert nicht mehr**. Die Funktion ist ein Stub.

**Ist das ein Bug?** Meinung: **Nein, aber eine UX-Regression.**

- **Vorher (≤v3.8.34):** User kam nie ausgeloggt (außer refresh_token >7 Tage tot → wurde durch gc-cached PW überbrückt).
- **Jetzt (≥v3.8.35):** User muss sich neu einloggen wenn refresh_token kaputt/verfallen. 

Praktisch heißt das:
- Daily-User (Login min. 1× pro Woche): **Unverändert**.
- Kiosk-/Werkstatt-Tablet das wochenlang läuft: Muss wöchentlich kurz nachloggen. UX-Reibung.
- User auf mehreren Geräten: Unverändert (jedes Gerät hat eigenen refresh).

**Fix-Optionen (Sebastian-Entscheidung, NICHT in diesem Run):**

1. **Status Quo behalten** (empfohlen für Security). User loggt halt ab und zu neu ein.
2. **L1 revertieren** → `epkolar_gc` zurück. base64-Reversibilität akzeptiert.
3. **Refresh-Token-TTL verlängern** in Supabase Dashboard auf 30/90 Tage. Reduziert Re-Login-Frequenz ohne Plaintext-Cache.
4. **"Remember me"-Option** mit expliziter User-Zustimmung (längere refresh_token-Lifetime nur wenn opt-in).

## Empfehlung

**Keine sofortige Aktion nötig.** Silent-Re-Auth-Stub ist intentional. Wenn Sebastian UX-Regression bei inaktiven Usern beobachtet → Option 3 (Dashboard-Setting) ist der niederrisikoste Fix.

## Markierung

Dieser Status ist VORAB-Check für Overnight #2. Alle Blöcke 1-7 laufen normal weiter, unter der H1-Regel "Auth-Zonen NICHT anfassen".
