"""AI-powered LinkedIn content generator using Claude API."""

from __future__ import annotations

import json
import os
from typing import Optional

from .models import LinkedInProfile, LIMITS


SYSTEM_PROMPT = """\
You are an expert LinkedIn profile optimizer and career strategist. Your job is \
to transform raw resume/CV text into a complete, optimized LinkedIn profile.

You must return ONLY valid JSON matching the schema below. No markdown, no \
explanation, no code fences — just the JSON object.

LINKEDIN BEST PRACTICES YOU MUST FOLLOW:
1. HEADLINE (max {headline_limit} chars): keyword-rich, states value proposition clearly. \
Include role title, key skills, education credential, and visa/work authorization if relevant.
2. ABOUT (max {about_limit} chars): First 300 chars are critical (shown before "see more"). \
Open with a hook. Use first person. Include specific achievements with numbers. \
End with what you're looking for and contact info.
3. EXPERIENCE: Each entry needs a compelling description with bullet points using ▸ symbol. \
Include quantified achievements, tech stack, and impact.
4. EDUCATION: Include dissertation/thesis titles, key modules, awards.
5. SKILLS: Provide up to {skills_max} skills. First {top_skills} are most important (pinned). \
Order by relevance to target roles.
6. PROJECTS: Include problem statement, methodology, results, tech stack.
7. LANGUAGES: Use LinkedIn proficiency levels: "Native or bilingual proficiency", \
"Full professional proficiency", "Professional working proficiency", "Limited working proficiency".

JSON SCHEMA:
{{
  "first_name": "string",
  "last_name": "string",
  "headline": "string (max {headline_limit} chars)",
  "about": "string (max {about_limit} chars, use \\n for line breaks)",
  "location": "string",
  "email": "string",
  "custom_url": "string (linkedin.com/in/suggestion)",
  "experiences": [
    {{
      "title": "string",
      "company": "string",
      "location": "string",
      "start_date": "string (e.g., March 2025)",
      "end_date": "string (e.g., Present)",
      "employment_type": "string (Full-time/Part-time/Internship/Self-employed/Contract)",
      "description": "string (use \\n and ▸ for bullets)",
      "skills": ["string"]
    }}
  ],
  "educations": [
    {{
      "school": "string",
      "degree": "string",
      "field_of_study": "string",
      "start_date": "string",
      "end_date": "string",
      "description": "string"
    }}
  ],
  "projects": [
    {{
      "title": "string",
      "description": "string",
      "url": "string (if available)",
      "associated_with": "string (school or company, if applicable)",
      "stack": "string"
    }}
  ],
  "skills": ["string (up to {skills_max} skills, ordered by importance)"],
  "top_skills": ["string (first {top_skills}, these get pinned)"],
  "languages": {{"Language": "Proficiency level"}},
  "open_to_roles": ["string (job titles)"],
  "open_to_locations": ["string"]
}}
""".format(
    headline_limit=LIMITS["headline"],
    about_limit=LIMITS["about"],
    skills_max=LIMITS["skills_max"],
    top_skills=LIMITS["top_skills"],
)


def generate_profile(
    resume_text: str,
    api_key: Optional[str] = None,
    model: str = "claude-sonnet-4-20250514",
    extra_instructions: str = "",
) -> LinkedInProfile:
    """Generate a complete LinkedIn profile from resume text using Claude.

    Args:
        resume_text: Raw text extracted from resume PDF(s).
        api_key: Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
        model: Claude model to use.
        extra_instructions: Additional instructions (e.g., target role, location preferences).

    Returns:
        LinkedInProfile with all sections populated.
    """
    try:
        import anthropic
    except ImportError:
        raise RuntimeError(
            "anthropic SDK is required. Install with: pip install anthropic"
        )

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
            "or pass --api-key flag."
        )

    client = anthropic.Anthropic(api_key=key)

    user_msg = f"Here is the resume/CV text to convert into a LinkedIn profile:\n\n{resume_text}"
    if extra_instructions:
        user_msg += f"\n\nAdditional instructions:\n{extra_instructions}"

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw = response.content[0].text.strip()

    # Strip markdown code fences if the model wrapped the JSON
    if raw.startswith("```"):
        lines = raw.split("\n")
        # Remove first and last lines (```json and ```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw = "\n".join(lines)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Failed to parse AI response as JSON: {e}\n\nRaw response:\n{raw[:500]}"
        )

    profile = LinkedInProfile.from_dict(data)
    _enforce_limits(profile)
    return profile


def _enforce_limits(profile: LinkedInProfile) -> None:
    """Truncate fields that exceed LinkedIn character limits."""
    if len(profile.headline) > LIMITS["headline"]:
        profile.headline = profile.headline[: LIMITS["headline"] - 3] + "..."
    if len(profile.about) > LIMITS["about"]:
        profile.about = profile.about[: LIMITS["about"] - 3] + "..."
    if len(profile.skills) > LIMITS["skills_max"]:
        profile.skills = profile.skills[: LIMITS["skills_max"]]
    if len(profile.top_skills) > LIMITS["top_skills"]:
        profile.top_skills = profile.top_skills[: LIMITS["top_skills"]]
