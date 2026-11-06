const assert = require('node:assert/strict');
require('../browser/js/pipeline.js');
const { mergeDetections } = globalThis.RAPipeline;
const a = { label: 'Cup', source: 'builtin', confidence: 0.8, box: [0, 0, 10, 10] };
const b = { label: 'cup', source: 'custom', confidence: 0.9, box: [0, 0, 10, 10] };
const c = { label: 'person', source: 'custom', confidence: 0.7, box: [0, 0, 10, 10] };
assert.deepEqual(mergeDetections([a, b, c], 0.5, 5), [b, c]);
assert.deepEqual(mergeDetections([a, b, c], 0.5, 1), [b]);
assert.deepEqual(mergeDetections([a, { ...b, source: 'builtin' }], 0.5, 5).length, 2);
