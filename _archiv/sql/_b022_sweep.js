// v3.5.182-188 B-022 Full-Sweep Script
// Scans index.html, finds setX({...x,...}) where setter-Name matches state-Var,
// rewrites to functional setX(p=>({...p,...})).
// String/template-literal-aware brace matching.
//
// Usage: node sql/_b022_sweep.js              → dry-run, prints candidates
//        node sql/_b022_sweep.js --write      → apply + write file
//        node sql/_b022_sweep.js --chunk N M  → apply ONLY hits N..M (inclusive, 1-indexed)

const fs=require('fs');
const args=process.argv.slice(2);
const write=args.includes('--write');
const chunkI=args.indexOf('--chunk');
const chunkRange=chunkI>=0?{from:parseInt(args[chunkI+1]),to:parseInt(args[chunkI+2])}:null;

const src=fs.readFileSync('index.html','utf8');

// Find matches: set<Setter>({ ... <stateVar> , ...
// where stateVar = Setter.charAt(0).toLowerCase()+Setter.slice(1)
const re=/set([A-Z][a-zA-Z0-9]*)\(\s*\{\s*\.\.\.([a-z][a-zA-Z0-9]*)\s*,/g;

function findCallClose(s, openParenIdx){
  // s[openParenIdx] must be '('
  let d=0, i=openParenIdx;
  let str=null, esc=false;
  while(i<s.length){
    const c=s[i];
    if(str){
      if(esc){esc=false;i++;continue;}
      if(c==='\\'){esc=true;i++;continue;}
      if(c===str){str=null;i++;continue;}
      i++;continue;
    }
    if(c==='"'||c==="'"||c==='`'){str=c;i++;continue;}
    if(c==='/'){
      // skip regex and line-comments — for safety skip // comments
      if(s[i+1]==='/'){while(i<s.length&&s[i]!=='\n')i++;continue;}
      if(s[i+1]==='*'){i+=2;while(i<s.length-1&&!(s[i]==='*'&&s[i+1]==='/'))i++;i+=2;continue;}
    }
    if(c==='('){d++;i++;continue;}
    if(c===')'){d--;i++;if(d===0)return i-1;continue;}
    i++;
  }
  return -1;
}

const hits=[];
let m;
while((m=re.exec(src))){
  const setter=m[1];
  const stateVar=m[2];
  const expected=setter.charAt(0).toLowerCase()+setter.slice(1);
  if(stateVar!==expected)continue;
  // m.index points to start of 'setX'
  const setStart=m.index;
  const openParenIdx=src.indexOf('(',setStart);
  if(openParenIdx<0)continue;
  const closeParenIdx=findCallClose(src,openParenIdx);
  if(closeParenIdx<0)continue;
  const commaAfterSpreadIdx=m.index+m[0].length; // position right after ','
  // The inner body is from commaAfterSpreadIdx to the '}' before ')'
  // Find '}' immediately before closeParenIdx (skipping whitespace)
  let j=closeParenIdx-1;
  while(j>0 && /\s/.test(src[j]))j--;
  if(src[j]!=='}'){continue;} // unexpected shape — skip
  const closeBraceIdx=j;
  const innerBody=src.substring(commaAfterSpreadIdx,closeBraceIdx);
  const lineNo=src.substring(0,setStart).split(/\r?\n/).length;
  hits.push({
    lineNo, setter, stateVar,
    setStart, closeParenIdx, innerBody,
    original:src.substring(setStart,closeParenIdx+1)
  });
}

console.error('Found '+hits.length+' candidates');
if(chunkRange){
  console.error('Chunk-Range: '+chunkRange.from+'..'+chunkRange.to+' ('+(chunkRange.to-chunkRange.from+1)+' hits)');
}

// Apply (right-to-left to preserve indices)
const toApply=chunkRange
  ? hits.slice(chunkRange.from-1, chunkRange.to)
  : hits;

const sortedApply=[...toApply].sort((a,b)=>b.setStart-a.setStart);

let out=src;
for(const h of sortedApply){
  const replacement='set'+h.setter+'(p=>({...p,'+h.innerBody+'}))';
  out=out.substring(0,h.setStart)+replacement+out.substring(h.closeParenIdx+1);
}

if(write){
  fs.writeFileSync('index.html',out,'utf8');
  console.error('Applied '+toApply.length+' replacements, wrote index.html');
} else {
  // Show first 10 hits
  hits.slice(0,10).forEach((h,i)=>{
    console.error('  #'+(i+1)+' L'+h.lineNo+' '+h.setter+': '+h.original.substring(0,120).replace(/\n/g,'\\n'));
  });
}
