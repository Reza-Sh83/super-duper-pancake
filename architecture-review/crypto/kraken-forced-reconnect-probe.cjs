const assert=require("node:assert/strict");const parse=x=>JSON.parse(x,(k,v,c)=>["price","qty"].includes(k)&&typeof v==="number"?c.source:v);
const digits=s=>s.replace(".","").replace(/^0+/,"");
function crc(s){let c=-1;for(const ch of s){c^=ch.charCodeAt(0);for(let i=0;i<8;i++)c=(c>>>1)^((c&1)?0xedb88320:0)}return(c^-1)>>>0}
const {execFileSync}=require("node:child_process");
const sample=()=>execFileSync("w32tm",["/stripchart","/computer:time.cloudflare.com","/samples:5","/dataonly"],{encoding:"utf8",timeout:21000}).split(/\r?\n/).flatMap(l=>{const m=l.match(/,\s*([+-][\d.]+)s\s*$/);return m?[Number(m[1])*1000]:[]});
(async()=>{const before=sample();assert(before.length>=3);const correction=[...before].sort((a,b)=>a-b)[Math.floor(before.length/2)];const trace=[], observations=[];let state="DISCONNECTED";
function epoch(number){return new Promise((resolve,reject)=>{const socket=new WebSocket("wss://ws.kraken.com/v2");let book={asks:new Map(),bids:new Map()},n=0,expected=false;
const timer=setTimeout(()=>{socket.close();reject(Error("deadline"))},10000);
state="SYNCING";trace.push([number,state]);assert.notEqual(state,"READY");
socket.onopen=()=>socket.send(JSON.stringify({method:"subscribe",params:{channel:"book",symbol:["BTC/USD"],depth:10,snapshot:true}}));
socket.onerror=e=>{clearTimeout(timer);reject(Error(e.message))};
socket.onclose=()=>{clearTimeout(timer);state="DISCONNECTED";trace.push([number,state]);if(expected)resolve();else reject(Error("unexpected close"))};
socket.onmessage=e=>{if(expected)return;try{const received=Date.now(),p=parse(e.data);if(p.channel!=="book")return;const d=p.data[0];assert.equal(d.symbol,"BTC/USD");assert.equal(p.type,n===0?"snapshot":"update");const ordered={};
for(const side of ["asks","bids"]){for(const {price,qty} of d[side]){if(Number(qty)===0)book[side].delete(price);else book[side].set(price,qty)}ordered[side]=[...book[side]].sort((a,b)=>(side==="asks"?1:-1)*(Number(a[0])-Number(b[0]))).slice(0,10);book[side]=new Map(ordered[side])}
assert.equal(crc([...ordered.asks,...ordered.bids].flat().map(digits).join("")),d.checksum);if(n++===0){state="READY";trace.push([number,state])}
if(d.timestamp)observations.push({number,type:p.type,checksum:d.checksum,rawAgeMs:received-Date.parse(d.timestamp),estimatedCorrectedAgeMs:received+correction-Date.parse(d.timestamp)});
if(n===3){expected=true;state="STALE";trace.push([number,state]);assert.notEqual(state,"READY");socket.close(1000,"forced test disconnect")}
}catch(err){clearTimeout(timer);socket.close();reject(err)}};
})}
await epoch(1);assert.equal(state,"DISCONNECTED");await epoch(2);assert.equal(state,"DISCONNECTED");const after=sample();assert(after.length>=3);console.log(JSON.stringify({before,after,correction,trace,observations,scope:"short public probe; forced client close and automatic new epoch; estimated age by software correction, system clock unchanged; no orders or full runtime"}))})().catch(e=>{console.error(e);process.exitCode=1});
