import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const script = readFileSync(new URL('../web/static/language.js', import.meta.url), 'utf8');

const runLanguageScript = ({
  browserLanguages = ['en-US'],
  pageLanguage = 'en',
  storedLanguage = null,
} = {}) => {
  const state = {
    click: null,
    domReady: null,
    replaced: null,
    saved: null,
  };
  const targetLanguage = pageLanguage === 'ja' ? 'en' : 'ja';
  const languageLink = {
    hreflang: targetLanguage,
    addEventListener(event, listener) {
      if (event === 'click') state.click = listener;
    },
  };
  const location = {
    hash: '#measurements',
    href: 'https://notification-sound-db.semnil.com/?q=bell#measurements',
    search: '?q=bell',
    replace(value) {
      state.replaced = value;
    },
  };

  const context = {
    URL,
    document: {
      documentElement: { lang: pageLanguage },
      querySelector(selector) {
        if (selector === '.language-link') return languageLink;
        const match = selector.match(/hreflang="(en|ja)"/);
        if (!match) return null;
        const path = match[1] === 'ja' ? '/ja/' : '/';
        return { href: `https://notification-sound-db.semnil.com${path}` };
      },
      addEventListener(event, listener) {
        if (event === 'DOMContentLoaded') state.domReady = listener;
      },
    },
    localStorage: {
      getItem() {
        return storedLanguage;
      },
      setItem(key, value) {
        state.saved = { key, value };
      },
    },
    navigator: {
      language: browserLanguages[0],
      languages: browserLanguages,
    },
    window: { location },
  };
  vm.runInNewContext(script, context);
  return state;
};

test('browser preference selects Japanese and preserves URL state', () => {
  const state = runLanguageScript({ browserLanguages: ['ja-JP', 'en-US'] });
  assert.equal(
    state.replaced,
    'https://notification-sound-db.semnil.com/ja/?q=bell#measurements',
  );
});

test('stored selection takes priority over browser preference', () => {
  const state = runLanguageScript({
    browserLanguages: ['ja-JP', 'en-US'],
    pageLanguage: 'ja',
    storedLanguage: 'en',
  });
  assert.equal(
    state.replaced,
    'https://notification-sound-db.semnil.com/?q=bell#measurements',
  );
});

test('language switch stores an explicit selection', () => {
  const state = runLanguageScript();
  assert.equal(state.replaced, null);
  state.domReady();
  state.click();
  assert.deepEqual(state.saved, {
    key: 'notification-sound-db.language',
    value: 'ja',
  });
});
