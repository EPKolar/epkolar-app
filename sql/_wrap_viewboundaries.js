// v3.5.193 BLOCK 8: Wrap Haupt-Tab-Views in _ViewBoundary
// Pattern: tabs[safeKat].perm==="X" && [extra-checks &&] React.createElement(Component, {props})
// Transform: → tabs[safeKat].perm==="X" && [extras &&] React.createElement(_ViewBoundary, {name:"X"}, React.createElement(Component, {props}))
//
// Arg: --write → applies + saves
const fs=require('fs');
const write=process.argv.includes('--write');

const src=fs.readFileSync('index.html','utf8');
const lines=src.split(/\r?\n/);

// Find lines with "tabs[...].perm===\"XXX\" && ... React.createElement(NAME, {" pattern
// where NAME is capitalized (not _ViewBoundary, not already-wrapped)
const tabRe=/(tabs[^)]+\.perm\s*\)?\s*=>\s*_?\d+[a-z]?\.perm\])?\s*===\s*"([a-zA-Z_]+)"/;
// Simpler: find '.perm])==="XXX"'
const permRe=/\.perm\]\)===\s*"([a-zA-Z_]+)"/;

let modified=false;
const newLines=lines.map((ln,idx)=>{
  const pm=permRe.exec(ln);
  if(!pm)return ln;
  const permName=pm[1];
  // Find React.createElement(Capitalized, ...) in this line AFTER the perm-check
  // Skip if already wrapped
  if(ln.includes('React.createElement(_ViewBoundary'))return ln;
  // Find the React.createElement(NAME, {...}) to wrap
  // NAME must be a capital-starting Component (not a DOM tag like 'div')
  // Pattern: React.createElement([A-Z]\w*, {
  const ceRe=/React\.createElement\(([A-Z]\w+),\s*\{/g;
  const matches=[];
  let m;
  while((m=ceRe.exec(ln)))matches.push({start:m.index,compName:m[1]});
  if(matches.length===0)return ln;
  // Take the LAST match (the outermost component render for this conditional)
  // Actually the FIRST capitalized React.createElement after the perm-check position is the right one
  const permEnd=pm.index+pm[0].length;
  const target=matches.find(m=>m.start>=permEnd);
  if(!target)return ln;
  // Find the matching ')' of this React.createElement call
  let depth=0,i=target.start,str=null,esc=false;
  while(i<ln.length){
    const c=ln[i];
    if(str){if(esc){esc=false;}else if(c==='\\'){esc=true;}else if(c===str){str=null;}i++;continue;}
    if(c==='"'||c==="'"||c==='`'){str=c;i++;continue;}
    if(c==='('){depth++;i++;continue;}
    if(c===')'){depth--;i++;if(depth===0)break;continue;}
    i++;
  }
  const endIdx=i; // after matching ')'
  const original=ln.substring(target.start,endIdx);
  const wrapped='React.createElement(_ViewBoundary,{name:"'+permName+'"},'+original+')';
  modified=true;
  return ln.substring(0,target.start)+wrapped+ln.substring(endIdx);
});

const out=newLines.join('\n');
const wrapCount=(out.match(/React\.createElement\(_ViewBoundary/g)||[]).length;
console.error('_ViewBoundary wraps in output: '+wrapCount);

if(write&&modified){
  fs.writeFileSync('index.html',out,'utf8');
  console.error('Applied, file written.');
} else if(!modified){
  console.error('No changes needed.');
}
