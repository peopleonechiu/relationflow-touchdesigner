const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('browser/index.html', 'utf8').match(/<script>([\s\S]*)<\/script>/)[1];
const emitted=[];
class FakeWorker {
 postMessage(m){setTimeout(()=>this.onmessage({data:{type:'done',req:m.req,ep:'wasm'}}),1)}
}
class FakeSocket {
 static OPEN=1;
 constructor(){this.readyState=0;setTimeout(()=>{this.readyState=1;if(this.onopen)this.onopen()},30)}
 send(data){emitted.push(JSON.parse(data))}
}
const nodes={status:{textContent:''},overlay:{getContext(){return {clearRect(){}}}}};
const manifest={detectors:[{id:'yolo26n'}],text_encoders:{predicate:{}},relation:{}};
const context={Worker:FakeWorker,WebSocket:FakeSocket,document:{getElementById:id=>nodes[id]},location:{host:'127.0.0.1:8777',origin:'http://127.0.0.1:8777'},fetch:async()=>({json:async()=>manifest}),setTimeout,clearTimeout,console,Promise,Error};
vm.runInNewContext(source,context);
setTimeout(()=>{try{assert.ok(emitted.some(m=>m.type==='ready'));assert.match(nodes.status.textContent,/Ready/);console.log('PASS: normal startup remains ready after late WebSocket')}catch(e){console.error(e);process.exitCode=1}},80);
