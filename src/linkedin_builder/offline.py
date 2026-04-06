"""Offline profile generator — rule-based extraction without API calls.

Uses heuristic text parsing to extract structured data from common resume
formats. Works without any API key. Less polished than Claude-powered
generation but produces a solid starting point.
"""

from __future__ import annotations

import re
from typing import Optional

from .models import LinkedInProfile, Experience, Education, Project


# Common section headers in resumes
_SECTION_PATTERNS = [
    ("profile", re.compile(r"(?:PROFESSIONAL\s+)?PROFILE|SUMMARY|OBJECTIVE", re.I)),
    ("education", re.compile(r"EDUCATION", re.I)),
    ("experience", re.compile(r"(?:PROFESSIONAL\s+)?EXPERIENCE|WORK\s+EXPERIENCE|EMPLOYMENT", re.I)),
    ("skills", re.compile(r"(?:QUANTITATIVE\s+)?SKILLS|TECHNICAL\s+SKILLS|CORE\s+COMPETENCIES", re.I)),
    ("projects", re.compile(r"(?:RESEARCH\s+&\s+)?(?:QUANTITATIVE\s+)?PROJECTS|FEATURED\s+PROJECTS", re.I)),
    ("additional", re.compile(r"ADDITIONAL\s+INFORMATION|OTHER|INTERESTS|LANGUAGES", re.I)),
]


def generate_offline(resume_text: str) -> LinkedInProfile:
    """Generate a LinkedIn profile from resume text using rule-based extraction.

    This is a best-effort parser that works with most structured resume formats.
    """
    sections = _split_sections(resume_text)

    # Clean PDF artifacts globally
    resume_text = re.sub(r"\(cid:\d+\)", "▸", resume_text)

    # Extract name (usually first line)
    lines = resume_text.strip().split("\n")
    name_line = lines[0].strip()
    # Remove common resume tags from name line
    for tag in ["GRADUATE ROUTE", "NO SPONSORSHIP NEEDED", "NO SPONSORSHIP",
                "ZOEKJAAR", "NL WORK AUTHORISATION", "·", "•", "|"]:
        name_line = name_line.replace(tag, " ")
    name_line = re.sub(r"\s+", " ", name_line).strip()
    parts = name_line.split()
    first_name = parts[0] if parts else ""
    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

    # Extract email
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", resume_text)
    email = email_match.group(0) if email_match else ""

    # Extract phone
    phone_match = re.search(r"[\+\d][\d\s\-()]{7,}", resume_text)

    # Build profile section
    profile_text = sections.get("profile", "")

    # Build headline from subtitle line (usually line 2-3, contains · separators)
    headline = ""
    for line in lines[1:6]:
        line = line.strip()
        # Skip lines that are just tags/badges
        if re.match(r"^(GRADUATE|ZOEKJAAR|NO SPONSOR)", line, re.I):
            continue
        # Lines with · or | separators are typically taglines
        if ("·" in line or "|" in line) and len(line) < 220 and len(line) > 15:
            headline = line.replace("·", " | ")
            break
    if not headline:
        # Build from role keywords in the text
        roles = _infer_roles(resume_text)
        degree_match = re.search(r"(MSc|MBA|PhD)\s+\w+", resume_text)
        school_match = re.search(r"University of [\w\s]+", resume_text)
        parts = []
        if roles:
            parts.append(roles[0])
        if degree_match:
            parts.append(degree_match.group(0))
        if school_match:
            parts.append(school_match.group(0).strip())
        headline = " | ".join(parts) if parts else f"{first_name} {last_name}"

    # Build about from profile text
    about = profile_text.strip()

    # Parse experiences
    experiences = _parse_experiences(sections.get("experience", ""))

    # Parse education
    educations = _parse_educations(sections.get("education", ""))

    # Parse skills
    skills = _parse_skills(sections.get("skills", ""))

    # Parse projects
    projects = _parse_projects(sections.get("projects", ""))

    # Parse languages and additional info
    languages = _parse_languages(sections.get("additional", ""))

    # Determine location
    location = ""
    if "United Kingdom" in resume_text or "UK" in resume_text:
        location = "United Kingdom"
    elif "Netherlands" in resume_text or "NL" in resume_text:
        location = "Netherlands"

    # Suggest custom URL
    clean_name = f"{first_name}-{last_name}".lower().replace(" ", "-")
    clean_name = re.sub(r"[^a-z0-9-]", "", clean_name)
    custom_url = f"linkedin.com/in/{clean_name}"

    return LinkedInProfile(
        first_name=first_name,
        last_name=last_name,
        headline=headline[:220],
        about=about[:2600],
        location=location,
        email=email,
        custom_url=custom_url,
        experiences=experiences,
        educations=educations,
        projects=projects,
        skills=skills[:50],
        top_skills=skills[:5],
        languages=languages,
        open_to_roles=_infer_roles(resume_text),
        open_to_locations=_infer_locations(resume_text),
    )


def _split_sections(text: str) -> dict[str, str]:
    """Split resume text into named sections."""
    sections = {}
    current_key = None
    current_lines = []

    for line in text.split("\n"):
        stripped = line.strip()
        matched = False

        for key, pattern in _SECTION_PATTERNS:
            if pattern.search(stripped) and len(stripped) < 80:
                if current_key:
                    sections[current_key] = "\n".join(current_lines).strip()
                current_key = key
                current_lines = []
                matched = True
                break

        if not matched and current_key:
            current_lines.append(line)

    if current_key:
        sections[current_key] = "\n".join(current_lines).strip()

    return sections


def _parse_experiences(text: str) -> list[Experience]:
    """Extract experience entries from the experience section."""
    if not text.strip():
        return []

    experiences = []

    # Split on lines that look like company headers or role titles
    # Common patterns: "Company Name — Description" or "Title · Company" or "Role  Date"
    blocks = re.split(
        r"\n(?=(?:[A-Z][\w\s&]+(?:Ltd|Inc|Corp|Securities|Docs|Limited))|(?:(?:Founder|Engineer|Intern|Developer|Analyst|Manager|Director|Associate)\s))",
        text,
        flags=re.I,
    )

    for block in blocks:
        block = block.strip()
        if not block or len(block) < 20:
            continue

        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue

        exp = Experience(title="", company="", description="")

        # Scan first few lines for title, company, dates
        header_lines = lines[:4]
        body_lines = []
        title_found = False
        company_found = False

        for line in header_lines:
            # Check for role title
            title_match = re.match(
                r"(Founder\s*&?\s*Lead\s*Engineer|Asset\s*Management\s*Intern|Blockchain\s*Core\s*Developer|[\w\s]+(Analyst|Engineer|Developer|Manager|Intern|Director|Associate))",
                line,
                re.I,
            )
            if title_match and not title_found:
                # Extract just the title (before date or ·)
                title_text = re.split(r"\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|20\d{2}|\d{4})", line)[0]
                title_text = title_text.split("·")[0].strip()
                exp.title = title_text
                title_found = True
                continue

            # Check for company name (contains Ltd, Inc, Securities, or is a known company format)
            company_match = re.search(r"([\w\s&]+(?:Ltd|Inc|Corp|Securities|Docs|Limited))", line, re.I)
            if company_match and not company_found:
                exp.company = company_match.group(1).strip()
                company_found = True
                # Check if line also has a description after —
                desc_part = re.split(r"[—–]", line)
                if len(desc_part) > 1:
                    exp.company = desc_part[0].strip()
                continue

            # If line has — separator it might be "Company — Description"
            if ("—" in line or "–" in line) and not company_found:
                parts = re.split(r"[—–]", line)
                exp.company = parts[0].strip()
                company_found = True
                continue

        # Look for dates in entire block
        date_match = re.search(
            r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\w]*\s+\d{4}|(?:Mar|Jul|Oct)\s+\d{4}|20\d{2})\s*[–—-]+\s*(Present|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\w]*\s+\d{4}|20\d{2})",
            block,
            re.I,
        )
        if date_match:
            exp.start_date = date_match.group(1).strip()
            exp.end_date = date_match.group(2).strip()

        # Extract location
        loc_match = re.search(r"(China|United Kingdom|UK|London|Beijing|Amsterdam|Netherlands)", block, re.I)
        if loc_match:
            exp.location = loc_match.group(1)

        # Description: bullet points (lines starting with ▸ or •)
        desc_lines = []
        for line in lines:
            stripped = line.strip()
            # Skip header-like lines
            if stripped == exp.title or stripped == exp.company:
                continue
            if re.match(r"^(▸|•|\*|-)\s*", stripped):
                desc_lines.append(stripped)
            elif desc_lines:
                # Continuation of previous bullet
                desc_lines[-1] += " " + stripped

        exp.description = "\n".join(desc_lines).strip()

        # Infer employment type
        if re.search(r"intern", exp.title, re.I):
            exp.employment_type = "Internship"
        elif re.search(r"founder", exp.title, re.I):
            exp.employment_type = "Self-employed"
        else:
            exp.employment_type = "Full-time"

        if exp.company or exp.title:
            experiences.append(exp)

    return experiences


def _parse_educations(text: str) -> list[Education]:
    """Extract education entries."""
    if not text.strip():
        return []

    educations = []
    # Split by school names (lines with university/college)
    blocks = re.split(r"\n(?=.*(?:University|College|Institute|School))", text, flags=re.I)

    for block in blocks:
        block = block.strip()
        if not block or "University" not in block and "College" not in block:
            continue

        lines = block.split("\n")
        edu = Education(school="", degree="")

        # First line usually has degree and/or school
        for line in lines[:3]:
            line = line.strip()
            if re.search(r"(University|College|Institute)", line, re.I):
                edu.school = line.split("·")[0].strip()
            if re.search(r"(MSc|BSc|BA|MA|MBA|PhD|Bachelor|Master|Dual)", line, re.I):
                edu.degree = line.split("·")[0].strip()

        # Dates
        date_match = re.search(r"(Sep\w*\s+\d{4})\s*[–—-]\s*((?:Dec|Jun|May)\w*\s+\d{4})", block, re.I)
        if date_match:
            edu.start_date = date_match.group(1)
            edu.end_date = date_match.group(2)

        # Description
        desc_lines = []
        for line in lines[1:]:
            line = line.strip()
            if line and line != edu.school and line != edu.degree:
                desc_lines.append(line.lstrip("•▸- "))
        edu.description = "\n".join(desc_lines).strip()

        if edu.school:
            educations.append(edu)

    return educations


def _parse_skills(text: str) -> list[str]:
    """Extract skills from the skills section."""
    skills = []
    # Look for skill entries (often in table format: Category\tSkill1, Skill2, ...)
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Split on common delimiters
        for part in re.split(r"[,;·/]", line):
            part = part.strip()
            # Clean up parenthetical versions
            if part and len(part) > 1 and len(part) < 60:
                # Skip category labels
                if not re.match(r"^(Econometrics|Asset Pricing|Portfolio|Machine|Programming|Finance|Languages)\s*$", part, re.I):
                    skills.append(part)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for s in skills:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique


def _parse_projects(text: str) -> list[Project]:
    """Extract projects from the projects section."""
    if not text.strip():
        return []

    projects = []
    blocks = re.split(r"\n(?=[A-Z][\w\s-]{10,})", text)

    for block in blocks:
        block = block.strip()
        if not block or len(block) < 30:
            continue

        lines = block.split("\n")
        title = lines[0].strip()

        # URL
        url_match = re.search(r"(github\.com/\S+|https?://\S+)", block)
        url = url_match.group(0) if url_match else ""

        # Description
        desc_lines = [l.strip().lstrip("•▸- ") for l in lines[1:] if l.strip()]
        desc = "\n".join(desc_lines)

        # Stack
        stack_match = re.search(r"Stack:\s*(.+)", block, re.I)
        stack = stack_match.group(1).strip() if stack_match else ""

        projects.append(Project(
            title=title,
            description=desc,
            url=url,
            stack=stack,
        ))

    return projects


def _parse_languages(text: str) -> dict[str, str]:
    """Extract languages and proficiency levels."""
    languages = {}
    proficiency_map = {
        "native": "Native or bilingual proficiency",
        "bilingual": "Native or bilingual proficiency",
        "fluent": "Full professional proficiency",
        "professional": "Professional working proficiency",
        "intermediate": "Limited working proficiency",
        "basic": "Elementary proficiency",
    }

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Pattern: "English (fluent)" or "English — fluent" or "Mandarin (native)"
        for lang_match in re.finditer(
            r"(English|Mandarin|Chinese|Uyghur|Uzbek|French|German|Spanish|Arabic|Japanese|Korean|Russian|Hindi|Turkish)\s*[\(·—–-]\s*(\w+)",
            line,
            re.I,
        ):
            lang = lang_match.group(1).strip()
            level_hint = lang_match.group(2).strip().lower()

            # Map to LinkedIn proficiency
            proficiency = "Professional working proficiency"
            for key, value in proficiency_map.items():
                if key in level_hint:
                    proficiency = value
                    break

            # Normalize language names
            if lang.lower() == "chinese":
                lang = "Mandarin Chinese"

            languages[lang] = proficiency

    return languages


def _infer_roles(text: str) -> list[str]:
    """Infer target roles from resume content."""
    roles = []
    role_keywords = {
        "Quant Analyst": r"quant(?:itative)?\s+(?:finance|analyst)",
        "Risk Analyst": r"risk\s+(?:model|analy)",
        "Quant Developer": r"quant(?:itative)?\s+dev",
        "Data Scientist": r"data\s+scien|machine\s+learning",
        "Systematic Strategies Researcher": r"systematic\s+(?:strateg|trad)",
    }
    text_lower = text.lower()
    for role, pattern in role_keywords.items():
        if re.search(pattern, text_lower):
            roles.append(role)
    return roles or ["Quantitative Analyst"]


def _infer_locations(text: str) -> list[str]:
    """Infer location preferences from resume content."""
    locations = []
    if re.search(r"United Kingdom|UK|London|Edinburgh|Graduate Route", text):
        locations.extend(["United Kingdom", "London", "Edinburgh"])
    if re.search(r"Netherlands|NL|Amsterdam|Zoekjaar", text):
        locations.extend(["Netherlands", "Amsterdam"])
    if not locations:
        locations.append("Remote")
    return locations
