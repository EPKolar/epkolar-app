/* Mutationsprobe: benennt EINE aufgeloeste Variablen-Referenz in eine
   garantiert freie um und prueft, ob der Scanner sie meldet.
   Findet er sie nicht, misst er an dieser Stelle NICHTS. */
const fs=require('fs'), path=require('path');
/* mitversionierte Pakete, absolut - nie ein fremdes node_modules von oberhalb */
const _V=p=>require(path.join(__dirname,'node_modules',p));
const espree=_V('espree'), escope=_V('eslint-scope');
const {execFileSync}=require('child_process');
const QUELLE=process.argv[2], N=parseInt(process.argv[3]||'25',10);
const raw=fs.readFileSync(QUELLE,'utf8');
const re=/<script([^>]*)>/gi; let m; const blks=[];
while((m=re.exec(raw))){const a=m[1],s=m.index+m[0].length,e=raw.indexOf('</script>',s);re.lastIndex=e+9;if(/\bsrc\s*=/i.test(a))continue;blks.push({s,e,code:raw.slice(s,e)});}

/* alle AUFGELOESTEN Lese-Referenzen einsammeln (absolute Offsets) */
const kand=[];
for(const b of blks){
  const ast=espree.parse(b.code,{ecmaVersion:'latest',sourceType:'script',range:true});
  const sm=escope.analyze(ast,{ecmaVersion:2025,sourceType:'script',fallback:'iteration'});
  (function go(sc){
    for(const r of sc.references){
      if(!r.resolved) continue;
      if(r.resolved.scope.type==='global'||r.resolved.scope.type==='module') continue; // globale nicht mutieren
      if(!r.isRead()) continue;
      const id=r.identifier;
      /* `typeof X` auf einen undeklarierten Namen ist LEGAL und wirft NICHT.
         So eine Stelle ist nicht mutierbar - der Scanner hat recht, wenn er
         schweigt.  Ohne diese Ausnahme misst die Probe den Scanner falsch
         (Stand 2026-08-30: genau ein solcher Schein-Miss bei 40 Mutationen). */
      if(/\btypeof\s*$/.test(b.code.slice(Math.max(0,id.range[0]-16), id.range[0]))) continue;
      kand.push({off:b.s+id.range[0], len:id.range[1]-id.range[0], name:id.name, tiefe:sc.type});
    }
    sc.childScopes.forEach(go);
  })(sm.globalScope);
}
console.log('aufgeloeste lokale Lese-Referenzen insgesamt: '+kand.length);
/* deterministisch streuen */
const schritt=Math.max(1,Math.floor(kand.length/N));
const tmp=path.join(__dirname,'_mut.html');
let ok=0, miss=0; const fehl=[];
const zeilenAnfang=[0]; for(let i=0;i<raw.length;i++) if(raw[i]==='\n') zeilenAnfang.push(i+1);
const zeile=o=>{let lo=0,hi=zeilenAnfang.length-1;while(lo<hi){const mid=(lo+hi+1)>>1;if(zeilenAnfang[mid]<=o)lo=mid;else hi=mid-1;}return lo+1;};
for(let i=0;i<N;i++){
  const k=kand[(i*schritt)%kand.length]; if(!k)continue;
  const marke='zZfrei'+i+'Q';
  const mutiert=raw.slice(0,k.off)+marke+raw.slice(k.off+k.len);
  fs.writeFileSync(tmp,mutiert,'utf8');
  let namen=[];
  try{ execFileSync(process.execPath,[path.join(__dirname,'freivar.js'),tmp,'--json'],{encoding:'utf8'}); }
  catch(e){ try{ namen=JSON.parse((e.stdout||'[]')).map(t=>t.name); }catch(_){ namen=['<CRASH>']; } }
  if(namen.includes(marke)) ok++; else { miss++; fehl.push(k.name+' @Zeile '+zeile(k.off)+' (Scope '+k.tiefe+') -> gemeldet: '+namen.join(',')); }
}
try{fs.unlinkSync(tmp);}catch(e){}
console.log('Mutationen erkannt: '+ok+'/'+(ok+miss));
fehl.forEach(x=>console.log('  NICHT ERKANNT: '+x));
process.exit(miss?1:0);
