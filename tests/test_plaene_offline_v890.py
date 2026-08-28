# -*- coding: utf-8 -*-
"""v3.9.890 - Der Bauplan ist das einzige, was die App NICHT mitnimmt.

Die App ist sonst konsequent offline-faehig: SyncQueue, PhotoQ, ODB fuer
Projekte/Eintraege/Formulare/planData. Genau ein Datentyp faellt heraus - der
Plan. Und das ist ausgerechnet der, den ein Elektrotrupp im Keller oder in der
Tiefgarage braucht, wo es nie Empfang gibt.

────────────────────────────────────────────────────────────────────────────
GEMESSEN (Stand v3.9.888, main c8bd097) - die Kette, Glied fuer Glied
────────────────────────────────────────────────────────────────────────────

1. Der Plan ist nach dem ersten Server-Pull IMMER eine Netz-URL.
   Der Upload schickt die base64 als `file_data` mit; die Storage-Interception
   laedt sie hoch und wirft sie dann weg (index.html:2720-2721):

       const publicUrl=await _sbUploadFile(storagePath,mapped.file_data);
       mapped.file_url=publicUrl;
       delete mapped.file_data; // Don't store base64 in DB

   `_mapPlan` (index.html:1915) faellt danach auf genau diese URL zurueck:

       const du=p.dataUrl||p.data_url||p.file_url||"";

   Und der Reload-Merge (index.html:8148) ERSETZT die lokalen Plan-Objekte
   durch den Server-Stand:

       upd.plans=[..._serverPlans,..._localPendingPlans];

   Damit verliert auch das hochladende Geraet seine Bytes beim naechsten Pull.

2. Der Service Worker klinkt sich bei JEDER Supabase-URL aus (sw.js:37):

       if (url.includes('supabase.co')) return;

   Die Plan-URL ist eine Supabase-Storage-URL
   (`.../storage/v1/object/public/epkolar-files/plans/...`, index.html:1566).
   Der SW sieht sie also - und laesst sie durch, ohne je etwas zu behalten.

3. `_planPdfCache` haelt nur die pdf.js-Dokumente im Arbeitsspeicher
   (index.html:4052: `window._planPdfCache = window._planPdfCache || {}`).
   Das sind PDFDocumentProxy-Objekte, nicht serialisierbar, und beim Neuladen
   weg.

4. Ergebnis im Keller: `_planLoadPdf` faellt in den http-Zweig
   (index.html:4068 `const r = await fetch(dataUrl);`), der Wurf landet im
   catch bei index.html:17272 und der Monteur liest:

       "PDF konnte nicht geladen werden: Failed to fetch"

   Das ist die Meldung eines Netzfehlers. Der wahre Sachverhalt ist ein
   anderer: der Plan wurde nie mitgenommen.

────────────────────────────────────────────────────────────────────────────
WARUM DER ZWISCHENSPEICHER IN INDEXEDDB LIEGEN MUSS UND NICHT IM CACHE STORAGE
────────────────────────────────────────────────────────────────────────────
v3.9.358 hat netz-zuerst fuer die HTML bewusst eingefuehrt, weil Nutzer nach
Deploys auf der Vorversion hingen. Der ganze Update-Weg ist seitdem darauf
gebaut, den Cache Storage WEGZUWERFEN. Gezaehlt: VIER Stellen loeschen ihn
vollstaendig -

    index.html:29-32   Boot, bei SW_VER-Mismatch  -> also bei JEDEM Deploy
    index.html:448     Boot-Watchdog (Auto-Heal)
    index.html:2973-74 _forceCacheClear (Update-Knopf, Kiosk-Self-Update)
    sw.js:23           activate: jeder Cache mit anderem Namen

Ein Plan-Zwischenspeicher im Cache Storage waere damit bei jedem Deploy leer -
und zwar genau dann, wenn ein Monteur morgens die App startet und danach ohne
Empfang in den Keller geht. IndexedDB wird von keiner dieser vier Stellen
angefasst. Der Vorschlag aendert deshalb sw.js NICHT und legt die Plan-Bytes
nach ODB.

Zweiter Punkt zur Vertraeglichkeit: fuer den PLAN ist "zuerst der
Zwischenspeicher" ohne Alterungsrisiko - anders als fuer die index.html. Eine
Revision legt naemlich einen NEUEN Plan an, sie ueberschreibt nicht
(index.html:_commitRevision: `const np={id:uid(),...}`). Plan-Bytes sind pro id
unveraenderlich. Genau darum darf hier gelten, was fuer die HTML verboten ist.

────────────────────────────────────────────────────────────────────────────
GROESSEN - was gemessen ist und was nicht
────────────────────────────────────────────────────────────────────────────
GEMESSEN (Bucket-Konfiguration, oeffentlich abfragbar):
    epkolar-files: public=true, file_size_limit = 52.428.800 Bytes (50 MiB)
Das ist die EINZIGE durchgesetzte Obergrenze im ganzen Plan-Pfad. Im Code gibt
es keine: `handleUpload` liest PDFs roh mit `readAsDataURL` (keine Kompression,
keine Pruefung), `APP_LIMITS.MAX_FILE_MB:10` hat null Leser (Triple-Grep).
Bild-Plaene laufen durch `compressPhoto(file,4000,0.92)`.

NICHT GEMESSEN: die echte Groessenverteilung der Plaene. Die `plans`-Tabelle
ist fuer anon per RLS dicht (HTTP 200, leeres Array), das Storage-Listing
ebenso. Alles Weitere waere Schaetzung und steht deshalb nicht in diesen Tests.

Daraus folgt die Bauentscheidung: Etappe 1 nimmt NUR mit, was ohnehin schon
uebers Netz kam (Gelegenheit statt Vorratshaltung). Sie erzeugt keine einzige
zusaetzliche Anfrage und kein Mobilfunk-Volumen - deshalb braucht sie die
unbekannte Verteilung nicht zu kennen. Ein "ganzes Projekt mitnehmen" waere
Etappe 2 und DARF erst gebaut werden, wenn die Groessen gemessen sind.

────────────────────────────────────────────────────────────────────────────
AUFBAU DIESER DATEI
────────────────────────────────────────────────────────────────────────────
Teil A - VERTRAG: was der Update-Weg heute leistet und was der Vorschlag nicht
         anfassen darf. Diese Riegel sind heute gruen und muessen es bleiben.
Teil B - BEFUND: die Stellen, an denen die Kette heute reisst. Heute gruen -
         sie beschreiben den Ist-Zustand und duerfen erst rot werden, wenn
         der Patch sie ersetzt (dann zeigen die Fix-Riegel in Teil C gruen).
Teil C - FIX: die Riegel fuer den Vorschlag. ROT, solange der Patch fehlt.
Teil D - Umkehrprobe.
"""
import re


# ══ TEIL A - VERTRAG: der Update-Weg bleibt unangetastet ════════════════════

def test_der_sw_bleibt_bei_supabase_aussen_vor(sw_js):
    """Der Plan-Zwischenspeicher darf NICHT im Service Worker gebaut werden -
    sonst faengt der SW plotzlich Storage-Verkehr ab, den er heute bewusst
    durchlaesst (Uploads, signierte URLs, REST)."""
    assert "if (url.includes('supabase.co')) return;" in sw_js, (
        "Der SW klinkt sich nicht mehr bei Supabase aus. Wenn der Plan-Cache "
        "dorthin gewandert ist, faengt der SW auch Uploads und REST-Verkehr ab."
    )


def test_navigation_bleibt_netz_zuerst(sw_js):
    """v3.9.358: sonst haengen Nutzer nach dem Deploy auf der Vorversion."""
    assert "fetch(event.request, { cache: 'no-store' })" in sw_js, (
        "Die Navigation ist nicht mehr netz-zuerst - genau der Zustand, den "
        "v3.9.358 abgestellt hat."
    )


def test_der_versions_poll_bleibt_unbehelligt(sw_js):
    assert "if (url.includes('index.html?_v=')) return;" in sw_js, (
        "Der Versions-Poll laeuft wieder durch den SW-Cache - dann meldet er "
        "womoeglich die eigene Altversion als 'aktuell'."
    )


def test_der_update_weg_wirft_jeden_cache_speicher_weg(index_html, sw_js):
    """Der Grund, warum die Plan-Bytes NICHT in den Cache Storage duerfen.
    Vier Stellen loeschen ihn vollstaendig - eine davon bei jedem Deploy."""
    assert "for(const k of keys)await caches.delete(k);" in index_html, (
        "_forceCacheClear raeumt den Cache Storage nicht mehr komplett."
    )
    assert "names.forEach(function(n){caches.delete(n);});" in index_html, (
        "Der Boot-Pfad raeumt bei SW_VER-Mismatch nicht mehr auf - das ist die "
        "Stelle, die bei JEDEM Deploy feuert."
    )
    assert "if('caches' in window)caches.keys().then(function(k){k.forEach(function(n){caches.delete(n)})});" in index_html, (
        "Der Boot-Watchdog raeumt den Cache Storage nicht mehr."
    )
    assert "keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))" in sw_js, (
        "Der SW loescht beim Aktivieren keine fremden Caches mehr."
    )


def test_die_planbytes_liegen_nicht_im_cache_storage(index_html):
    """Gegenprobe zum vorigen Riegel: wer trotzdem einen eigenen Cache
    aufmacht, baut ihn auf Sand."""
    assert "caches.open" not in index_html, (
        "index.html oeffnet einen Cache-Storage-Cache. Der wird von vier "
        "Stellen wieder geloescht (siehe test_der_update_weg_...). Plan-Bytes "
        "gehoeren nach IndexedDB."
    )


def test_eine_revision_bekommt_eine_neue_id(index_html):
    """Die Voraussetzung dafuer, dass 'zuerst der Zwischenspeicher' bei
    Plaenen erlaubt ist: Plan-Bytes sind pro id unveraenderlich."""
    i = index_html.find("const _commitRevision=(file,dataUrl,w,h,isPdf)=>{")
    assert i != -1, "_commitRevision nicht gefunden"
    block = index_html[i:i + 1400]
    assert "const np={id:uid()" in block, (
        "Eine Revision ueberschreibt jetzt den bestehenden Plan statt einen "
        "neuen anzulegen. Damit waere 'zuerst der Zwischenspeicher' NICHT mehr "
        "gefahrlos - der Monteur bekaeme die alte Revision zu sehen."
    )


def test_die_odb_migration_bleibt_nicht_zerstoerend(index_html):
    """DB_VER darf angehoben werden - aber nur so, dass bestehende Stores
    ueberleben (v3.5.133: sonst verlieren Offline-Nutzer ihre SyncQueue)."""
    assert "STORES.forEach(s=>{if(!db.objectStoreNames.contains(s))db.createObjectStore(s);});" in index_html, (
        "onupgradeneeded legt nicht mehr nur NEUE Stores an - ein DB_VER-Bump "
        "wuerde dann die ungesyncte SyncQueue mitnehmen."
    )


# ══ TEIL B - BEFUND: wo die Kette heute reisst ══════════════════════════════

def test_befund_die_base64_wird_vor_dem_insert_geloescht(index_html):
    assert 'delete mapped.file_data; // Don\'t store base64 in DB' in index_html, (
        "Die Storage-Interception sieht anders aus als gemessen - der Befund "
        "muss neu erhoben werden."
    )


def test_befund_der_plan_faellt_auf_die_netz_url_zurueck(index_html):
    i = index_html.find("function _mapPlan(p){")
    assert i != -1, "_mapPlan nicht gefunden"
    block = index_html[i:i + 300]
    assert 'const du=p.dataUrl||p.data_url||p.file_url||"";' in block, (
        "_mapPlan loest die Plan-Quelle anders auf als gemessen."
    )


def test_befund_der_reload_ersetzt_die_lokalen_plaene(index_html):
    assert "upd.plans=[..._serverPlans,..._localPendingPlans];" in index_html, (
        "Der Reload-Merge sieht anders aus als gemessen - dann stimmt die "
        "Aussage 'auch das hochladende Geraet verliert die Bytes' nicht mehr."
    )


def test_befund_der_pdf_zwischenspeicher_lebt_nur_im_arbeitsspeicher(index_html):
    assert "window._planPdfCache = window._planPdfCache || {};" in index_html, (
        "_planPdfCache ist nicht mehr das gemessene window-Objekt."
    )


def test_befund_es_gibt_keine_groessenpruefung_beim_plan_upload(index_html):
    """MAX_FILE_MB steht in APP_LIMITS und hat null Leser - die einzige echte
    Grenze ist das 50-MiB-Limit des Buckets (serverseitig gemessen)."""
    # v3.9.890: gezaehlt wird OHNE Kommentare - der erklaerende Kommentar am
    # Plan-Cache nennt MAX_FILE_MB woertlich und wurde sonst mitgezaehlt.
    _code = re.sub(r"/\*[\s\S]*?\*/", "", index_html)
    assert _code.count("MAX_FILE_MB") == 1, (
        "MAX_FILE_MB hat jetzt Leser - dann ist die Aussage 'keine Grenze im "
        "Code' ueberholt und die Groessenrechnung muss neu gemacht werden."
    )


# ══ TEIL C - FIX: rot, solange der Patch fehlt ══════════════════════════════

def test_es_gibt_einen_speicher_fuer_plan_bytes(index_html):
    m = re.search(r'const STORES=\[(.*?)\];', index_html)
    assert m, "STORES nicht gefunden"
    assert '"planFiles"' in m.group(1), (
        "Es gibt keinen eigenen ODB-Store fuer die Plan-Bytes. Sie duerfen "
        "NICHT in 'planData' liegen: das Objekt wird bei jeder Ticket-Aenderung "
        "komplett neu geschrieben (ODB.save('planData',planData) haengt am "
        "planData-Effekt) - mehrere MB pro Pin-Verschiebung."
    )


def test_die_db_version_wurde_angehoben(index_html):
    m = re.search(r'const DB_VER=(\d+);', index_html)
    assert m, "DB_VER nicht gefunden"
    assert int(m.group(1)) >= 9, (
        "DB_VER wurde nicht angehoben - onupgradeneeded feuert dann nicht und "
        "der neue Store fehlt bei allen bestehenden Geraeten (ODB.set warnt "
        "nur 'Store missing' und macht still nichts)."
    )


def test_was_ueber_das_netz_kam_wird_mitgenommen(index_html):
    """Der Kern von Etappe 1: kein zusaetzliches Byte, nur nicht wegwerfen."""
    i = index_html.find("async function _planLoadPdf(planId, dataUrl) {")
    assert i != -1, "_planLoadPdf nicht gefunden"
    block = index_html[i:i + 2600]
    assert "_planCachePut(" in block, (
        "Der gerade heruntergeladene Plan wird nicht behalten. Genau hier "
        "liegen die Bytes schon im Arbeitsspeicher (buf) - sie nicht zu "
        "sichern kostet nichts und bringt nichts."
    )


def test_der_zwischenspeicher_wird_zuerst_gefragt(index_html):
    i = index_html.find("async function _planLoadPdf(planId, dataUrl) {")
    block = index_html[i:i + 2600]
    assert "_planCacheGet(" in block, (
        "_planLoadPdf fragt den Zwischenspeicher nicht - ohne Empfang faellt "
        "es weiter in fetch() und wirft 'Failed to fetch'."
    )


def test_der_zwischenspeicher_hat_eine_obergrenze(index_html):
    """Der Bucket erlaubt 50 MiB pro Objekt (gemessen). Ohne eigene Grenze
    kann ein einzelner Scan-Plan den Geraetespeicher fuellen."""
    assert "PLAN_CACHE_MAX_BYTES" in index_html, (
        "Es gibt keine Obergrenze fuer einen mitgenommenen Plan - der Bucket "
        "laesst 50 MiB pro Datei zu."
    )


def test_ein_zu_grosser_plan_wird_gesagt_nicht_geschluckt(index_html):
    i = index_html.find("async function _planCachePut(")
    assert i != -1, "_planCachePut nicht gefunden"
    block = index_html[i:i + 1600]
    assert "PLAN_CACHE_MAX_BYTES" in block, (
        "_planCachePut prueft die Obergrenze nicht."
    )
    assert "__toast" in block, (
        "Ein Plan, der nicht mitgenommen werden konnte (zu gross oder "
        "Speicher voll), verschwindet stillschweigend. Genau das Muster hat "
        "v3.9.223 bei PhotoQ und v3.9.574 bei der SyncQueue abgestellt: der "
        "Nutzer muss es erfahren, sonst glaubt er, der Plan sei dabei."
    )


def test_die_meldung_sagt_was_wirklich_los_ist(index_html):
    assert "wurde nicht mitgenommen" in index_html, (
        "Der Viewer meldet weiter einen Netzfehler ('PDF konnte nicht geladen "
        "werden: Failed to fetch'). Fuer den Monteur im Keller ist das die "
        "falsche Diagnose - das Netz ist nicht kaputt, der Plan war nie da."
    )


def test_kein_link_der_ohne_netz_nicht_gehen_kann(index_html):
    # v3.9.890: Geprueft wird die EIGENSCHAFT - der Link haengt an navigator.onLine -
    # und nicht eine bestimmte Schreibweise. Die Umsetzung behaelt zusaetzlich die
    # _planSrc-Pruefung und klammert deshalb anders.
    import re as _re
    m = _re.search(
        r"_planSrc[^?]{0,60}navigator\.onLine!==false[^?]{0,4}\?\s*React\.createElement\('a',\s*\{href:_planSrc",
        index_html)
    assert m, (
        "Der Fehler-Bildschirm bietet weiter 'Plan im neuen Tab oeffnen' an, ohne "
        "an navigator.onLine zu haengen - offline fuehrt der Knopf zwingend in "
        "denselben Fehler. Ein Angebot, das nicht gehen kann, ist schlimmer als keins."
    )


def test_ein_hochgeladener_plan_bleibt_auf_dem_geraet(index_html):
    """Beim Upload liegen die Bytes bereits als dataUrl vor - sie danach vom
    Server zurueckzuholen waere doppelt bezahlt."""
    i = index_html.find("const handleUpload=e=>{const fls=")
    assert i != -1, "handleUpload (VPlan) nicht gefunden"
    block = index_html[i:i + 4200]
    assert "_planCachePut(" in block, (
        "Der frisch hochgeladene Plan wird nicht mitgenommen - er ist ab dem "
        "naechsten Server-Pull (upd.plans=[..._serverPlans,...]) auch auf dem "
        "hochladenden Geraet nur noch eine URL."
    )


def test_beim_nutzerwechsel_wird_der_plan_speicher_geraeumt(index_html):
    """Geteilte Baustellen-Tablets (v3.9.127 F6). Der bestehende Purge loescht
    nur den Schluessel 'data' je Store - fuer planFiles braucht es clear()."""
    assert 'ODB.clear("planFiles")' in index_html or "ODB.clear('planFiles')" in index_html, (
        "Der Plan-Speicher wird beim Nutzerwechsel nicht geraeumt. Der "
        "bestehende Purge (ODB.del(_s,'data')) trifft ihn NICHT, weil die "
        "Plaene unter eigenen Schluesseln liegen - der naechste Nutzer haette "
        "die Plaene des Vorgaengers auf dem Tablet."
    )


def test_der_neue_code_nutzt_kein_optional_chaining(index_html):
    """Die Datei ist sucrase-transpiliert - '?.' im Quelltext ist ein Bruch."""
    i = index_html.find("async function _planCachePut(")
    if i == -1:
        i = index_html.find("window._planPdfCache = window._planPdfCache || {};")
    block = index_html[i:i + 2600]
    assert "?." not in block, (
        "Im neuen Plan-Cache-Block steht optional chaining ('?.'). Die Datei "
        "wird sucrase-transpiliert ausgeliefert (_optionalChain)."
    )


# ══ TEIL D - Umkehrprobe ════════════════════════════════════════════════════

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html, sw_js):
    z1 = sw_js.replace("fetch(event.request, { cache: 'no-store' })",
                       "fetch(event.request)", 1)
    assert z1 != sw_js, "Rueckbau 1 griff nicht"
    assert "fetch(event.request, { cache: 'no-store' })" not in z1, (
        "Umkehrprobe: der Riegel auf netz-zuerst (v3.9.358) wuerde nicht "
        "anschlagen"
    )

    z2 = index_html.replace("for(const k of keys)await caches.delete(k);", "", 1)
    assert z2 != index_html, "Rueckbau 2 griff nicht"
    assert "for(const k of keys)await caches.delete(k);" not in z2, (
        "Umkehrprobe: der Riegel auf den Cache-Wegwurf wuerde nicht anschlagen"
    )

    z3 = index_html.replace("const np={id:uid(),pid:p.id,name:old.name",
                            "const np={id:old.id,pid:p.id,name:old.name", 1)
    assert z3 != index_html, "Rueckbau 3 griff nicht"
    i3 = z3.find("const _commitRevision=(file,dataUrl,w,h,isPdf)=>{")
    assert "const np={id:uid()" not in z3[i3:i3 + 1400], (
        "Umkehrprobe: der Riegel auf die Unveraenderlichkeit der Plan-id "
        "wuerde nicht anschlagen - und damit waere 'zuerst der "
        "Zwischenspeicher' unbemerkt gefaehrlich geworden"
    )

    assert "caches.open" not in index_html, "Umkehrprobe: Ausgangslage stimmt nicht"
    z4 = index_html + "\ncaches.open('epkolar-plans');\n"
    assert "caches.open" in z4, (
        "Umkehrprobe: der Riegel gegen einen Plan-Cache im Cache Storage "
        "wuerde nicht anschlagen"
    )
