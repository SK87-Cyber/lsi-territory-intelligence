// Compute the snapshot digest of a template/built HTML through the verify-style DOM stub.
// Usage: node digest.js <html> [buildLabel] [dateISO]   -> prints liveDigest() JSON
const fs = require("fs");
let html = fs.readFileSync(process.argv[2], "utf8");
html = html.replace("__GEO_JSON__", "null");
const m = html.match(/<script>([\s\S]*)<\/script>/);
function el(){return {addEventListener(){},setAttribute(){},set innerHTML(v){this._h=v},get innerHTML(){return this._h||""},appendChild(){},querySelector:()=>el(),querySelectorAll:()=>[],onclick:null,onkeydown:null,style:{},classList:{add(){},remove(){},toggle(){}},dataset:{},scrollIntoView(){},getBoundingClientRect:()=>({left:0,top:0,width:100,height:100}),setPointerCapture(){},insertAdjacentHTML(){},remove(){},textContent:""};}
const document={body:el(),getElementById:()=>el(),createElement:()=>el(),addEventListener(){},querySelector:()=>el(),querySelectorAll:()=>[]};
global.window={innerWidth:1200,innerHeight:800}; global.fetch=()=>Promise.reject(new Error("offline"));
new Function("document", m[1] + ";globalThis.__d=liveDigest();")(document);
const d = globalThis.__d;
if (process.argv[3]) d.build = process.argv[3];
if (process.argv[4]) d.date = process.argv[4];
console.log(JSON.stringify(d));
