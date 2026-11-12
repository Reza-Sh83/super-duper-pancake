const assert=require("node:assert/strict");const parse=x=>JSON.parse(x,(k,v,c)=>["price","qty"].includes(k)&&typeof v==="number"?c.source:v);
const digits=s=>s.replace(".","").replace(/^0+/,"");
function crc(s){let c=-1;for(const ch of s){c^=ch.charCodeAt(0);for(let i=0;i<8;i++)c=(c>>>1)^((c&1)?0xedb88320:0)}return(c^-1)>>>0}
const url="wss://ws.kraken.com/v2",w=new WebSocket(url),raw=[],book={asks:new Map(),bids:new Map()};let checks=[],ready=false,finished=false;const timer=setTimeout(()=>end("timeout"),13000);
function end(state){if(finished)return;finished=true;clearTimeout(timer);console.log(JSON.stringify({node:process.version,url,state,checks,raw}));w.close()}
w.onopen=()=>w.send(JSON.stringify({method:"subscribe",params:{channel:"book",symbol:["BTC/USD"],depth:10,snapshot:true}}));
w.onerror=e=>end(e.message??"error");
w.onmessage=e=>{try{const received=new Date().toISOString(),p=parse(e.data);if(p.channel!=="book")return;const d=p.data[0];raw.push({received,wire:e.data});if(p.type==="snapshot"){book.asks.clear();book.bids.clear();ready=true}assert(ready);
const ordered={};for(const side of ["asks","bids"]){for(const {price,qty} of d[side]){if(Number(qty)===0)book[side].delete(price);else book[side].set(price,qty)}ordered[side]=[...book[side]].sort((a,b)=>(side==="asks"?1:-1)*(Number(a[0])-Number(b[0]))).slice(0,10);book[side]=new Map(ordered[side])}
const computed=crc([...ordered.asks,...ordered.bids].flat().map(digits).join(""));assert.equal(computed,d.checksum);checks.push({kind:p.type,checksum:computed,ask:ordered.asks[0],bid:ordered.bids[0],received,event:d.timestamp,apparentAgeMs:Date.parse(received)-Date.parse(d.timestamp)});if(checks.length===6)end("six_crc_passed")}catch(e){end(String(e))}};
