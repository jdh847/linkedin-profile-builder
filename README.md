# LinkedIn Profile Builder

AI-powered LinkedIn profile generator from PDF resumes. Feed it your CV, get a complete, optimized LinkedIn profile — headline, about, experience, education, skills, projects — ready to copy-paste.

Built with Claude API + Python.

## Features

- **PDF resume parsing** — extracts text from any resume PDF (single or multiple versions)
- **AI-powered generation** — Claude generates LinkedIn-optimized content following best practices (keyword density, character limits, hook writing)
- **Three output formats:**
  - **TXT** — section-by-section copy-paste file, organized by LinkedIn field
  - **JSON** — structured data for programmatic use
  - **HTML** — visual preview that looks like a real LinkedIn profile
- **LinkedIn best practices built in** — respects character limits (220 headline, 2600 about), pins top 5 skills, uses proper proficiency levels for languages
- **Multi-CV support** — merge content from multiple resume versions

## Quick Start

```bash
# Install
pip install -e .

# Set your API key
export ANTHROPIC_API_KEY=your-key-here

# Generate profile from resume
linkedin-builder build resume.pdf

# Multiple CVs (merges content)
linkedin-builder build cv_uk.pdf cv_nl.pdf

# Custom output directory
linkedin-builder build resume.pdf -o ~/Desktop/linkedin

# Extra instructions
linkedin-builder build resume.pdf -i "Target: quant risk roles in London"

# Re-export existing profile
linkedin-builder export output/linkedin_profile.json --format html
```

## Output

```
output/
├── linkedin_profile.json            # Structured profile data
├── linkedin_profile_copypaste.txt   # Copy-paste ready (section by section)
└── linkedin_profile_preview.html    # Visual preview (open in browser)
```

The TXT file is organized as a step-by-step guide:
1. Account creation details
2. Headline (copy-paste)
3. About section (copy-paste)
4. Experience entries (title, company, dates, description — each field labeled)
5. Education entries
6. Featured projects
7. Skills list (top 5 pinned + remaining)
8. Languages with proficiency levels
9. Final settings (custom URL, Open to Work preferences)

## How It Works

```
PDF Resume → pdfplumber → raw text → Claude API → structured JSON → TXT / HTML / JSON
```

1. **Parse**: `pdfplumber` extracts text from your resume PDF
2. **Generate**: Claude converts the resume into LinkedIn-optimized content, following a detailed system prompt with LinkedIn best practices
3. **Validate**: Enforces LinkedIn character limits (headline: 220, about: 2600, skills: 50 max)
4. **Export**: Outputs in your chosen format(s)

## Requirements

- Python 3.9+
- Anthropic API key ([get one here](https://console.anthropic.com/))

## Configuration

| Flag | Default | Description |
|------|---------|-------------|
| `--api-key` | `$ANTHROPIC_API_KEY` | Anthropic API key |
| `--model` | `claude-sonnet-4-20250514` | Claude model |
| `--format` | `all` | Output format: `json`, `txt`, `html`, or `all` |
| `--output-dir` / `-o` | `./output` | Output directory |
| `--instructions` / `-i` | — | Extra context (target role, location, tone) |

## License

MIT
