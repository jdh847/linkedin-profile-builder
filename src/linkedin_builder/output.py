"""Output formatters — JSON, copy-paste TXT, and HTML preview."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .models import LinkedInProfile


def to_json(profile: LinkedInProfile, output_path: Optional[str] = None) -> str:
    """Export profile as JSON."""
    result = profile.to_json(indent=2)
    if output_path:
        Path(output_path).write_text(result, encoding="utf-8")
    return result


def to_txt(profile: LinkedInProfile, output_path: Optional[str] = None) -> str:
    """Export profile as copy-paste-ready plain text."""
    sections = []

    sections.append("=" * 62)
    sections.append("LINKEDIN PROFILE — COPY-PASTE READY")
    sections.append(f"{profile.first_name} {profile.last_name}")
    sections.append("=" * 62)
    sections.append("")

    # Step 1: Account
    sections.append(_divider("STEP 1: CREATE ACCOUNT"))
    sections.append(f"Email: {profile.email}")
    sections.append(f"First name: {profile.first_name}")
    sections.append(f"Last name: {profile.last_name}")
    sections.append(f"Location: {profile.location}")
    if profile.experiences:
        exp = profile.experiences[0]
        sections.append(f"Current role: {exp.title} at {exp.company}")
    sections.append("")

    # Step 2: Headline
    sections.append(_divider("STEP 2: HEADLINE (paste into headline field)"))
    sections.append(profile.headline)
    sections.append("")

    # Step 3: About
    sections.append(_divider("STEP 3: ABOUT SECTION (paste into 'Add a summary')"))
    sections.append(profile.about)
    sections.append("")

    # Step 4: Experience
    for i, exp in enumerate(profile.experiences, 1):
        sections.append(_divider(f"STEP 4: EXPERIENCE — Entry {i} of {len(profile.experiences)}"))
        sections.append(f"Title:           {exp.title}")
        sections.append(f"Company:         {exp.company}")
        sections.append(f"Location:        {exp.location}")
        sections.append(f"Start Date:      {exp.start_date}")
        sections.append(f"End Date:        {exp.end_date}")
        if exp.employment_type:
            sections.append(f"Employment Type: {exp.employment_type}")
        sections.append("")
        sections.append("Description (paste this):")
        sections.append(exp.description)
        if exp.skills:
            sections.append("")
            sections.append(f"Skills: {', '.join(exp.skills)}")
        sections.append("")

    # Step 5: Education
    for i, edu in enumerate(profile.educations, 1):
        sections.append(_divider(f"STEP 5: EDUCATION — Entry {i} of {len(profile.educations)}"))
        sections.append(f"School:          {edu.school}")
        sections.append(f"Degree:          {edu.degree}")
        sections.append(f"Field of Study:  {edu.field_of_study}")
        sections.append(f"Start Date:      {edu.start_date}")
        sections.append(f"End Date:        {edu.end_date}")
        sections.append("")
        sections.append("Description (paste this):")
        sections.append(edu.description)
        sections.append("")

    # Step 6: Featured / Projects
    if profile.projects:
        for i, proj in enumerate(profile.projects, 1):
            sections.append(_divider(f"STEP 6: FEATURED — Project {i} of {len(profile.projects)}"))
            sections.append(f"Title: {proj.title}")
            if proj.url:
                sections.append(f"URL: {proj.url}")
            if proj.associated_with:
                sections.append(f"Associated with: {proj.associated_with}")
            sections.append("")
            sections.append("Description (paste this):")
            sections.append(proj.description)
            if proj.stack:
                sections.append(f"\nStack: {proj.stack}")
            sections.append("")

    # Step 7: Skills
    sections.append(_divider("STEP 7: SKILLS"))
    sections.append("PIN THESE TOP 5:")
    for i, skill in enumerate(profile.top_skills, 1):
        sections.append(f"  {i}. {skill}")
    sections.append("")
    sections.append("THEN ADD:")
    remaining = [s for s in profile.skills if s not in profile.top_skills]
    for i, skill in enumerate(remaining, len(profile.top_skills) + 1):
        sections.append(f"  {i}. {skill}")
    sections.append("")

    # Step 8: Languages
    sections.append(_divider("STEP 8: LANGUAGES"))
    for lang, level in profile.languages.items():
        sections.append(f"  {lang:<15} → {level}")
    sections.append("")

    # Step 9: Settings
    sections.append(_divider("STEP 9: FINAL SETTINGS"))
    if profile.custom_url:
        sections.append(f"Custom URL: {profile.custom_url}")
    if profile.open_to_roles:
        sections.append(f"Open to work: {', '.join(profile.open_to_roles)}")
    if profile.open_to_locations:
        sections.append(f"Locations: {', '.join(profile.open_to_locations)}")
    sections.append("")
    sections.append("=" * 62)
    sections.append("DONE! Your LinkedIn profile is complete.")
    sections.append("=" * 62)

    result = "\n".join(sections)
    if output_path:
        Path(output_path).write_text(result, encoding="utf-8")
    return result


def to_html(profile: LinkedInProfile, output_path: Optional[str] = None) -> str:
    """Export profile as an HTML preview page."""
    try:
        from jinja2 import Template
    except ImportError:
        raise RuntimeError("jinja2 is required for HTML output: pip install jinja2")

    template_path = Path(__file__).parent.parent.parent / "templates" / "profile.html"
    if template_path.exists():
        template_str = template_path.read_text(encoding="utf-8")
    else:
        template_str = _DEFAULT_HTML_TEMPLATE

    template = Template(template_str)
    html = template.render(profile=profile)

    if output_path:
        Path(output_path).write_text(html, encoding="utf-8")
    return html


def _divider(title: str) -> str:
    line = "━" * 62
    return f"\n{line}\n{title}\n{line}"


_DEFAULT_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ profile.first_name }} {{ profile.last_name }} — LinkedIn Preview</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #f3f2ef; color: #191919; line-height: 1.5; }
  .container { max-width: 800px; margin: 0 auto; padding: 20px; }
  .card { background: #fff; border-radius: 8px; border: 1px solid #e0e0e0;
          margin-bottom: 8px; padding: 24px; }
  .banner { height: 120px; background: linear-gradient(135deg, #0a66c2, #004182);
            border-radius: 8px 8px 0 0; margin: -24px -24px 0; }
  .avatar { width: 120px; height: 120px; border-radius: 50%; background: #e0e0e0;
            border: 4px solid #fff; margin-top: -60px; display: flex; align-items: center;
            justify-content: center; font-size: 48px; color: #666; }
  h1 { font-size: 24px; margin: 12px 0 4px; }
  .headline { color: #666; font-size: 14px; margin-bottom: 8px; }
  .location { color: #666; font-size: 13px; }
  .section-title { font-size: 20px; font-weight: 600; margin-bottom: 16px;
                   padding-bottom: 8px; border-bottom: 1px solid #e0e0e0; }
  .about-text { white-space: pre-wrap; font-size: 14px; }
  .exp-item { margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid #f0f0f0; }
  .exp-item:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
  .exp-title { font-weight: 600; font-size: 16px; }
  .exp-company { color: #333; font-size: 14px; }
  .exp-dates { color: #666; font-size: 13px; }
  .exp-desc { white-space: pre-wrap; font-size: 14px; margin-top: 8px; }
  .skill-badge { display: inline-block; background: #e8f4fd; color: #0a66c2;
                 padding: 4px 12px; border-radius: 16px; font-size: 13px;
                 margin: 3px; font-weight: 500; }
  .skill-badge.top { background: #0a66c2; color: #fff; }
  .lang-item { display: flex; justify-content: space-between; padding: 6px 0;
               border-bottom: 1px solid #f0f0f0; font-size: 14px; }
  .open-to { background: #e8f4fd; border: 1px solid #0a66c2; border-radius: 8px;
             padding: 12px 16px; margin-top: 12px; font-size: 13px; color: #0a66c2; }
  .footer { text-align: center; padding: 20px; color: #999; font-size: 12px; }
</style>
</head>
<body>
<div class="container">

  <div class="card">
    <div class="banner"></div>
    <div class="avatar">{{ profile.first_name[0] }}{{ profile.last_name[0] }}</div>
    <h1>{{ profile.first_name }} {{ profile.last_name }}</h1>
    <div class="headline">{{ profile.headline }}</div>
    <div class="location">{{ profile.location }}{% if profile.email %} · {{ profile.email }}{% endif %}</div>
    {% if profile.open_to_roles %}
    <div class="open-to">
      <strong>Open to work:</strong> {{ profile.open_to_roles | join(', ') }}
      {% if profile.open_to_locations %} · {{ profile.open_to_locations | join(', ') }}{% endif %}
    </div>
    {% endif %}
  </div>

  <div class="card">
    <div class="section-title">About</div>
    <div class="about-text">{{ profile.about }}</div>
  </div>

  <div class="card">
    <div class="section-title">Experience</div>
    {% for exp in profile.experiences %}
    <div class="exp-item">
      <div class="exp-title">{{ exp.title }}</div>
      <div class="exp-company">{{ exp.company }} · {{ exp.employment_type }}</div>
      <div class="exp-dates">{{ exp.start_date }} – {{ exp.end_date }} · {{ exp.location }}</div>
      <div class="exp-desc">{{ exp.description }}</div>
    </div>
    {% endfor %}
  </div>

  <div class="card">
    <div class="section-title">Education</div>
    {% for edu in profile.educations %}
    <div class="exp-item">
      <div class="exp-title">{{ edu.school }}</div>
      <div class="exp-company">{{ edu.degree }}{% if edu.field_of_study %}, {{ edu.field_of_study }}{% endif %}</div>
      <div class="exp-dates">{{ edu.start_date }} – {{ edu.end_date }}</div>
      <div class="exp-desc">{{ edu.description }}</div>
    </div>
    {% endfor %}
  </div>

  {% if profile.projects %}
  <div class="card">
    <div class="section-title">Featured Projects</div>
    {% for proj in profile.projects %}
    <div class="exp-item">
      <div class="exp-title">{{ proj.title }}</div>
      {% if proj.url %}<div class="exp-company">{{ proj.url }}</div>{% endif %}
      {% if proj.associated_with %}<div class="exp-dates">Associated with: {{ proj.associated_with }}</div>{% endif %}
      <div class="exp-desc">{{ proj.description }}</div>
      {% if proj.stack %}<div class="exp-dates" style="margin-top:8px">Stack: {{ proj.stack }}</div>{% endif %}
    </div>
    {% endfor %}
  </div>
  {% endif %}

  <div class="card">
    <div class="section-title">Skills</div>
    {% for skill in profile.top_skills %}
    <span class="skill-badge top">{{ skill }}</span>
    {% endfor %}
    {% for skill in profile.skills %}
    {% if skill not in profile.top_skills %}
    <span class="skill-badge">{{ skill }}</span>
    {% endif %}
    {% endfor %}
  </div>

  <div class="card">
    <div class="section-title">Languages</div>
    {% for lang, level in profile.languages.items() %}
    <div class="lang-item">
      <span>{{ lang }}</span>
      <span style="color:#666">{{ level }}</span>
    </div>
    {% endfor %}
  </div>

</div>
<div class="footer">
  Generated by <strong>linkedin-profile-builder</strong> · github.com/jdh847/linkedin-profile-builder
</div>
</body>
</html>
"""
