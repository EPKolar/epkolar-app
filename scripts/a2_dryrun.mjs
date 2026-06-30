// A-2 Dry-Run — repliziert die exakten Maps + die GEFIXTE _juprowaReversMap-Status-Logik (index.html:3307).
// Kein OFFA-Kontakt. Beweist: gepullter Code C -> push C (Roundtrip-stabil) + echte Aenderung -> Reverse.
// Lauf: node scripts/a2_dryrun.mjs
const JUPROWA_STATUS_MAP={'0':'aufgenommen','1':'freigegeben','2':'aufgeschoben','3':'in_bearbeitung','4':'freigegeben','5':'erledigt','10':'abgerechnet','11':'bar_bezahlt','15':'bar_bezahlt','20':'storniert'};
const JUPROWA_STATUS_REV={aufgenommen:'0',freigegeben:'1',in_bearbeitung:'3',aufgeschoben:'2',erledigt:'5',abgerechnet:'10',bar_bezahlt:'11',storniert:'20'};

// === exakt die neue Builder-Logik aus index.html:3307 ===
function pushAufstatus(scheinstatus, juprowa_raw){
  if(scheinstatus && JUPROWA_STATUS_REV[scheinstatus]!=null){
    const _rawSt=(juprowa_raw && typeof juprowa_raw==='object' && juprowa_raw.AK_AUFSTATUS!=null)?String(juprowa_raw.AK_AUFSTATUS):null;
    return (_rawSt!=null && JUPROWA_STATUS_MAP[_rawSt]===scheinstatus)?_rawSt:JUPROWA_STATUS_REV[scheinstatus];
  }
  return undefined; // wird nicht gesendet
}
function pushAufstatusOLD(scheinstatus){
  return (scheinstatus && JUPROWA_STATUS_REV[scheinstatus]!=null)?JUPROWA_STATUS_REV[scheinstatus]:undefined;
}

const codes=['0','1','2','3','4','5','10','11','15','20'];
console.log('=== ROUNDTRIP (gepullter Code -> App-Status -> Push unveraendert) ===');
console.log('CODE | App-Status      | OLD push | NEW push | stabil?');
let allStable=true;
for(const c of codes){
  const app=JUPROWA_STATUS_MAP[c];
  const oldP=pushAufstatusOLD(app);
  const newP=pushAufstatus(app, {AK_AUFSTATUS:c});
  const stable=newP===c;
  if(!stable)allStable=false;
  console.log(c.padStart(4),'|',String(app).padEnd(15),'|',String(oldP).padStart(8),'|',String(newP).padStart(8),'|',stable?'YES':'*** NO ***');
}
console.log('\n=== Injektiver Roundtrip ueber alle 10 Codes:', allStable?'BESTANDEN':'FEHLGESCHLAGEN','===');
if(!allStable)process.exitCode=1;

console.log('\n=== ECHTE User-Aenderung (kein passender Roh-Status) -> Reverse korrekt ===');
console.log('raw=4(freigegeben), User setzt erledigt  -> NEW push:', pushAufstatus('erledigt',{AK_AUFSTATUS:'4'}), '(erwartet 5)');
console.log('raw=15(bar_bezahlt), User setzt storniert -> NEW push:', pushAufstatus('storniert',{AK_AUFSTATUS:'15'}),'(erwartet 20)');
console.log('\n=== Fallback ohne juprowa_raw -> Reverse (Alt-Verhalten) ===');
console.log('raw=null, status freigegeben -> NEW push:', pushAufstatus('freigegeben',null), '(erwartet 1)');

console.log('\n=== Kontrast: ALTE Logik bei 4/15 (Bug) ===');
console.log('Code 4 (freigegeben): OLD ->', pushAufstatusOLD('freigegeben'), '(KORRUPT: 4 wurde 1)');
console.log('Code 15 (bar_bezahlt): OLD ->', pushAufstatusOLD('bar_bezahlt'), '(KORRUPT: 15 wurde 11)');
