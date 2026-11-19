# portal-foto (EPKolar Kundenportal, v3.9.1047)

Edge Function: the anonymous customer portal uploads defect photos into the PRIVATE bucket `epkolar-docs`
instead of sending base64 to `portal_submit_defect` (owner rule 18.11.2026: no files in the DB).

## Deploy

```
supabase functions deploy portal-foto --project-ref jiggujpruejkaomgxarp
```

- Source: `supabase/functions/portal-foto/index.ts` (deploy via MCP `deploy_edge_function` with `verify_jwt: true`).
- `verify_jwt = true` (default). The portal sends the legacy anon JWT (`SUPABASE_KEY`) as `Authorization: Bearer` + `apikey`.
- Secrets: only the built-ins `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` (auto-injected, nothing to set).
- CORS: origin `https://epkolar.github.io` only (OPTIONS preflight answered).

## API

| Request | Response |
|---|---|
| `POST {code, defect_id, name, dataUrl}` | `200 {path:"sbpriv:epkolar-docs/portal/<projectId>/<defectId>/<name>.<ext>", url:<signed 7 d>}` |
| `POST {code, action:"sign", paths:[...]}` | `200 {urls:{<input path>: <signed 7 d>}}` (only paths under `portal/<projectId of code>/`) |

`name` = client photo key `[A-Za-z0-9_-]{8,64}`; re-sending the same key for the same defect returns the existing
object (idempotent retry, no second object). Invalid/missing key -> random UUID.

Error bodies are `{error:<code>}` only: `invalid_code` 403, `invalid_defect` 400, `bad_type` 400/415, `bad_image` 400,
`too_large` 413, `limit_defect` / `limit_project` 429, `storage_unavailable` 503, `upload_failed` 502, `bad_request` 400.

## Validation and abuse limits

- Portal code exactly like the RPC: `btrim`, length >= 3, `projects.portal_code = code AND portal_code <> ''`.
- `defect_id`: non-empty, <= 64 chars, `[A-Za-z0-9_-]`.
- MIME only `image/jpeg`, `image/png`, `image/webp`; magic bytes must match the declared type.
- Max 4 MB decoded per photo (body hard cap 6 MB).
- Max 10 objects per defect folder `portal/<pid>/<did>/`.
- Max 60 objects per project per 24 h (counted by listing `portal/<pid>/*/` and `created_at`).
- Counting is list-based, not transactional: two exactly concurrent requests can overshoot a limit by one each. Acceptable for abuse damping.

## Storage access

- Upload/sign use the service role (bypasses storage RLS).
- Staff view these photos with their own login via `_dateiSigniert` -> `_sbSignedDocUrl`. The existing `epkolar-docs`
  SELECT policy is `is_staff() OR (storage.foldername(name))[2] = current_monteur_id()` (docs/handoff/STAND-2026-06-16-STORAGE.md),
  so staff can sign `portal/...`. Whether `is_staff()` is true for every field role was NOT verified here — check
  before release if Monteure must see customer photos (before, the base64 thumbs in `defects.images` were visible to all).

## Release order

1. Deploy this function.
2. Release the app version with the new portal client.
3. Only then apply `sql/portal_submit_defect_keine_dateien_v1047.sql` (after running its probe block).
