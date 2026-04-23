# preview/ — Standalone UI-Mocks

Dieser Ordner enthält **Preview-HTML-Files**, die Features skizzieren, **ohne in `index.html` gemergt** oder von einem Build-Step angefasst zu werden.

## Zweck

- **Design-Iteration** vor Integration in die App
- **Sebastian-Review** (Mockup öffnen, URL teilen, Feedback sammeln)
- **Stakeholder-Demos** ohne Admin-Account
- **Dokumentation** wie eine Feature-UI gedacht ist, mit echtem HTML statt Screenshots

## Was steckt drin

| File | Feature | Status |
|---|---|---|
| `whatsapp_ui_v0.html` | Feature 12 WhatsApp-Benachrichtigungen | Schema deployed (pending), UI-Preview bereit |
| `WHATSAPP_UI_README.md` | Integration-Plan, Mock-vs-real-Tabelle, Schema-Lücken | Verlinkt aus `ROADMAP.md` |

## Regeln

1. **Kein Import** aus `index.html` oder umgekehrt. Preview-Files sind 100 % standalone.
2. **Kein npm-Build** berührt diesen Ordner. Die App wird nicht gebundled; Preview ebenso.
3. **Design-Tokens 1:1 kopieren** aus `THEMES.dark` (siehe jeweiliges Preview für die Werte).
4. **React via CDN** (`unpkg.com`) — wie in `index.html`. Keine lokale `node_modules/`.
5. **Pure State** — kein Supabase-Call, kein Fetch (außer React-CDN beim Load).
6. **Mock-Fixtures hart im JS** — 3-8 Entries pro Entität reichen für Review.
7. **Role-Switch** im Preview nachbilden, damit Sebastian RLS-Sicht pro Rolle prüft.

## Öffnen

```bash
# Einfach Doppel-Klick im Explorer → file:// im Browser
start preview/whatsapp_ui_v0.html      # Windows

# Oder Local Server (empfohlen für MIME-Check):
python -m http.server 8000 --directory .
# → http://localhost:8000/preview/whatsapp_ui_v0.html
```

## Neue Preview anlegen

Pattern folgen (siehe `whatsapp_ui_v0.html`):

1. `<!DOCTYPE html>` + `<meta charset="UTF-8">` + CSS-Vars im `:root`
2. React 18 production.min.js + react-dom.production.min.js via unpkg CDN
3. `React.createElement` (kein JSX — matcht index.html Convention)
4. Mock-Fixtures als Top-Level `const`
5. `perm(role)`-Pure-Function spiegelt Schema-RLS
6. `ReactDOM.createRoot(document.getElementById("root")).render(...)` am Ende
7. Separates `<FEATURE>_README.md` mit Mock-vs-real-Tabelle + Integration-Plan

## Was NICHT hier gehört

- **Utility-Scripts** → `sql/_check_*.js`
- **Test-Files** → `tests/`
- **Audit-Docs** → `sql/*.md`
- **Archive** → `_archiv/`
- **Produktive Features** → `index.html`

## Integration-Workflow

Wenn ein Preview grün-Licht bekommt:

1. Sebastian reviewt Preview
2. Feedback-Issues → `<FEATURE>_README.md` aktualisieren
3. **Kein direktes Copy-Paste** in index.html — Review der Integration separat
4. Integration-Session plant die nötigen Changes (Supabase-Calls, RLS-Checks, Test-Coverage)
5. Nach Merge bleibt Preview als Historical-Reference liegen (oder wird in `_archiv/preview/` verschoben)
