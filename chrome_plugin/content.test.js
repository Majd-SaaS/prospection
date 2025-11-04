const test = require('node:test');
const assert = require('node:assert/strict');

const { isFollowButton } = require('./content.js');

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
