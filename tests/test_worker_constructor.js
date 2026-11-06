const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('browser/index.html', 'utf8').match(/<script>([\s\S]*)<\/script>/)[1];
const emitted=[];
class FakeWorker { constructor(){throw new Error('worker initialization failed')} }
class FakeSocket {
 static OPEN=1;
 constructor(){this.readyState=0;setTimeout(()=>{this.readyState=1;if(this.onopen)this.onopen()},20)}
 send(data){emitted.push(JSON.parse(data))}
}
const nodes={status:{textContent:''},overlay:{getContext(){return {clearRect(){}}}}};
const context={Worker:FakeWorker,WebSocket:FakeSocket,document:{getElementById:id=>nodes[id]},location:{host:'127.0.0.1:8777',origin:'http://127.0.0.1:8777'},fetch:async()=>({json:async()=>({})}),setTimeout,clearTimeout,console,Promise,Error};
vm.runInNewContext(source,context);
setTimeout(()=>{try{assert.ok(emitted.some(m=>String(m.message||'').includes('worker initialization failed')));console.log('PASS: worker failure reported after WebSocket opens')}catch(e){console.error('FAIL: worker failure hidden; emitted',JSON.stringify(emitted));process.exitCode=1}},80);
