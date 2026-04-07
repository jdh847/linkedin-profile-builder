#!/bin/bash
# Add languages with proficiency levels to LinkedIn profile
# Usage: ./add_languages.sh <profile-json> <linkedin-slug>

set -euo pipefail

B=~/.claude/skills/gstack/browse/dist/browse
PROFILE_JSON="${1:?Usage: $0 <profile.json> <linkedin-slug>}"
SLUG="${2:?Usage: $0 <profile.json> <linkedin-slug>}"

# Extract languages as "name|proficiency" pairs
LANGS=$(jq -r '.languages | to_entries[] | "\(.key)|\(.value)"' "$PROFILE_JSON")

while IFS='|' read -r lang prof; do
  [ -z "$lang" ] && continue
  echo "Adding language: $lang ($prof)"

  # Navigate to add language form
  $B goto "https://www.linkedin.com/in/$SLUG/edit/forms/language/new/?profileFormEntryPoint=PROFILE_SECTION" 2>/dev/null
  sleep 2

  # Fill language name (React-controlled combobox)
  $B js "
    const langInput = document.querySelector('input[id*=\"language\"]');
    if (langInput) {
      const setter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value'
      ).set;
      setter.call(langInput, '$lang');
      langInput.dispatchEvent(new Event('input', { bubbles: true }));
      'typed $lang';
    } else { 'language input not found'; }
  " 2>/dev/null
  sleep 1

  # Select the exact match from dropdown (avoid "Creoles and pidgins" etc.)
  $B js "
    const opts = document.querySelectorAll('[role=\"option\"]');
    for (const o of opts) {
      if (o.textContent.trim() === '$lang') { o.click(); 'selected $lang'; break; }
    }
  " 2>/dev/null
  sleep 0.5

  # Set proficiency via <select> dropdown
  $B js "
    const selects = document.querySelectorAll('select');
    for (const sel of selects) {
      for (const opt of sel.options) {
        if (opt.text.trim() === '$prof') {
          sel.value = opt.value;
          sel.dispatchEvent(new Event('change', { bubbles: true }));
          break;
        }
      }
    }
    'set proficiency to $prof';
  " 2>/dev/null
  sleep 0.5

  # Save
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

  echo "Done: $lang"
done <<< "$LANGS"

echo "ALL LANGUAGES ADDED"
