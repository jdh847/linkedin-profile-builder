#!/bin/bash
# Fill LinkedIn Intro section (name, headline, location)
# Usage: ./fill_intro.sh <profile-json>
# Requires: gstack browse ($B) or adapt for playwright/puppeteer

set -euo pipefail

B=~/.claude/skills/gstack/browse/dist/browse
PROFILE_JSON="${1:?Usage: $0 <profile.json>}"
SLUG="${2:?Usage: $0 <profile.json> <linkedin-slug>}"

# Extract fields from JSON
FIRST_NAME=$(jq -r '.first_name' "$PROFILE_JSON")
LAST_NAME=$(jq -r '.last_name' "$PROFILE_JSON")
HEADLINE=$(jq -r '.headline' "$PROFILE_JSON")
LOCATION=$(jq -r '.location' "$PROFILE_JSON")

echo "Setting intro for: $FIRST_NAME $LAST_NAME"

# Navigate to profile and open Edit Intro
$B goto "https://www.linkedin.com/in/$SLUG/" 2>/dev/null
sleep 2
$B js "
  const editBtn = [...document.querySelectorAll('button')]
    .find(b => b.textContent.trim() === 'Edit intro');
  if (editBtn) editBtn.click();
" 2>/dev/null
sleep 2

# Fill headline (React-controlled input)
$B js "
  const input = document.querySelector('input[aria-label*=\"Headline\"]');
  if (input) {
    const setter = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype, 'value'
    ).set;
    setter.call(input, $(jq -c '.headline' "$PROFILE_JSON"));
    input.dispatchEvent(new Event('input', { bubbles: true }));
    'filled headline';
  } else { 'headline input not found'; }
"

# Fill location — update postal code to trigger city dropdown
# Adapt the postal code for your target city
$B js "
  const postal = document.querySelector('input[id*=\"postal\"]');
  if (postal) {
    const setter = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype, 'value'
    ).set;
    setter.call(postal, 'SW1A 1AA');  // London postal code
    postal.dispatchEvent(new Event('input', { bubbles: true }));
    postal.dispatchEvent(new Event('change', { bubbles: true }));
    'updated postal code';
  }
"
sleep 1

# Save
$B js "
  const saveBtn = [...document.querySelectorAll('button')]
    .find(b => b.textContent.trim() === 'Save' && b.offsetParent !== null);
  if (saveBtn) saveBtn.click();
  'saved';
"
sleep 2

echo "Done: Intro updated"
