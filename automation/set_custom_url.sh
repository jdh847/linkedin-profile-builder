#!/bin/bash
# Set LinkedIn custom/vanity URL
# Usage: ./set_custom_url.sh <desired-slug>

set -euo pipefail

B=~/.claude/skills/gstack/browse/dist/browse
DESIRED_SLUG="${1:?Usage: $0 <desired-slug>}"

echo "Setting custom URL to: linkedin.com/in/$DESIRED_SLUG"

# Navigate to public profile settings
$B goto "https://www.linkedin.com/public-profile/settings" 2>/dev/null
sleep 3

# Click edit button
$B js "
  const editBtn = [...document.querySelectorAll('button')]
    .find(b => b.textContent.includes('Edit your custom URL'));
  if (editBtn) editBtn.click();
" 2>/dev/null
sleep 1

# Fill the vanity URL input
$B js "
  const input = document.querySelector('input[id*=\"vanity\"]') ||
                document.querySelector('[aria-label*=\"Vanity\"]');
  if (input) {
    const setter = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype, 'value'
    ).set;
    setter.call(input, '$DESIRED_SLUG');
    input.dispatchEvent(new Event('input', { bubbles: true }));
    'filled slug';
  }
" 2>/dev/null
sleep 0.5

# Save
$B js "
  const saveBtn = [...document.querySelectorAll('button')]
    .find(b => b.textContent.trim() === 'Save' && b.offsetParent !== null);
  if (saveBtn) saveBtn.click();
" 2>/dev/null
sleep 2

echo "Done: linkedin.com/in/$DESIRED_SLUG"
