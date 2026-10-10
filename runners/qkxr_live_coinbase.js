#!/usr/bin/env node
const fs = require('fs'); const path = require('path');
const URL='wss://advanced-trade-ws.coinbase.com';
const PRODUCT=process.env.QKXR_PRODUCT||'BTC-USD';
const TARGET=Number(process.env.QKXR_UPDATES||'100');
const DEPTH=Number(process.env.QKXR_DEPTH||'20');
const OUT=process.argv[2]||('evidence/qkxr/coinbase_'+PRODUCT.replace('-','').toLowerCase()+'_l2_live.csv');
const bids=new Map(), asks=new Map(); let count=0,lastSeq=null,ws;
function apply(side,price,qty){const m=side==='bid'?bids:asks,p=Number(price),q=Number(qty);if(!Number.isFinite(p)||!Number.isFinite(q))return;if(q===0)m.delete(p);else m.set(p,q)}
function top(m,desc){return [...m.entries()].sort((a,b)=>desc?b[0]-a[0]:a[0]-b[0]).slice(0,DEPTH)}
function snap(){const b=top(bids,true),a=top(asks,false);if(!b.length||!a.length)return null;let bv=0,av=0;for(const[,q]of b)bv+=q;for(const[,q]of a)av+=q;return {ts:new Date().toISOString(),sequence:lastSeq??'',bid:b[0][0],ask:a[0][0],bid_vol:bv,ask_vol:av,imbalance:(bv-av)/(bv+av)}}
function finish(code){try{ws?.close()}catch{};console.log('QKXR_COINBASE_L2_CAPTURE count='+count+' target='+TARGET+' output='+OUT);process.exit(code)}
fs.mkdirSync(path.dirname(OUT),{recursive:true});fs.writeFileSync(OUT,'timestamp,sequence,bid,ask,bid_vol,ask_vol,imbalance\n');
ws=new WebSocket(URL);
ws.addEventListener('open',()=>{ws.send(JSON.stringify({type:'subscribe',product_ids:[PRODUCT],channel:'level2'}));console.log('SUBSCRIBED product='+PRODUCT+' channel=level2 depth='+DEPTH)});
ws.addEventListener('message',ev=>{let msg;try{msg=JSON.parse(ev.data)}catch{return}const events=Array.isArray(msg.events)?msg.events:[];for(const e of events){if(e.product_id&&e.product_id!==PRODUCT)continue;for(const u of(e.updates||[])){const s=String(u.side||'').toLowerCase();if(s==='bid')apply('bid',u.price_level,u.new_quantity);else if(s==='offer'||s==='ask')apply('ask',u.price_level,u.new_quantity)}const seq=e.sequence_num??msg.sequence_num??null;if(seq!==null)lastSeq=seq;const s=snap();if(!s)continue;fs.appendFileSync(OUT,[s.ts,s.sequence,s.bid,s.ask,s.bid_vol,s.ask_vol,s.imbalance].join(',')+'\n');count++;if(count>=TARGET)finish(0)}});
ws.addEventListener('error',e=>{console.error('WEBSOCKET_ERROR',e.message||e);finish(2)});
ws.addEventListener('close',()=>{if(count<TARGET){console.error('WEBSOCKET_CLOSED_EARLY',count,TARGET);process.exit(3)}});
setTimeout(()=>{if(count<TARGET){console.error('TIMEOUT',count,TARGET);finish(4)}},Number(process.env.QKXR_TIMEOUT_MS||'120000'));
