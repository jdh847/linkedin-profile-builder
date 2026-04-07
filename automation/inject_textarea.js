/**
 * Helper: Inject text into a React-controlled textarea.
 *
 * LinkedIn uses React, so setting .value directly doesn't trigger
 * state updates. This uses the native property setter to bypass
 * React's synthetic event system.
 *
 * Usage with gstack browse:
 *   $B eval /path/to/inject_textarea.js
 *
 * Modify SELECTOR and TEXT before running.
 */

const SELECTOR = 'textarea';  // CSS selector or aria-label match
const TEXT = 'Your description text here.\n\nWith multiple paragraphs.';

// Find the textarea
const textareas = document.querySelectorAll('textarea');
let target = null;

// Try aria-label match first
for (const ta of textareas) {
  const label = ta.getAttribute('aria-label') || '';
  if (label.toLowerCase().includes('description')) {
    target = ta;
    break;
  }
}
// Fallback to first textarea
if (!target && textareas.length > 0) target = textareas[0];

if (target) {
  const setter = Object.getOwnPropertyDescriptor(
    window.HTMLTextAreaElement.prototype, 'value'
  ).set;
  setter.call(target, TEXT);
  target.dispatchEvent(new Event('input', { bubbles: true }));
  target.dispatchEvent(new Event('change', { bubbles: true }));
  'injected ' + TEXT.length + ' chars';
} else {
  'textarea not found';
}
