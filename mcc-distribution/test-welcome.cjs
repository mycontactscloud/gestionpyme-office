// SPDX-License-Identifier: MPL-2.0
// Exercise upstream l10n.js and the real tour messages with packaged resources.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = process.cwd();
const config = JSON.parse(fs.readFileSync('mcc-distribution/welcome-translations.json', 'utf8'));
const resources = path.resolve(process.argv[2] || 'mcc-distribution/browser-translation-overlay');
const release = JSON.parse(fs.readFileSync('mcc-distribution/distribution.json', 'utf8')).release;
const template = fs.readFileSync(process.argv[3] || 'mcc-distribution/browser-template-overlay/cool.html', 'utf8');
const indexUrl = template.match(/href=["']([^"']*\/l10n\/localizations\.json\?v=[^"']+)["']/)[1];
assert(indexUrl.endsWith('?v=' + release));
const loader = fs.readFileSync('browser/js/l10n.js', 'utf8');
const steps = fs.readFileSync('browser/src/control/onboarding/OnboardingSteps.ts', 'utf8');
const sourceMessages = Array.from(steps.matchAll(/_\(\s*'([^']*)'/g), match => match[1]);
assert.equal(sourceMessages.length, 24);
assert.deepEqual(config.messages.slice(0, 24), sourceMessages);

const locales = ['en-US', 'en-GB', 'en-CA', 'en-AU', 'en-IN', 'es-ES', 'es-MX', 'es-AR',
  'fr-FR', 'fr-CA', 'fr-CH', 'de-DE', 'de-AT', 'de-CH', 'it-IT', 'it-CH',
  'ca-ES', 'gl-ES', 'pt-PT', 'pt-AO', 'pt-MZ', 'pt-BR', 'eu-ES'];
for (const locale of locales) {
  const key = locale === 'en-GB' ? 'en-GB' : locale === 'pt-BR' ? 'pt-BR' : locale.split('-')[0];
  let entry = config.languages[key];
  const expected = entry.sameAs ? config.languages[entry.sameAs].translations : entry.translations;
  const requested = [];
  class XHR {
    open(method, url, asynchronous) {
      assert.equal(method, 'GET');
      assert.equal(asynchronous, false);
      this.url = url;
    }
    send() {
      const name = this.url.split('/').pop().split('?')[0];
      assert.equal(name, path.basename(name));
      requested.push(name);
      assert(this.url.endsWith('?v=' + release), this.url);
      this.responseText = fs.readFileSync(path.join(resources, name), 'utf8');
    }
  }
  const document = {
    documentElement: {},
    getElementsByTagName: () => [{
      type: 'application/vnd.oftn.l10n+json',
      getAttribute: name => ({rel: 'localizations', href: indexUrl})[name]
    }]
  };
  // Start in Spanish to test lazy loading when the editor URL requests another locale.
  const context = vm.createContext({document, navigator: {language: 'es-ES'}, XMLHttpRequest: XHR,
    console, setTimeout: callback => callback(), langParam: locale});
  vm.runInContext('window = this; self = this;', context);
  vm.runInContext(loader, context, {filename: 'upstream-l10n.js'});
  vm.runInContext('String.locale = langParam; function _(text) {return text.toLocaleString();}', context);
  for (let i = 0; i < config.messages.length; ++i) {
    context.message = config.messages[i];
    assert.equal(vm.runInContext('_(message)', context), expected[i], `${locale}: ${context.message}`);
  }
  const executableSteps = steps.replace(/\): OnboardingStep\[\]/, ')');
  vm.runInContext(executableSteps, context, {filename: 'OnboardingSteps.ts'});
  const actualSteps = vm.runInContext('getOnboardingSteps()', context);
  assert.equal(actualSteps.length, 12);
  actualSteps.forEach((step, i) => {
    assert.equal(step.title, expected[i * 2]);
    assert.equal(step.text, expected[i * 2 + 1]);
  });
  assert.equal(vm.runInContext('_("Unrelated synthetic message")', context), 'Unrelated synthetic message');
  assert(requested.includes(entry.resource), locale);
}
console.log(`Full tour: 12 steps and ${config.messages.length} messages resolved through versioned resources and upstream l10n.js in ${locales.length} regional locales.`);
