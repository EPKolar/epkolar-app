# Die anklickbaren Nicht-Knoepfe, einzeln eingeordnet

**Erzeugt von `scripts/bedienelemente_124_bericht.py`.** Wer eine Einordnung
anzweifelt, laesst das Skript neu laufen und vergleicht - eine von Hand
geschriebene Liste ueber 124 Stellen waere nicht nachpruefbar.

🔴 **Die Tabellen unten zeigen den Stand NACH dem Bau.** Vor
v3.9.969 waren es **124** Stellen; die vierzehn Sortierkoepfe haben ihren
Tastaturzugang bekommen und fallen damit aus der Aufnahme heraus. Was hier
steht, sind die **110**, die noch offen sind. Wer die urspruenglichen 124
sehen will, laesst das Skript gegen `git show a57663b:index.html` laufen.

## Die Klassen

| Klasse | heisst | Folge |
|---|---|---|
| **BEDIENELEMENT** | loest eine Handlung aus, die es sonst nirgends gibt | bekommt Tastaturzugang |
| **DOPPELWEG** | ein echter Knopf in der Naehe ruft dasselbe | unveraendert |
| **KEIN ELEMENT** | der `onClick` tut etwas Nebensaechliches | unveraendert |
| **UNSICHER** | am Quelltext nicht entscheidbar | **unveraendert**, und gemeldet |

Die vierte Klasse steht im Auftrag selbst: *"Wenn du bei einem unsicher bist:
unveraendert lassen und als unsicher melden. Lieber ein fehlender Zugang als
ein Phantom in der Tab-Reihenfolge."*

## 🔴 Warum nicht alle 82 BEDIENELEMENTE gebaut worden sind

Die Arbeitsscheinliste hat **bei 1440 px schon heute 1882 Tab-Stopps**, bei
390 px 941 - gemessen mit `scripts/tabreihenfolge_messen.py` an der echten
Saat. Sie rendert 185 Zeilen mit je mehreren Formularfeldern und Knoepfen.

Drei ihrer anklickbaren Tabellenzellen rufen **alle dieselbe** Funktion
(`_openEditGuarded`). Gaebe man jeder einen Tab-Stopp, waeren das **555
weitere**. Eine Tab-Reihenfolge, durch die niemand mehr durchkommt, ist kein
Zugang - sie ist ein neuer Mangel mit dem Aussehen einer Kur.

Der richtige Weg dort ist **ein Stopp je ZEILE**, nicht je Zelle. Das ist ein
Umbau der Tabellenstruktur, kein Ergaenzen von Attributen, und es braucht eine
eigene Messung. **Frage an Sebastian.**

Gebaut wurden deshalb die **Sortierkoepfe**: ein Stopp je SPALTE, Sortieren
ist nirgends sonst erreichbar, und die Tab-Reihenfolge der Arbeitsscheinliste
ist dadurch von 1882 auf **1894** gewachsen - exakt um die zwoelf.

## 🔴 Was an dieser Einordnung unsicher ist

* Der Zaehler, der "steht in einer Wiederholung" erkennen sollte, hat sich
  **als unbrauchbar erwiesen**: er meldet `7` fuer die Sortierkoepfe, die
  einmal je Spalte gerendert werden. Er zaehlt umschliessende `.map(` ueber
  eine Klammerbilanz, und die verrechnet sich an Klammern in Zeichenketten.
  **Die Spalte steht deshalb nicht in dieser Tabelle** - eine Zahl, von der
  ich weiss, dass sie falsch ist, gehoert nicht in einen Bericht.
* "Ein Knopf in der Naehe ruft dasselbe" sucht in einem Fenster von 4000
  Zeichen. Ein Knopf weiter weg wird nicht gefunden; dann steht hier
  faelschlich BEDIENELEMENT statt DOPPELWEG.
* Ob ein `div` mit `onClick` am Schirm wirklich erreichbar und sinnvoll ist,
  sagt diese Tabelle nicht. Sie liest den Quelltext.

## Die Zahlen

| Klasse | Anzahl |
|---|---|
| BEDIENELEMENT | 68 |
| DOPPELWEG | 35 |
| UNSICHER | 5 |
| KEIN ELEMENT | 2 |
| **gesamt** | **110** |

## BEDIENELEMENT (68)

| Ansicht | Tag | eigener Knopf | `onClick` | Begruendung |
|---|---|---|---|---|
| ASKommentarePanel | `div` | nein | `()=>insertMention(w)` | Loest insertMention aus; kein Knopf in der Naehe ruft dasselbe. |
| AbsView | `div` | nein | `()=>{if(isAdmin){setSel(m);setSubView("kalender");}}` | Loest setSel, setSubView aus; kein Knopf in der Naehe ruft dasselbe. |
| AbsView | `td` | nein | `()=>{if(isAdmin){setSel(m);setSubView("kalender");}}` | Loest setSel, setSubView aus; kein Knopf in der Naehe ruft dasselbe. |
| AbsView | `div` | ja | `()=>{if(inM&&!we)tog(day);}` | Loest tog aus; kein Knopf in der Naehe ruft dasselbe. |
| AbsView | `div` | nein | `()=>_openAttest(f)` | Loest _openAttest aus; kein Knopf in der Naehe ruft dasselbe. |
| AbsView | `div` | nein | `()=>{setSel(m);setSubView("kalender");}` | Loest setSel, setSubView aus; kein Knopf in der Naehe ruft dasselbe. |
| AbsView | `div` | nein | `()=>{if(at2){setSel(m);setMo(d.getMonth());setSubView("kalender");}}` | Loest setSel, setMo, setSubView aus; kein Knopf in der Naehe ruft dasselbe. |
| AdminPanel | `div` | nein | `()=>setSel(u.id)` | Loest setSel aus; kein Knopf in der Naehe ruft dasselbe. |
| App | `div` | ja | `()=>{markRead(n.id);/* v3.9.144: Notification-Klick navigiert — n.link` | Loest markRead, abgeleitet, Fahrzeuge aus; kein Knopf in der Naehe ruft dasselbe. |
| App | `div` | nein | `()=>{refreshPendingDetail();setShowSyncPanel(true);}` | Loest refreshPendingDetail, setShowSyncPanel aus; kein Knopf in der Naehe ruft dasselbe. |
| App | `div` | nein | `()=>{refreshPendingDetail();setShowSyncPanel(true);}` | Loest refreshPendingDetail, setShowSyncPanel aus; kein Knopf in der Naehe ruft dasselbe. |
| ArbeitsscheinView | `td` | nein | `()=>_openEditGuarded(a)` | Loest _openEditGuarded aus; kein Knopf in der Naehe ruft dasselbe. |
| ArbeitsscheinView | `td` | nein | `()=>_openEditGuarded(a)` | Loest _openEditGuarded aus; kein Knopf in der Naehe ruft dasselbe. |
| ArbeitsscheinView | `td` | nein | `()=>_openEditGuarded(a)` | Loest _openEditGuarded aus; kein Knopf in der Naehe ruft dasselbe. |
| ArbeitsscheinView | `div` | nein | `e=>{e.stopPropagation();openEdit(a);}` | Loest openEdit aus; kein Knopf in der Naehe ruft dasselbe. |
| ArbeitsscheinView | `div` | nein | `()=>{setCalDate(new Date(day));setCalView("tag");}` | Loest setCalDate, Date, setCalView aus; kein Knopf in der Naehe ruft dasselbe. |
| ArbeitsscheinView | `div` | nein | `()=>_openEditGuarded(a)` | Loest _openEditGuarded aus; kein Knopf in der Naehe ruft dasselbe. |
| ArbeitsscheinView | `div` | nein | `()=>_openEditGuarded(a)` | Loest _openEditGuarded aus; kein Knopf in der Naehe ruft dasselbe. |
| BauprovisorienView | `div` | nein | `()=>_kPick(hit)` | Loest _kPick aus; kein Knopf in der Naehe ruft dasselbe. |
| ChefDashboard | `div` | nein | `function(){const _pp=(projects\|\|[]).find(pr=>pr.id===x.pid);if(_pp&&` | Loest onOpenP, onNav, Tab aus; kein Knopf in der Naehe ruft dasselbe. |
| ChefDashboard | `tr` | nein | `function(){if(onOpenP)onOpenP(p.p);}` | Loest onOpenP aus; kein Knopf in der Naehe ruft dasselbe. |
| ChefDashboard | `div` | nein | `function(){window.__asFilter='alle';onNav('arbeitsscheine');}` | Loest onNav aus; kein Knopf in der Naehe ruft dasselbe. |
| DispoPanel | `div` | nein | `function(e){if(e&&e.stopPropagation)e.stopPropagation();}` | Loest eine Handlung aus; kein Knopf in der Naehe ruft dasselbe. |
| DispoPanel | `div` | nein | `function(){/* v3.9.718 P1-b: Wartelisten-Eintrag oeffnet den Schein; n` | Loest unterdrueckt, onOpenSchein aus; kein Knopf in der Naehe ruft dasselbe. |
| FahrtenbuchView | `div` | nein | `function(ev){try{ev.stopPropagation();}catch(_e){}}` | Loest eine Handlung aus; kein Knopf in der Naehe ruft dasselbe. |
| FahrtenbuchView | `div` | nein | `function(){_waehleFahrt(s);}` | Loest _waehleFahrt aus; kein Knopf in der Naehe ruft dasselbe. |
| FahrzeugView | `div` | nein | `()=>setSel(f.id)` | Loest setSel aus; kein Knopf in der Naehe ruft dasselbe. |
| FahrzeugView | `div` | ja | `()=>setSel(f.id)` | Loest setSel aus; kein Knopf in der Naehe ruft dasselbe. |
| FahrzeugView | `span` | nein | `()=>_delSvcDoc(i,d)` | Loest _delSvcDoc aus; kein Knopf in der Naehe ruft dasselbe. |
| FlotteView | `div` | ja | `function(){if(row.hatTracker)_focus(row);setBuchFid(row.f.id);}` | Loest _focus, setBuchFid aus; kein Knopf in der Naehe ruft dasselbe. |
| HomeView | `div` | nein | `()=>{ if(a.details&&a.details.length){ setAlertsExpanded(prev=>prev===` | Loest setAlertsExpanded aus; kein Knopf in der Naehe ruft dasselbe. |
| MitarbeiterView | `div` | nein | `()=>setSel(m.id)` | Loest setSel aus; kein Knopf in der Naehe ruft dasselbe. |
| MitarbeiterView | `div` | nein | `()=>{if(isWAdm)toggleProj(selM.id,p.id);}` | Loest toggleProj aus; kein Knopf in der Naehe ruft dasselbe. |
| PlanPin | `div` | nein | `e=>{e.stopPropagation();onClick(ticket);}` | Loest onClick aus; kein Knopf in der Naehe ruft dasselbe. |
| PlanThumbnail | `div` | nein | `{marginBottom: 8, cursor: "pointer", border: "2px solid " + (active ? ` | Loest eine Handlung aus; kein Knopf in der Naehe ruft dasselbe. |
| PlanViewerCanvas | `div` | nein | `(e)=>{e.stopPropagation();const _fx=pan.x+(_cx/100)*_pw*zoom, _fy=pan.` | Loest setZoom, setPan aus; kein Knopf in der Naehe ruft dasselbe. |
| StundenzettelView | `div` | nein | `()=>setFinkStatusFilter(finkStatusFilter===k.f?"alle":k.f)` | Loest setFinkStatusFilter aus; kein Knopf in der Naehe ruft dasselbe. |
| StundenzettelView | `span` | nein | `()=>setFinkStunden(z.id,0)` | Loest setFinkStunden aus; kein Knopf in der Naehe ruft dasselbe. |
| TicketListItem | `div` | nein | `()=>onClick(ticket)` | Loest onClick aus; kein Knopf in der Naehe ruft dasselbe. |
| VBueroExport | `div` | ja | `(e)=>e.stopPropagation()` | Loest eine Handlung aus; kein Knopf in der Naehe ruft dasselbe. |
| VBueroExport | `td` | nein | `()=>openMultiEntryEdit(w,ds,projId)` | Loest openMultiEntryEdit aus; kein Knopf in der Naehe ruft dasselbe. |
| VBueroExport | `tr` | nein | `function(){_setKrOpen(function(pp){var mm=Object.assign({},pp);if(mm[b` | Loest _setKrOpen aus; kein Knopf in der Naehe ruft dasselbe. |
| VDoku | `div` | nein | `e=>{e.stopPropagation();if(hasKids)toggleExpand(folder.id);}` | Loest toggleExpand aus; kein Knopf in der Naehe ruft dasselbe. |
| VDoku | `div` | ja | `()=>{setCurFolder(folder.id);if(isMob)setTreeOpen(false);}` | Loest setCurFolder, setTreeOpen aus; kein Knopf in der Naehe ruft dasselbe. |
| VDoku | `div` | nein | `()=>setShowUp(true)` | Loest setShowUp aus; kein Knopf in der Naehe ruft dasselbe. |
| VGefahrstoff | `div` | ja | `()=>openFile(fi)` | Loest openFile aus; kein Knopf in der Naehe ruft dasselbe. |
| VGefahrstoff | `span` | nein | `()=>jumpTo(-1)` | Loest jumpTo aus; kein Knopf in der Naehe ruft dasselbe. |
| VGefahrstoff | `span` | nein | `()=>jumpTo(c.i)` | Loest jumpTo aus; kein Knopf in der Naehe ruft dasselbe. |
| VGefahrstoff | `div` | ja | `()=>goInto(fo.id)` | Loest goInto aus; kein Knopf in der Naehe ruft dasselbe. |
| VMang | `div` | nein | `e=>{e.stopPropagation();setLightbox({src:ph,title:m.name+" — Foto "+(i` | Loest setLightbox aus; kein Knopf in der Naehe ruft dasselbe. |
| VMaterial | `div` | ja | `()=>setOrderDetail(isDetail?null:ord.id)` | Loest setOrderDetail aus; kein Knopf in der Naehe ruft dasselbe. |
| VPlan | `div` | nein | `()=>setSelTicket(null)` | Loest setSelTicket aus; kein Knopf in der Naehe ruft dasselbe. |
| VPlan | `div` | nein | `()=>setSelTicket(null)` | Loest setSelTicket aus; kein Knopf in der Naehe ruft dasselbe. |
| WeekPlan | `span` | nein | `()=>toggleMAMulti(r.id,pickDays,m.id)` | Loest toggleMAMulti aus; kein Knopf in der Naehe ruft dasselbe. |
| WeekPlan | `span` | nein | `()=>toggleMAMulti(r.id,pickDays,m.id)` | Loest toggleMAMulti aus; kein Knopf in der Naehe ruft dasselbe. |
| WeekPlan | `span` | nein | `(e)=>{e.stopPropagation();toggleMAWeek(r.id,m.id);}` | Loest toggleMAWeek aus; kein Knopf in der Naehe ruft dasselbe. |
| WeekPlan | `span` | nein | `()=>toggleFZMulti(r.id,pickDays,f.id)` | Loest toggleFZMulti aus; kein Knopf in der Naehe ruft dasselbe. |
| WeekPlan | `span` | nein | `()=>toggleFZMulti(r.id,pickDays,f.id)` | Loest toggleFZMulti aus; kein Knopf in der Naehe ruft dasselbe. |
| WeekPlan | `span` | nein | `(e)=>{e.stopPropagation();toggleFZWeek(r.id,f.id);}` | Loest toggleFZWeek aus; kein Knopf in der Naehe ruft dasselbe. |
| WeekPlan | `div` | nein | `isAdmin?()=>setCellPick({rowId:r.id,days:[d],type:'ma'}):undefined` | Loest setCellPick aus; kein Knopf in der Naehe ruft dasselbe. |
| WeekPlan | `div` | nein | `isAdmin?()=>setCellPick({rowId:r.id,days:['_bem'],type:'bem'}):undefin` | Loest setCellPick aus; kein Knopf in der Naehe ruft dasselbe. |
| WeekPlan | `th` | nein | `(isAdmin&&isTgt)?()=>_wpPasteDay(d):undefined` | Loest _wpPasteDay aus; kein Knopf in der Naehe ruft dasselbe. |
| WeekPlan | `span` | nein | `(e)=>{e.stopPropagation();if(isTgt)_wpPasteDay(d);else if(isSrc)setCop` | Loest _wpPasteDay, setCopySrcDay, _wpCopyDay aus; kein Knopf in der Naehe ruft dasselbe. |
| WeekPlan | `td` | nein | `()=>{if(isAdmin&&isEmpty&&editRow!==r.id){setEditRow(r.id);setEditBvh(` | Loest setEditRow, setEditBvh aus; kein Knopf in der Naehe ruft dasselbe. |
| WerkzeugView | `span` | nein | `onChange?()=>onChange(i):undefined` | Loest onChange aus; kein Knopf in der Naehe ruft dasselbe. |
| WerkzeugView | `div` | nein | `()=>{if(isAdmin)openEdit(w);}` | Loest openEdit aus; kein Knopf in der Naehe ruft dasselbe. |
| WorkerKompetenzenPanel | `span` | nein | `editable?e=>{e.stopPropagation();setLevel(key,lvl);}:null` | Loest setLevel aus; kein Knopf in der Naehe ruft dasselbe. |
| ZeiterfassungView | `div` | ja | `e=>e.stopPropagation()/* v3.9.416: Klicks im Panel schließen nicht */` | Loest eine Handlung aus; kein Knopf in der Naehe ruft dasselbe. |

## DOPPELWEG (35)

| Ansicht | Tag | eigener Knopf | `onClick` | Begruendung |
|---|---|---|---|---|
| ArbeitsscheinView | `div` | ja | `()=>setAsShowQR(null)` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setAsShowQR |
| ArbeitsscheinView | `div` | nein | `()=>{setCalDate(new Date(day));setCalView("tag");}` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setCalView |
| BauprovisorienView | `div` | ja | `()=>setQrShow(null)` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setQrShow |
| FahrzeugView | `div` | nein | `()=>_openFileUrl(selFz.zulassungsschein,"Zulassungsschein")` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: _openFileUrl |
| FahrzeugView | `div` | nein | `()=>{const m=monteure.find(x=>x.n===bh.fahrer);setBeschForm({fahrer:bh` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setShowBesch |
| HomeView | `div` | ja | `()=>onOpenP(pr)` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: onOpenP |
| KundenPortal | `div` | nein | `e=>{e.stopPropagation();_openFileUrl(ph);}` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: _openFileUrl |
| PZEView | `div` | ja | `()=>setKorr(null)` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setKorr |
| StundenzettelView | `div` | ja | `()=>{setSigZettel(null);setSigData(null);}` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setSigData, setSigZettel |
| StundenzettelView | `div` | ja | `()=>setViewPdf(null)` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setViewPdf |
| VBueroExport | `div` | ja | `()=>{setSelProj(ps.id);if(ps.cnt)_toggleBWB(ps.id);}/* v3.9.360: Klick` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: _toggleBWB |
| VBueroExport | `div` | ja | `()=>_setTankFotoView(null)` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: _setTankFotoView |
| VCheck | `div` | ja | `()=>setSel(c.id)` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setSel |
| VDash | `div` | nein | `()=>{if(setView)setView("fotos");}` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setView |
| VDoku | `div` | ja | `()=>openDoc(d)` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: openDoc |
| VForm | `div` | nein | `()=>{setFTab(t.id);setShowAll(false);setSearch("");}` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setFTab, setSearch, setShowAll |
| VForm | `div` | nein | `()=>{setFTab(f._type);setShowAll(false);setSearch("");}` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setFTab, setSearch, setShowAll |
| VMang | `div` | nein | `()=>setLightbox({src:ph,title:m.name+" — Foto "+(i+1)})` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setLightbox |
| VMaterial | `div` | nein | `()=>setDnAutoEnabled(prev=>{const s=new Set(prev);if(s.has(g.id))s.del` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: Set, setDnAutoEnabled |
| VMaterial | `div` | nein | `()=>{setDnSelected(prev=>{const s=new Set(prev);if(s.has(a.artNr))s.de` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: Set |
| VPlan | `tr` | ja | `()=>{setSelTicket(t);setSelPlan(plans.find(x=>x.id===t.planId)\|\|null` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setSideMode |
| VPlan | `div` | ja | `()=>{setSelTicket(t);setSelPlan(plans.find(x=>x.id===t.planId)\|\|null` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setSubView |
| VPlan | `div` | nein | `()=>toggleLayer(l.id)` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: toggleLayer |
| VPlan | `div` | nein | `()=>_optionalChain([fileRef, 'access', _417 => _417.current, 'optional` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: _optionalChain |
| VPlan | `div` | ja | `()=>{setSelPlan(pl);setSubView("viewer");}` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setSelPlan, setSubView |
| VPlan | `div` | ja | `()=>setTplEdit(null)` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setTplEdit |
| VZeit | `span` | nein | `function(){setEditEntryId(entry.id);setAddWorker(entry.worker\|\|entry` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setAddBemerkung, setAddBis, setAddDay |
| WeekPlan | `td` | nein | `e=>{e.stopPropagation();if(isMob&&isAdmin){setCellPick(isPickCell?null` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setCellPick |
| WeekPlan | `div` | ja | `()=>{if(cellPick)setCellPick(null);setSelCells(null);}` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setCellPick, setSelCells |
| WeekPlan | `div` | ja | `()=>{setCellPick(null);setSelCells(null);}` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setCellPick, setSelCells |
| WerkzeugView | `tr` | ja | `()=>{if(isAdmin)openEdit(w);}` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: openEdit |
| WerkzeugView | `span` | nein | `()=>{setWerkzeuge(p=>p.map(w=>w.id===wzServiceSel?{...w,serviceheft:(w` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: _pushWzSh, setWerkzeuge |
| WerkzeugView | `span` | nein | `()=>{setWerkzeuge(p=>p.map(w=>w.id===wzServiceSel?{...w,serviceheft:(w` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: _pushWzSh, setWerkzeuge |
| ZeiterfassungView | `div` | ja | `()=>{setAddDay(null);setEditEntry(null);}/* v3.9.416: Tap-outside schl` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setAddDay, setEditEntry |
| ZeiterfassungView | `tr` | nein | `()=>{setSelWorker(m.id);setViewAll(false);}` | Ein echter Knopf in der Naehe ruft dieselbe Funktion: setViewAll |

## UNSICHER (5)

| Ansicht | Tag | eigener Knopf | `onClick` | Begruendung |
|---|---|---|---|---|
| App | `div` | nein | `r.action` | Der Behandler ist eine undurchsichtige Angabe ('r.action') - am Quelltext nicht entscheidbar. Unveraendert gelassen. |
| DispoPanel | `div` | nein | `o.open` | Der Behandler ist eine undurchsichtige Angabe ('o.open') - am Quelltext nicht entscheidbar. Unveraendert gelassen. |
| PdfViewerModal | `div` | ja | `onClose` | Der Behandler ist eine undurchsichtige Angabe ('onClose') - am Quelltext nicht entscheidbar. Unveraendert gelassen. |
| PlanViewer | `div` | nein | `handlePlanClick` | Der Behandler ist eine undurchsichtige Angabe ('handlePlanClick') - am Quelltext nicht entscheidbar. Unveraendert gelassen. |
| QuickEditPin | `div` | ja | `onClose` | Der Behandler ist eine undurchsichtige Angabe ('onClose') - am Quelltext nicht entscheidbar. Unveraendert gelassen. |

## KEIN ELEMENT (2)

| Ansicht | Tag | eigener Knopf | `onClick` | Begruendung |
|---|---|---|---|---|
| App | `div` | ja | `e=>{if(e.target===e.currentTarget)onClose();}` | Hintergrundflaeche eines Dialogs (e.target===e.currentTarget). Der Dialog hat einen eigenen Schliessen-Knopf; ein role=button auf einer bildschirmfuel |
| VMaterial | `div` | ja | `e=>{if(e.target===e.currentTarget)setFlexPopup(null);}` | Hintergrundflaeche eines Dialogs (e.target===e.currentTarget). Der Dialog hat einen eigenen Schliessen-Knopf; ein role=button auf einer bildschirmfuel |

## Was mit den zehn "eigener Knopf: ja" passieren muss

Zehn der BEDIENELEMENTE enthalten **selbst einen Knopf**. Sie duerfen **kein**
`role="button"` bekommen: ein Knopf in einem Knopf ist ungueltiges ARIA, und
eine Vorlesehilfe liest dann Unsinn. Fuer sie ist `tabIndex` plus
Tastenbehandler **ohne** `role` die richtige Form - so ist es am 27.09.2026 in
`ProjList` gebaut worden.

Sie brauchen ausserdem eine eigene Fokusring-Regel: die vorhandene greift auf
`[role="button"]:focus-visible`, und ohne `role` greift sie nicht. Das ist eine
Zeile CSS, aber sie fehlt heute - und ein Tab-Stopp ohne sichtbaren Ring ist
fuer einen sehenden Tastaturnutzer wertlos.
