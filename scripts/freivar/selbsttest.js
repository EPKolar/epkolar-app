/* Misst den Scanner an beiden Richtungen je Sprachkonstrukt. */
const {execFileSync}=require('child_process'); const fs=require('fs'), os=require('os'), path=require('path');
const tmp=path.join(require('os').tmpdir(),'_freivar_selbsttest.html');
function lauf(js){
  fs.writeFileSync(tmp,'<html><body><script>\n'+js+'\n</'+'script></body></html>','utf8');
  try{ execFileSync(process.execPath,[path.join(__dirname,'freivar.js'),tmp,'--json'],{encoding:'utf8'}); return []; }
  catch(e){ const o=(e.stdout||'').trim(); if(!o){ console.log('CRASH:',e.message); return ['<CRASH>']; }
    return JSON.parse(o).map(t=>t.name); }
}
const ZU='</'+'script>', AUF='<scr'+'ipt>';
const faelle=[
 // [Name, Quelltext, erwartete freie Namen]
 ['Pfeilfunktion gebunden',      'var g=[1].map(x=>x+1);window.g=g;', []],
 ['Pfeilfunktion FREI',          'var g=[1].map(x=>y+1);window.g=g;', ['y']],
 ['Pfeil mehrere Parameter',     'var g=[1].reduce((a,b)=>a+b,0);window.g=g;', []],
 ['Pfeil mehrere Param FREI',    'var g=[1].reduce((a,b)=>a+c,0);window.g=g;', ['c']],
 ['Objekt-Methodenkurzform',     'var o={foo(a){return a*2;}};window.o=o;', []],
 ['Objekt-Methodenkurzform FREI','var o={foo(a){return a*zz;}};window.o=o;', ['zz']],
 ['Klasse',                      'class K{constructor(a){this.a=a;} m(b){return this.a+b;}} window.K=K;', []],
 ['Klasse FREI',                 'class K{constructor(a){this.a=a;} m(b){return this.a+qq;}} window.K=K;', ['qq']],
 ['Destrukturierung Parameter',  'function f({a,b:[c],...r}){return a+c+r.z;} window.f=f;', []],
 ['Destrukt. Param FREI',        'function f({a,b:[c]}){return a+c+dd;} window.f=f;', ['dd']],
 ['Vorgabewert im Parameter',    'function f(a,b=a+1){return b;} window.f=f;', []],
 ['Vorgabewert FREI',            'function f(a,b=ee+1){return b;} window.f=f;', ['ee']],
 ['catch-Bindung',               'try{null.x;}catch(e){console.log(e.message);}', []],
 ['catch-Bindung FREI',          'try{null.x;}catch(e){console.log(ff.message);}', ['ff']],
 ['for...of-Bindung',            'for(const it of [1,2]){console.log(it);}', []],
 ['for...of FREI',               'for(const it of [1,2]){console.log(gg);}', ['gg']],
 ['for...in-Bindung',            'for(var k in {a:1}){console.log(k);}', []],
 ['Template-Literal gebunden',   'var n=1;window.s=`x${n}y`;', []],
 ['Template-Literal FREI',       'window.s=`x${hh}y`;', ['hh']],
 ['getaggtes Template FREI',     'function tg(){} window.s=tg`a${ii}b`;', ['ii']],
 ['Getter/Setter Kurzform',      'var o={get v(){return 1;},set v(x){this._v=x;}};window.o=o;', []],
 ['Getter FREI',                 'var o={get v(){return jj;}};window.o=o;', ['jj']],
 ['benannter Funktionsausdruck', 'window.f=function rec(n){return n?rec(n-1):0;};', []],
 ['Generator + yield',           'function* g(){var a=1;yield a;} window.g=g;', []],
 ['async/await',                 'async function f(){var r=await Promise.resolve(1);return r;} window.f=f;', []],
 ['async/await FREI',            'async function f(){var r=await kk();return r;} window.f=f;', ['kk']],
 ['Eigenschaftsname != Variable', 'var o={f:1,map:2,length:3};window.o=o.f+o.map;', []],
 ['Kurzform-Eigenschaft FREI',   'var q=1;window.o={q,ll};', ['ll']],
 ['Label ist keine Variable',    'aussen: for(var i=0;i<1;i++){break aussen;} window.i=i;', []],
 ['optionale Verkettung',        'var o={};window.z=o?.a?.b;', []],
 ['optionale Verkettung FREI',   'window.z=mm?.a?.b;', ['mm']],
 ['var hoistet in Funktion',     'function f(){if(1){var v=2;} return v;} window.f=f;', []],
 ['let hoistet NICHT aus Block', 'function f(){ {let v=2;console.log(v);} return 1;} window.f=f;', []],
 ['Block-let von aussen FREI',   'function f(){ {let v=2;console.log(v);} return v2;} window.f=f;', ['v2']],
 ['Schwesterblock sieht nichts', 'function a(){var lokal=1;return lokal;} function b(){return lokal;} window.a=a;window.b=b;', ['lokal']],
 // Rueckfallprobe: eslint-scope reicht auch AUFGELOESTE globale Referenzen
 // durch globalScope.through.  Top-Level-var im Block war darum Fehlalarm.
 ['var im try, oberste Ebene',   'try{var _bi=document.getElementById("x");if(_bi)_bi.remove();}catch(e){}', []],
 ['var im if, oberste Ebene',    'if(1){var _bj=2;console.log(_bj);}', []],
 ['var in for, oberste Ebene',   'for(var _bk=0;_bk<1;_bk++){console.log(_bk);}', []],
 ['Block2 sieht Block1-Global',  'var gemeinsam=1;'+ZU+AUF+'window.z=gemeinsam;', []],
 ['typeof x ist erlaubt',        'window.z=(typeof nichtDa==="undefined");', []],
 ['Zuweisung an Undeklariertes', 'function f(){nn=5;} window.f=f;', ['nn']],
];
let ok=0,bad=0;
for(const [name,src,erw] of faelle){
  const got=[...new Set(lauf(src))].sort(); const soll=[...erw].sort();
  const gut=JSON.stringify(got)===JSON.stringify(soll);
  if(gut)ok++;else bad++;
  console.log((gut?'  OK  ':'FEHLER')+'  '+name.padEnd(30)+' erwartet['+soll.join(',')+'] bekommen['+got.join(',')+']');
}
try{fs.unlinkSync(tmp);}catch(e){}
console.log('\n'+ok+' von '+(ok+bad)+' Konstrukten korrekt.');
process.exit(bad?1:0);
