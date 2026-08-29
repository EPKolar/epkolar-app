/* RIEGEL v3.9.908 - Zeitfenster. Misst die EIGENSCHAFT, nicht den Wortlaut.
   Aufruf: node riegel_fenster.js <pfad-zu-index.html>   Exit 0 = gruen, 1 = rot. */
process.env.TZ='Europe/Vienna';
const fs=require('fs');
const datei=process.argv[2]||'C:/repos/epkolar-app/index.html';
const S=fs.readFileSync(datei,'utf8');
let rot=0; const sag=(ok,name,txt)=>{if(!ok)rot++;console.log((ok?'  gruen  ':'  ROT    ')+name+'   '+txt);};

/* Ausdruck ab Position i bis zum ; auf Tiefe 0 herausschneiden */
function ausdruck(i){let d=0;for(let k=i;k<S.length;k++){const c=S[k];
  if(c==='('||c==='{'||c==='[')d++; else if(c===')'||c==='}'||c===']')d--;
  else if(c===';'&&d===0)return S.slice(i,k);} return null;}
function funde(nadel){const o=[];let i=-1;while((i=S.indexOf(nadel,i+1))>=0)o.push(i);return o;}
const _p=n=>String(n).padStart(2,'0');
const _ymd=d=>d.getFullYear()+'-'+_p(d.getMonth()+1)+'-'+_p(d.getDate());

/* ---- R1  _antragWerktage: Anzeige MUSS mit der Materialisierung uebereinstimmen ---- */
(()=>{
 const i=S.indexOf('const _antragWerktage=');
 if(i<0)return sag(false,'R1 _antragWerktage','Ausdruck nicht gefunden');
 const q=ausdruck(i+'const '.length);
 const _stdVonTagBrk=d=>{const w=d.getDay();return (w===0||w===6)?0:8;};
 const f=new Function('_stdVonTagBrk','return ('+q.slice(q.indexOf('=')+1)+');')(_stdVonTagBrk);
 /* Gegenstueck: die ortsrichtige Schleife aus _materialisiereAbsence */
 const soll=(von,bis)=>{const a=new Date(von+'T00:00:00'),b=new Date(bis+'T00:00:00');let n=0;
   for(let d=new Date(a);d<=b;d.setDate(d.getDate()+1))if(_stdVonTagBrk(d)>0)n++;return n;};
 const F=[['2026-10-19','2026-10-30'],['2025-10-20','2025-10-31'],['2027-10-25','2027-11-05'],
          ['2026-10-24','2026-10-26'],['2026-03-23','2026-04-03'],['2024-02-26','2024-03-01']];
 let schlecht=[];
 for(const [v,b] of F){const a=f(v,b),s=soll(v,b);if(a!==s)schlecht.push(v+'..'+b+': Anzeige '+a+' vs. gebucht '+s);}
 sag(schlecht.length===0,'R1 _antragWerktage','Anzeige = Materialisierung ueber die Zeitumstellung'+(schlecht.length?('  ['+schlecht.join(' | ')+']'):''));
})();

/* ---- R2/R3  toIso: Fensterende MUSS die Ortsmitternacht des Folgetags sein ---- */
(()=>{
 const st=funde('toIso=');
 if(st.length!==2)return sag(false,'R2/R3 toIso','erwartet 2 Fundstellen, gefunden '+st.length);
 const F=['2026-10-25','2025-10-26','2027-10-31','2026-03-29','2024-03-31','2026-10-31','2026-02-28','2024-02-29'];
 st.forEach((i,nr)=>{
  const q=ausdruck(i+'toIso='.length);
  let schlecht=[];
  for(const bis of F){
   const got=new Function('bis','TIME_DAY','return ('+q+');')(bis,86400000);
   const soll=(()=>{const d=new Date(bis+'T00:00:00');d.setDate(d.getDate()+1);return d.toISOString();})();
   if(got!==soll)schlecht.push(bis+': '+got+' statt '+soll);
  }
  sag(schlecht.length===0,'R'+(nr+2)+' toIso #'+(nr+1),'Fensterende = Ortsmitternacht des Folgetags'+(schlecht.length?('  ['+schlecht.join(' | ')+']'):''));
 });
})();

/* ---- R4  Bautagebuch-Wochenkachel MUSS eine Obergrenze haben ---- */
(()=>{
 const i=S.indexOf('"select=id&datum=gte."+weekStart');
 if(i<0)return sag(false,'R4 Bautagebuch','Abfrage nicht gefunden');
 let d=0,ende=-1;
 for(let k=i;k<S.length;k++){const c=S[k];
   if(c==='('||c==='{'||c==='[')d++;
   else if(c===')'||c==='}'||c===']'){if(d===0){ende=k;break;}d--;}
   else if(c===','&&d===0){ende=k;break;}}
 const q=S.slice(i,ende);
 const s=new Function('weekStart','_ymd','return ('+q+');')('2026-08-31',_ymd);
 const hatUnten=/datum=gte\.2026-08-31/.test(s);
 const hatOben=/datum=lt\.2026-09-07/.test(s);
 sag(hatUnten&&hatOben,'R4 Bautagebuch','Fenster halboffen Mo..<Mo+7   erzeugt: '+s);
})();

/* ---- R5  Chef-Portal: Ueberfaelligkeit in Tagen darf im Sommerhalbjahr nicht um 1 danebenliegen ---- */
(()=>{
 /* NICHT die erste Fundstelle nehmen: es gibt zwei _dOver, die andere haengt an now=Date.now() */
 const kopf='const _today=_td;const _dOver=';
 const i=S.indexOf(kopf);
 if(i<0)return sag(false,'R5 _dOver','Ausdruck nicht gefunden');
 if(S.indexOf(kopf,i+1)>=0)return sag(false,'R5 _dOver','Anker nicht mehr eindeutig');
 const q=ausdruck(i+kopf.length);
 const F=[['2026-03-30','2026-03-29'],['2026-06-01','2026-03-20'],['2026-04-15','2026-03-28'],
          ['2026-10-26','2026-10-25'],['2026-12-01','2026-10-20'],['2027-01-15','2026-03-01']];
 let schlecht=[];
 for(const [t,d] of F){
  const f=new Function('_today','TIME_DAY','return ('+q+');')(t,86400000);
  const soll=Math.round((new Date(t+'T12:00:00')-new Date(d+'T12:00:00'))/86400000);
  const got=f(d);
  if(got!==soll)schlecht.push('heute '+t+' Frist '+d+': '+got+' statt '+soll);
 }
 sag(schlecht.length===0,'R5 _dOver','Tage ueber Frist sommerzeitfest'+(schlecht.length?('  ['+schlecht.join(' | ')+']'):''));
})();

console.log(rot?('\nROT: '+rot+' Riegel gerissen'):'\nGRUEN: alle Riegel halten');
process.exit(rot?1:0);
