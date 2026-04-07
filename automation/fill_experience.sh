#!/bin/bash
# Add experience entries to LinkedIn profile
# Usage: ./fill_experience.sh <profile-json> <linkedin-slug>

set -euo pipefail

B=~/.claude/skills/gstack/browse/dist/browse
PROFILE_JSON="${1:?Usage: $0 <profile.json> <linkedin-slug>}"
SLUG="${2:?Usage: $0 <profile.json> <linkedin-slug>}"

COUNT=$(jq '.experiences | length' "$PROFILE_JSON")

for i in $(seq 0 $((COUNT - 1))); do
  TITLE=$(jq -r ".experiences[$i].title" "$PROFILE_JSON")
  COMPANY=$(jq -r ".experiences[$i].company" "$PROFILE_JSON")
  LOCATION=$(jq -r ".experiences[$i].location" "$PROFILE_JSON")
  EMP_TYPE=$(jq -r ".experiences[$i].employment_type" "$PROFILE_JSON")
  START_DATE=$(jq -r ".experiences[$i].start_date" "$PROFILE_JSON")
  END_DATE=$(jq -r ".experiences[$i].end_date" "$PROFILE_JSON")
  DESC=$(jq -r ".experiences[$i].description" "$PROFILE_JSON")

  echo "Adding experience $((i+1))/$COUNT: $TITLE at $COMPANY"

  # Navigate to add experience form
  $B goto "https://www.linkedin.com/in/$SLUG/edit/forms/position/new/?profileFormEntryPoint=PROFILE_SECTION" 2>/dev/null
  sleep 2

  # Fill title
  $B fill "[aria-label='Title *']" "$TITLE" 2>/dev/null
  sleep 0.5

  # Fill company (combobox with autocomplete)
  $B js "
    const companyInput = document.querySelector('input[id*=\"company\"]') ||
                         document.querySelector('[aria-label*=\"Company\"]');
    if (companyInput) {
      const setter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value'
      ).set;
      setter.call(companyInput, '$COMPANY');
      companyInput.dispatchEvent(new Event('input', { bubbles: true }));
      'typed company';
    }
  " 2>/dev/null
  sleep 1

  # Select first company option
  $B js "
    const opts = document.querySelectorAll('[role=\"option\"]');
    if (opts.length > 0) { opts[0].click(); }
  " 2>/dev/null
  sleep 0.5

  # Set employment type
  if [ -n "$EMP_TYPE" ] && [ "$EMP_TYPE" != "null" ]; then
    $B js "
      const selects = document.querySelectorAll('select');
      for (const sel of selects) {
        for (const opt of sel.options) {
          if (opt.text.trim() === '$EMP_TYPE') {
            sel.value = opt.value;
            sel.dispatchEvent(new Event('change', { bubbles: true }));
            break;
          }
        }
      }
    " 2>/dev/null
  fi

  # Uncheck "currently working" if end date is not Present
  if [ "$END_DATE" != "Present" ]; then
    $B js "
      const cb = document.querySelector('input[type=\"checkbox\"]');
      if (cb && cb.checked) { cb.click(); }
    " 2>/dev/null
    sleep 0.5
  fi

  # Set dates via <select> elements
  # Parse month and year from start/end dates
  START_MONTH=$(echo "$START_DATE" | awk '{print $1}')
  START_YEAR=$(echo "$START_DATE" | awk '{print $2}')
  END_MONTH=$(echo "$END_DATE" | awk '{print $1}')
  END_YEAR=$(echo "$END_DATE" | awk '{print $2}')

  $B js "
    function setSelectByText(sel, text) {
      for (const opt of sel.options) {
        if (opt.text.trim() === text) {
          sel.value = opt.value;
          sel.dispatchEvent(new Event('change', { bubbles: true }));
          return true;
        }
      }
      return false;
    }
    const selects = document.querySelectorAll('select');
    // Month/Year selects vary by form state
    // Typically: [employment_type, start_month, start_year, end_month, end_year]
    let dateSelects = [...selects].filter(s =>
      s.options.length > 10 || // month has 13 options
      [...s.options].some(o => o.text.match(/^20\d{2}$/))  // year
    );
    if (dateSelects.length >= 2) {
      setSelectByText(dateSelects[0], '$START_MONTH');
      setSelectByText(dateSelects[1], '$START_YEAR');
    }
    if (dateSelects.length >= 4) {
      setSelectByText(dateSelects[2], '$END_MONTH');
      setSelectByText(dateSelects[3], '$END_YEAR');
    }
    'dates set';
  " 2>/dev/null

  # Fill location
  $B js "
    const locInputs = document.querySelectorAll('input');
    for (const inp of locInputs) {
      const label = inp.getAttribute('aria-label') || '';
      if (label.toLowerCase().includes('location')) {
        const setter = Object.getOwnPropertyDescriptor(
          window.HTMLInputElement.prototype, 'value'
        ).set;
        setter.call(inp, '$LOCATION');
        inp.dispatchEvent(new Event('input', { bubbles: true }));
        break;
      }
    }
  " 2>/dev/null
  sleep 1

  # Select location from dropdown
  $B js "
    const opts = document.querySelectorAll('[role=\"option\"]');
    if (opts.length > 0) opts[0].click();
  " 2>/dev/null
  sleep 0.5

  # Inject description (React-controlled textarea)
  TEMP_JS=$(mktemp /tmp/exp-desc-XXXXX.js)
  DESC_JSON=$(jq -c ".experiences[$i].description" "$PROFILE_JSON")
  cat > "$TEMP_JS" << JSEOF
const descText = $DESC_JSON;
const textareas = document.querySelectorAll('textarea');
let desc = null;
for (const ta of textareas) {
  const label = ta.getAttribute('aria-label') || '';
  if (label.toLowerCase().includes('description')) { desc = ta; break; }
}
if (!desc && textareas.length > 0) desc = textareas[0];
if (desc) {
  const setter = Object.getOwnPropertyDescriptor(
    window.HTMLTextAreaElement.prototype, 'value'
  ).set;
  setter.call(desc, descText);
  desc.dispatchEvent(new Event('input', { bubbles: true }));
  desc.dispatchEvent(new Event('change', { bubbles: true }));
  'done - ' + descText.length + ' chars';
} else { 'textarea not found'; }
JSEOF

  $B eval "$TEMP_JS" 2>/dev/null
  rm -f "$TEMP_JS"
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

  echo "Done: $TITLE at $COMPANY"
done

echo "ALL EXPERIENCES ADDED"
