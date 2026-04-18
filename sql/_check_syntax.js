// Helper: node sql/_check_syntax.js — exits 0 if main script is valid JS
const fs=require('fs'),path=require('path'),os=require('os'),cp=require('child_process');
const s=fs.readFileSync('index.html','utf8');
const lines=s.split(/\r?\n/);
// Find line index of last '<script>\n' (the main script opener at ~line 274)
// More robust: find lines that are exactly '<script>' (trimmed)
const opens=[]; const closes=[];
for(let i=0;i<lines.length;i++){
  const t=lines[i].trim();
  if(t==='<script>') opens.push(i);
  if(t==='</script>'||t==='</script></body></html>') closes.push(i);
}
// Main script is the last open that has a close after it. Actually: opens are 11,244,273 (0-idx); main script starts at idx 273 (line 274).
// The intervening '<script>' at line 4550 is inside a template literal, so we just pick the last real open that is NOT inside a string.
// Heuristic: take opens[2] (the 3rd real script open, index 273) as main.
let mainOpen=-1;
if(opens.length>=3) mainOpen=opens[2];
else mainOpen=opens[opens.length-1];
const mainClose=closes[closes.length-1];
if(mainOpen<0||mainClose<0){console.error('cannot find main script boundaries');process.exit(1)}
const body=lines.slice(mainOpen+1,mainClose).join('\n');
const tmp=path.join(os.tmpdir(),'main_syntax_check.js');
fs.writeFileSync(tmp,body,'utf8');
try{cp.execSync('node --check "'+tmp+'"',{stdio:'inherit'});console.log('syntax OK');}
catch(e){process.exit(1)}
finally{try{fs.unlinkSync(tmp);}catch(_){}}
