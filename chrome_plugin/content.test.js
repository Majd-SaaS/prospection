const test = require('node:test');
const assert = require('node:assert/strict');

const noop = () => {};

global.window = {
  location: {
    hash: '',
    href: 'https://www.linkedin.com/company/example/',
    includes: (value) => 'https://www.linkedin.com/company/example/'.includes(value),
  },
  name: '',
  document: {
    documentElement: {
      getAttribute: () => 'en',
    },
    querySelector: () => null,
    querySelectorAll: () => [],
    addEventListener: noop,
    readyState: 'complete',
  },
};

global.document = global.window.document;

global.chrome = {
  runtime: {
    sendMessage: noop,
    lastError: null,
  },
  storage: {
    local: {
      get: (keys, callback) => {
        callback(keys);
      },
    },
  },
};

global.fetch = () => Promise.resolve({ ok: true });

const {
  isFollowButton,
  classifyButtonState,
  storageGet,
  getExtensionSettings,
} = require('./content.js');

const createButton = ({
  text = '',
  ariaLabel = '',
  controlName = '',
  ariaPressed = null,
  spans = [],
  disabled = false,
} = {}) => ({
  disabled,
  textContent: text,
  getAttribute: (name) => {
    switch (name) {
      case 'aria-label':
        return ariaLabel;
      case 'data-control-name':
        return controlName;
      case 'aria-pressed':
        return ariaPressed;
      default:
        return null;
    }
  },
  querySelectorAll: (selector) => {
    if (selector === 'span') {
      return spans.map((spanText) => ({
        textContent: spanText,
      }));
    }
    return [];
  },
});

test('detects a follow button using visible text', () => {
  const button = createButton({ text: 'Follow' });
  assert.equal(isFollowButton(button), true);
});

test('ignores buttons that indicate already following', () => {
  const button = createButton({ text: 'Following' });
  assert.equal(isFollowButton(button), false);
});

test('ignores buttons with aria-pressed="true"', () => {
  const button = createButton({ text: 'Follow', ariaPressed: 'true' });
  assert.equal(isFollowButton(button), false);
});

test('detects follow button via aria-label when text missing', () => {
  const button = createButton({ ariaLabel: 'Follow company page' });
  assert.equal(isFollowButton(button), true);
});

test('ignores aria-label with following', () => {
  const button = createButton({ ariaLabel: 'Following company page' });
  assert.equal(isFollowButton(button), false);
});

test('detects follow button via nested span text', () => {
  const button = createButton({ spans: ['  Follow  '] });
  assert.equal(isFollowButton(button), true);
});

test('classifies following button state correctly', () => {
  const followButton = createButton({ text: 'Follow' });
  const followingButton = createButton({ text: 'Following', ariaPressed: 'true' });

  assert.equal(classifyButtonState(followButton), 'follow');
  assert.equal(classifyButtonState(followingButton), 'already followed');
});

test('storageGet falls back to defaults on read error', async () => {
  chrome.storage.local.get = (keys, callback) => {
    chrome.runtime.lastError = new Error('hardware unavailable');
    callback({});
    chrome.runtime.lastError = null;
  };

  const result = await storageGet({ enabled: true, autoCloseIrrelevant: false });
  assert.deepEqual(result, { enabled: true, autoCloseIrrelevant: false });
});

test('getExtensionSettings merges stored values with defaults', async () => {
  chrome.storage.local.get = (keys, callback) => {
    chrome.runtime.lastError = null;
    callback({ enabled: false });
  };

  const settings = await getExtensionSettings();
  assert.equal(settings.enabled, false);
  assert.equal(settings.autoCloseIrrelevant, true);
});
