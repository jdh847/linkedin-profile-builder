#!/bin/bash
# Fill LinkedIn About section
# Usage: ./fill_about.sh <profile-json> <linkedin-slug>

set -euo pipefail

B=~/.claude/skills/gstack/browse/dist/browse
PROFILE_JSON="${1:?Usage: $0 <profile.json> <linkedin-slug>}"
SLUG="${2:?Usage: $0 <profile.json> <linkedin-slug>}"

ABOUT=$(jq -r '.about' "$PROFILE_JSON")

echo "Setting About section..."

# Navigate to Edit About
$B goto "https://www.linkedin.com/in/$SLUG/" 2>/dev/null
sleep 2
$B js "
  const editLink = [...document.querySelectorAll('a')]
    .find(a => a.textContent.includes('Edit about'));
  if (editLink) editLink.click();
  else {
    const addLink = [...document.querySelectorAll('a')]
      .find(a => a.textContent.includes('Add a summary'));
    if (addLink) addLink.click();
  }
" 2>/dev/null
sleep 2

# Write About text to temp file for injection
TEMP_JS=$(mktemp /tmp/set-about-XXXXX.js)
cat > "$TEMP_JS" << 'JSEOF'
const descText = ABOUT_PLACEHOLDER;
const textareas = document.querySelectorAll('textarea');
let target = null;
for (const ta of textareas) {
  const label = ta.getAttribute('aria-label') || '';
  if (label.toLowerCase().includes('about')) { target = ta; break; }
}
if (!target && textareas.length > 0) target = textareas[0];
if (target) {
  const setter = Object.getOwnPropertyDescriptor(
    window.HTMLTextAreaElement.prototype, 'value'
  ).set;
  setter.call(target, descText);
  target.dispatchEvent(new Event('input', { bubbles: true }));
  target.dispatchEvent(new Event('change', { bubbles: true }));
  'done - ' + descText.length + ' chars';
} else { 'textarea not found'; }
JSEOF

# Replace placeholder with actual JSON-escaped about text
ABOUT_JSON=$(jq -c '.about' "$PROFILE_JSON")
sed -i '' "s|ABOUT_PLACEHOLDER|$ABOUT_JSON|" "$TEMP_JS" 2>/dev/null || \
  sed -i "s|ABOUT_PLACEHOLDER|$ABOUT_JSON|" "$TEMP_JS"

$B eval "$TEMP_JS" 2>/dev/null
rm -f "$TEMP_JS"
sleep 0.5

# Save
$B js "
  const saveBtn = [...document.querySelectorAll('button')]
    .find(b => b.textContent.trim() === 'Save' && b.offsetParent !== null);
  if (saveBtn) saveBtn.click();
  'saved';
"
sleep 2

echo "Done: About section updated"
