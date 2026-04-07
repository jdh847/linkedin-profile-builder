# LinkedIn Profile Builder

Zero-to-one LinkedIn profile automation. Feed it your resume PDF, get a fully optimized LinkedIn profile — then deploy it to LinkedIn automatically via headless browser.

**Two phases:**
1. **Generate** — AI reads your resume and produces LinkedIn-optimized content (headline, about, experience, education, skills, languages)
2. **Automate** — Browser scripts fill every LinkedIn form field, select dropdowns, inject descriptions, and save — no manual copy-pasting

Built with Claude API + Python + headless Chromium.

## Architecture

```
Phase 1: Content Generation
┌─────────┐     ┌───────────┐     ┌──────────┐     ┌──────────────┐
│ PDF     │────►│ pdfplumber│────►│ Claude   │────►│ JSON / TXT / │
│ Resume  │     │ (parser)  │     │ API      │     │ HTML output  │
└─────────┘     └───────────┘     └──────────┘     └──────┬───────┘
                                                          │
Phase 2: Browser Automation                               │
┌──────────────┐     ┌────────────┐     ┌─────────┐      │
│ automation/  │◄────│ profile    │◄────┘          │      │
│ shell scripts│     │ JSON       │               │      │
└──────┬───────┘     └────────────┘               │      │
       │                                           │      │
       ▼                                           │      │
┌──────────────┐     ┌────────────┐               │      │
│ headless     │────►│ LinkedIn   │               │      │
│ Chromium     │     │ (live)     │               │      │
└──────────────┘     └────────────┘               │      │
```

## Quick Start

### Phase 1: Generate Profile Content

```bash
# Install
pip install -e .

# Set your API key
export ANTHROPIC_API_KEY=your-key-here

# Generate profile from resume
linkedin-builder build resume.pdf

# Multiple CVs (merges content)
linkedin-builder build cv_uk.pdf cv_nl.pdf

# Target specific roles
linkedin-builder build resume.pdf -i "Target: quant risk roles in London"
```

Output:
```
output/
├── linkedin_profile.json            # Structured profile data
├── linkedin_profile_copypaste.txt   # Copy-paste ready (section by section)
└── linkedin_profile_preview.html    # Visual preview (open in browser)
```

### Phase 2: Automate LinkedIn (Optional)

The `automation/` directory contains shell scripts that read the JSON output and fill LinkedIn forms via headless Chromium. See [`automation/README.md`](automation/README.md) for setup and usage.

```bash
# Import browser cookies for authentication
$B cookie-import-browser chrome --domain linkedin.com

# Or: manual login via visible browser
$B handoff "Please log in to LinkedIn"
# ... log in ...
$B resume

# Then run the automation scripts
./automation/fill_intro.sh output/linkedin_profile.json your-slug
./automation/fill_about.sh output/linkedin_profile.json your-slug
./automation/fill_experience.sh output/linkedin_profile.json your-slug
./automation/add_skills.sh output/linkedin_profile.json your-slug
./automation/add_languages.sh output/linkedin_profile.json your-slug
./automation/set_custom_url.sh desired-url-slug
```

## Features

### Content Generation
- **PDF resume parsing** — extracts text from any resume PDF (single or multiple versions)
- **AI-powered generation** — Claude produces LinkedIn-optimized content with keyword density, character limits, and hook writing
- **Three output formats:** JSON (structured), TXT (copy-paste guide), HTML (visual preview)
- **LinkedIn best practices built in** — headline 220 chars, about 2600 chars, top 5 skills pinned, proper proficiency levels
- **Multi-CV support** — merge content from multiple resume versions

### Browser Automation
- **React-controlled form handling** — bypasses React's synthetic events using native property setters
- **Autocomplete/combobox support** — types into location, company, and language fields, selects from dropdown results
- **Date picker automation** — sets month/year selects for experience and education entries
- **Batch operations** — adds all skills and languages in a single script run
- **Error recovery** — handoff/resume pattern for authentication and CAPTCHA

## Key Technical Challenges Solved

### 1. React-Controlled Inputs
LinkedIn uses React. Setting `input.value` directly doesn't trigger state updates. Solution: use the native property setter to bypass React's synthetic event system:

```javascript
const setter = Object.getOwnPropertyDescriptor(
  window.HTMLInputElement.prototype, 'value'
).set;
setter.call(input, 'new value');
input.dispatchEvent(new Event('input', { bubbles: true }));
```

### 2. Autocomplete Dropdowns
Company, location, and language fields use autocomplete. You must type, wait for the dropdown, then click the correct `[role="option"]` element — matching by exact text to avoid wrong selections (e.g., "English" vs "Creoles and pidgins, English-based").

### 3. Textarea Injection
Experience and education descriptions use `<textarea>` with React control. Same native setter pattern but targeting `HTMLTextAreaElement.prototype`.

### 4. Authentication
LinkedIn requires login. Two approaches:
- **Cookie import**: import session cookies from a real browser
- **Handoff/resume**: open a visible Chrome window for manual login, then return control to the headless automation

## Configuration

| Flag | Default | Description |
|------|---------|-------------|
| `--api-key` | `$ANTHROPIC_API_KEY` | Anthropic API key |
| `--model` | `claude-sonnet-4-20250514` | Claude model |
| `--format` | `all` | Output: `json`, `txt`, `html`, or `all` |
| `--output-dir` / `-o` | `./output` | Output directory |
| `--instructions` / `-i` | — | Extra context (target role, location, tone) |
| `--offline` | — | Use rule-based extraction (no API key needed) |

## Project Structure

```
linkedin-profile-builder/
├── src/linkedin_builder/
│   ├── cli.py          # Click CLI interface
│   ├── generator.py    # Claude API integration + system prompt
│   ├── models.py       # LinkedInProfile, Experience, Education dataclasses
│   ├── offline.py      # Rule-based fallback (no API key)
│   ├── output.py       # JSON / TXT / HTML formatters
│   └── parser.py       # PDF text extraction (pdfplumber)
├── automation/
│   ├── README.md       # Browser automation docs
│   ├── fill_intro.sh   # Name, headline, location
│   ├── fill_about.sh   # About section
│   ├── fill_experience.sh  # Experience entries
│   ├── add_skills.sh   # Batch skill addition
│   ├── add_languages.sh    # Languages with proficiency
│   ├── set_custom_url.sh   # Vanity URL
│   └── inject_textarea.js  # Helper for React textareas
├── examples/
│   └── sample_output.json  # Example generated profile (fictional)
├── templates/
│   └── profile.html    # Jinja2 HTML preview template
└── pyproject.toml
```

## Requirements

- Python 3.9+
- Anthropic API key ([get one here](https://console.anthropic.com/))
- For automation: headless Chromium (via [gstack browse](https://github.com/nichochar/gstack), Playwright, or Puppeteer)

## License

MIT
