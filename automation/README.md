# Browser Automation Scripts

These scripts automate filling LinkedIn profile fields using headless Chromium.
They were used with [gstack browse](https://github.com/nichochar/gstack) but
can be adapted for Playwright, Puppeteer, or Selenium.

## Architecture

```
PDF Resume ──► linkedin-builder CLI ──► JSON profile
                                           │
                                           ▼
                                    automation scripts
                                           │
                                    headless Chromium
                                           │
                                           ▼
                                    LinkedIn profile (live)
```

## Scripts

| Script | Purpose |
|--------|---------|
| `fill_intro.sh` | Set name, headline, location via Edit Intro modal |
| `fill_about.sh` | Inject About section text (React-controlled textarea) |
| `fill_experience.sh` | Add experience entries with title, company, dates, description |
| `fill_education.sh` | Add/edit education entries |
| `add_skills.sh` | Batch-add skills from a list |
| `add_languages.sh` | Add languages with proficiency levels |
| `set_custom_url.sh` | Change vanity URL on public profile settings page |
| `inject_textarea.js` | Helper: inject text into React-controlled textarea fields |

## Key Techniques

### 1. React-Controlled Inputs

LinkedIn uses React, so `element.value = 'text'` doesn't trigger state updates.
Use the native setter pattern:

```javascript
const setter = Object.getOwnPropertyDescriptor(
  window.HTMLInputElement.prototype, 'value'
).set;
setter.call(inputElement, 'new value');
inputElement.dispatchEvent(new Event('input', { bubbles: true }));
```

For textareas, use `HTMLTextAreaElement.prototype` instead.

### 2. Autocomplete/Combobox Fields

LinkedIn's location, company, and language fields use autocomplete dropdowns:

```bash
# Type to trigger dropdown
$B fill "[aria-label='City']" "London"
sleep 1
# Select first matching option
$B js "document.querySelectorAll('[role=\"option\"]')[0].click()"
```

### 3. Date Selects

LinkedIn date fields are `<select>` elements. Find them by position or label:

```javascript
const selects = document.querySelectorAll('select');
// selects[0] = month, selects[1] = year (for start date)
// selects[2] = month, selects[3] = year (for end date)
function setSelectByText(sel, text) {
  for (const opt of sel.options) {
    if (opt.text.trim() === text) {
      sel.value = opt.value;
      sel.dispatchEvent(new Event('change', { bubbles: true }));
      return;
    }
  }
}
```

### 4. Handling Authentication

LinkedIn requires login. Use cookie import or browser handoff:

```bash
# Option 1: Import cookies from your real browser
$B cookie-import-browser chrome --domain linkedin.com

# Option 2: Handoff to visible browser for manual login
$B handoff "Please log in to LinkedIn"
# ... user logs in ...
$B resume  # return control to automation
```

## Adapting for Playwright

The same patterns work with Playwright:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.linkedin.com/in/YOUR-SLUG/")

    # React-controlled input
    page.evaluate("""
        const setter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value'
        ).set;
        const input = document.querySelector('[aria-label="Headline"]');
        setter.call(input, 'Your Headline');
        input.dispatchEvent(new Event('input', { bubbles: true }));
    """)
```

## Notes

- Always add `sleep` between form interactions (LinkedIn's React needs time to re-render)
- Snapshot the accessibility tree before interacting to find correct element refs
- LinkedIn rate-limits rapid form submissions — add 1-2s delays between saves
- The "Add more skills" button appears after saving each skill
- Language proficiency is a standard `<select>` dropdown (no autocomplete)
