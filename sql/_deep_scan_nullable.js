const fs=require('fs');
const s=fs.readFileSync('index.html','utf8');
const lines=s.split(/\r?\n/);
const hits=[];
for(let i=0;i<lines.length;i++){
  const ln=lines[i];
  const m=ln.match(/const\s+(\w+)\s*=\s*await\s+_sb(Get|Post|GetOrder|Upsert)\(/);
  if(!m)continue;
  const varname=m[1];
  const nextLines=lines.slice(i+1,Math.min(lines.length,i+3)).join('\n');
  const mapRe=new RegExp('(?<!\\w)'+varname+'\\.(map|filter|forEach|reduce)');
  if(mapRe.test(nextLines)){
    const guardRe=new RegExp('if\\s*\\(\\s*!?'+varname+'|'+varname+'\\?\\.');
    if(!guardRe.test(nextLines)){
      hits.push({line:i+1,var:varname,first:ln.trim().substring(0,100),next:nextLines.trim().substring(0,100)});
    }
  }
}
console.log('hits:',hits.length);
hits.slice(0,15).forEach(h=>console.log('L'+h.line+' '+h.var+': '+h.first+' | '+h.next));
