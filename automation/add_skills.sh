#!/bin/bash
# Batch-add skills to LinkedIn profile
# Usage: ./add_skills.sh <profile-json> <linkedin-slug>

set -euo pipefail

B=~/.claude/skills/gstack/browse/dist/browse
PROFILE_JSON="${1:?Usage: $0 <profile.json> <linkedin-slug>}"
SLUG="${2:?Usage: $0 <profile.json> <linkedin-slug>}"

# Extract skills from JSON
SKILLS=$(jq -r '.skills[]' "$PROFILE_JSON")

# Navigate to add skill form
$B goto "https://www.linkedin.com/in/$SLUG/edit/forms/skill/new/?profileFormEntryPoint=PROFILE_SECTION" 2>/dev/null
sleep 2

FIRST=true
while IFS= read -r skill; do
  [ -z "$skill" ] && continue
  echo "Adding: $skill"

  if [ "$FIRST" = false ]; then
    # Click "Add more skills" after first save
    $B js "
      const btns = document.querySelectorAll('button');
      for (const b of btns) {
        if (b.textContent.includes('Add more') && b.offsetParent !== null) {
          b.click(); break;
        }
      }
    " 2>/dev/null
    sleep 1
  fi
  FIRST=false

  # Fill skill name
  $B fill "[aria-label='Skill *']" "$skill" 2>/dev/null || $B js "
    const input = document.querySelector('input[id*=\"skill\"]');
    if (input) {
      const setter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value'
      ).set;
      setter.call(input, '$skill');
      input.dispatchEvent(new Event('input', { bubbles: true }));
    }
  " 2>/dev/null
  sleep 1

  # Select first autocomplete option
  $B js "
    const opts = document.querySelectorAll('[role=\"option\"]');
    if (opts.length > 0) { opts[0].click(); 'selected: ' + opts[0].textContent.trim(); }
    else { 'no options found'; }
  " 2>/dev/null
  sleep 0.5

  # Click Save
  $B js "
    const btns = document.querySelectorAll('button');
    for (const b of btns) {
      if (b.textContent.trim() === 'Save' && b.offsetParent !== null) {
        b.click(); break;
      }
    }
    'saved';
  " 2>/dev/null
  sleep 2

  echo "Done: $skill"
done <<< "$SKILLS"

echo "ALL SKILLS ADDED"
