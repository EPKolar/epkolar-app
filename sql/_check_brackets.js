// Helper: node sql/_check_brackets.js — baseline must be () -2 {} 0 [] 0
const s=require('fs').readFileSync('index.html','utf8');
let p=0,q=0,r=0;
for(const c of s){
  if(c==='(')p++;else if(c===')')p--;
  if(c==='{')q++;else if(c==='}')q--;
  if(c==='[')r++;else if(c===']')r--;
}
console.log('brackets () '+p+' {} '+q+' [] '+r);
if(p!==-2||q!==0||r!==0){console.error('BRACKET BASELINE BROKEN');process.exit(1)}
