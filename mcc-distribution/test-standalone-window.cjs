// SPDX-License-Identifier: MPL-2.0
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(__dirname + '/standalone-window.js', 'utf8');

function fixture(options = {}) {
    const callbacks = {}, timeouts = [], intervals = [];
    let closed = 0, cleared = 0, removed = false;
    const map = {on: (name, fn) => { callbacks[name] = fn; }, _disableDefaultAction: {UI_Close: !!options.disabled}};
    const document = {documentElement: {lang: options.lang || 'en'}, body: {replaceChildren(node) { this.result = node; }},
        createElement: tag => ({tag, children: [], appendChild(node) { this.children.push(node); }})};
    const window = {app: options.late ? {} : {map}, ThisIsAMobileApp: !!options.native,
        close() { assert(removed, 'normal document removal must run before closing the window'); closed++; },
        setTimeout: fn => timeouts.push(fn), setInterval: fn => intervals.push(fn), clearInterval: () => { cleared++; }};
    window.top = options.framed ? {} : window;
    vm.runInNewContext(source, {window, document, navigator: {language: 'en'}, brandProductName: 'GestiónPYME Office'});
    return {window, map, document, callbacks, timeouts, intervals, remove() { removed = true; },
        closed: () => closed, cleared: () => cleared};
}

const normal = fixture();
normal.callbacks.postMessage({msgId: 'UI_Save'});
assert.equal(normal.timeouts.length, 0);
normal.callbacks.postMessage({msgId: 'UI_Close'});
normal.callbacks.postMessage({msgId: 'UI_Close'});
assert.equal(normal.closed(), 0);
assert.equal(normal.timeouts.length, 1);
normal.remove();
normal.timeouts.shift()();
assert.equal(normal.closed(), 1);

// If the browser refuses to close a manually opened tab, it gets a useful message.
normal.timeouts.shift()();
assert.match(normal.document.body.result.children[1].textContent, /Close this tab/);
const spanish = fixture({lang: 'es'});
spanish.callbacks.postMessage({msgId: 'UI_Close'}); spanish.remove();
spanish.timeouts.shift()(); spanish.timeouts.shift()();
assert.match(spanish.document.body.result.children[1].textContent, /Cierra esta pestaña/);

for (const options of [{framed: true}, {native: true}]) {
    const f = fixture(options);
    assert.equal(f.callbacks.postMessage, undefined);
    assert.equal(f.intervals.length, 0);
}
const disabled = fixture({disabled: true});
disabled.callbacks.postMessage({msgId: 'UI_Close'});
assert.equal(disabled.timeouts.length, 0);
const late = fixture({late: true});
late.window.app.map = late.map; late.intervals[0]();
assert.equal(typeof late.callbacks.postMessage, 'function'); assert.equal(late.cleared(), 1);
const failed = fixture({late: true});
for (let i = 0; i < 240; i++) failed.intervals[0]();
assert.equal(failed.cleared(), 1);
console.log('Standalone close: normal action order, duplicate clicks, fallback, frame/native isolation, disabled action and delayed startup passed.');
