# Overnight-Agenten-Bug-Hunt — Welle 3 Funde (2026-06-07, So nachts)

3 read-only Audit-Agenten (Mobile/Responsive, Material/Bestellungen, Dashboard/Auswertungen). Konservativ:
contained Frontend-Bugs werden gefixt (Triade + eigener Commit); preis-/geschäftssensible + kosmetische → dokumentiert.

## Material / Bestellungen
- **[NIEDRIG-MITTEL] Material#3 Status `bereitgestellt` ist Dead-End → ✅ FIX v3.9.164**: `nextStatus` (13117) gibt für
  `bereitgestellt` null, UND die Lager-Action-Bedingung (13150: angefordert/in_bearbeitung/offen/bestellt) enthält
  `bereitgestellt` NICHT → keine Erledigt/Storno-Buttons → Auftrag steckt fest (wie der v3.9.43-`bestellt`-Fix). Fix:
  `||ord.status==="bereitgestellt"` in 13150 → Erledigt/Storno (13158/13159, ungated) erscheinen.
- **[MITTEL] Material#1 Bestell-Dedup First-Wins statt Min-Preis/Händler — DOKUMENTIERT (preis-sensibel)**: `openPV`
  (12656-12660) nimmt pro `supplier_id` den ERSTEN Treffer (`if(!bySup[sid])`), nicht den günstigsten → gezeigter EK +
  „bester Händler" abhängig von Array-Reihenfolge, günstigere Variante desselben Händlers verworfen. Fix: Min pro Händler
  (`if(!bySup[sid]||newEk<bySup[sid].ek)`). Ändert Einkaufs-Anzeige → Sebastian-Review.
- **[MITTEL] Material#2 EK-Fallback auf Listenpreis verfälscht Vergleich — DOKUMENTIERT**: `ek:parseFloat(sa.ek_preis)||
  parseFloat(sa.listenpreis)||0` (12659) — bei NULL-ek_preis (z.B. Monteur via `supplier_articles_safe`) wird Listenpreis
  als EK genutzt → Summen/bester-Händler verfälscht. Fix: Listenpreis NICHT als EK; fehlenden EK als „kein EK" markieren.
  Betrifft nur EK-lose Rollen die openPV erreichen → Review (zusammen mit #1).

## Mobile / Responsive (sonst gründlich auditiert, kein P0/P1)
- **[P2] Mobile#1 Foto-Queue-Panel überlappt 2-zeiligen Mobile-Header — FIX-Kandidat v3.9.164**: Panel `position:fixed;
  top:56` (5703), aber Mobile-Header ist 2-reihig (~80-100px) → Panel verdeckt Header/eigenen Trigger. Fix: `top:isMob?96:56`.
- **[P3 iOS] fixe Top-Panels (5703/5738) ohne `env(safe-area-inset-top)`** → Notch-Overlap im PWA-Standalone. DOKUMENTIERT.
- **[P3 iOS] zentrierte Modals ohne safe-area-bottom** (maxHeight:90vh nahe Home-Indicator). DOKUMENTIERT, gering.

## Dashboard / Auswertungen (überraschend sauber — keine harten Bugs)
Verifiziert SAUBER: absPerName-Doppelzählung (v3.9.31), KW-Mathematik (ISO), SVG-Charts (÷0/NaN-safe), Skalierung ≤100%.
- **[NIEDRIG] Stunden-KPI firmenweit für alle Rollen** (8578/8843): ein Monteur sieht Firmen-Gesamtstunden statt eigene.
  Evtl. gewollt (Label generisch). DOKUMENTIERT.
- **[NIEDRIG] Tankkosten-Sub inkl. stillgelegt** (16453) vs Chart filtert stillgelegt (16381) → Sub > Chart-Summe. Kosmetisch.
- Dead Code: `namePrefix` (16371) ungenutzt; `maxD` (8004) pro Iteration neu — harmlos.
