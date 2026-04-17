// SQL-Runner für EPKolar — führt B006b + B007 in Reihenfolge aus
// Benötigt: SUPABASE_DB_URL in .env (Pooler-String mit Passwort)
//
// Pooler-URL findest du in Supabase Dashboard → Project Settings → Database
//   → Connection String → "Transaction" (Port 6543) oder "Session" (Port 5432)
//   → Format: postgres://postgres.jiggujpruejkaomgxarp:<PASSWORD>@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
//
// Run:  SUPABASE_DB_URL="postgres://..." node sql-runner.mjs
// Oder: echo 'SUPABASE_DB_URL=postgres://...' > .env && node --env-file=.env sql-runner.mjs

import pg from 'pg';
import fs from 'fs';
import path from 'path';

const url = process.env.SUPABASE_DB_URL;
if (!url) {
  console.error('❌ SUPABASE_DB_URL nicht gesetzt. Bitte in .env eintragen.');
  console.error('   Format: postgres://postgres.<ref>:<PWD>@<region>.pooler.supabase.com:6543/postgres');
  process.exit(1);
}

const files = ['B006b_HEILUNGS_SQL.sql', 'B007_EXECUTE.sql'];
const here = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Z]:)/, '$1'));

const client = new pg.Client({ connectionString: url, ssl: { rejectUnauthorized: false } });

try {
  await client.connect();
  console.log('✅ verbunden');

  for (const f of files) {
    const full = path.join(here, f);
    if (!fs.existsSync(full)) {
      console.error('  ⚠ Datei fehlt:', full);
      continue;
    }
    console.log('▶', f);
    const sql = fs.readFileSync(full, 'utf8');
    try {
      const res = await client.query(sql);
      const rows = Array.isArray(res) ? res : [res];
      for (const r of rows) {
        if (r && r.rows && r.rows.length) {
          console.log('  Rows:', r.rows.length, 'example:', JSON.stringify(r.rows[0]));
        }
      }
      console.log('  ✅ ok');
    } catch (e) {
      console.error('  ❌', e.message);
    }
  }

  console.log('\n=== FINAL VERIFICATION ===');
  const v1 = await client.query(`
    SELECT routine_name FROM information_schema.routines
    WHERE routine_schema='public'
      AND routine_name IN ('current_monteur_id','current_user_role','current_user_pk','is_staff')
    ORDER BY routine_name`);
  console.log('Helpers:', v1.rows.map(r => r.routine_name).join(', '));

  const v2 = await client.query(`
    SELECT tablename, COUNT(*) AS policy_count
    FROM pg_policies
    WHERE schemaname='public'
      AND tablename IN ('arbeitsscheine','time_entries','notifications',
                        'urlaubsantraege','fahrtenbuch','as_checklist',
                        'as_kommentare','worker_kompetenzen')
    GROUP BY tablename ORDER BY tablename`);
  console.log('\nB-007 Policies:');
  for (const r of v2.rows) console.log('  ' + r.tablename.padEnd(22) + r.policy_count);

  const totalCount = v2.rows.reduce((a, r) => a + Number(r.policy_count), 0);
  console.log('\nTotal B-007 Policies:', totalCount, totalCount >= 16 ? '✅' : '❌ (expected ≥16)');

} finally {
  await client.end();
}
