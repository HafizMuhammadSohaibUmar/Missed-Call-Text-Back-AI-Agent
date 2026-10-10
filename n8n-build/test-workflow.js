const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const w = JSON.parse(fs.readFileSync(path.join(__dirname, 'missed-call-text-back-n8n.json'), 'utf8'));
assert.equal(w.active, false);
const names = new Set(w.nodes.map(n => n.name));
assert.equal(names.size, w.nodes.length);
for (const [source, ports] of Object.entries(w.connections)) {
  assert(names.has(source));
  for (const outputs of Object.values(ports)) for (const output of outputs) for (const edge of output) assert(names.has(edge.node), edge.node);
}
for (const n of w.nodes.filter(n => n.type === 'n8n-nodes-base.code')) new Function(n.parameters.jsCode);
const stop = w.nodes.find(n => n.name === 'STOP Word?');
const ai = w.nodes.find(n => n.name === 'Qualification AI Agent');
assert(stop && ai);
assert(w.connections['STOP Word?'].main[1][0].node === 'Check Existing Suppression');
assert(w.connections['Is Already Suppressed?'].main[1][0].node === 'Qualification AI Agent');
assert(w.nodes.some(n => n.name === 'Four-Hour Duplicate Check'));
assert(w.nodes.some(n => n.name === 'Phone Memory - Replies'));
console.log('Missed-call n8n workflow: structure, inactive default, code syntax, STOP ordering, memory, and duplicate guard passed');
