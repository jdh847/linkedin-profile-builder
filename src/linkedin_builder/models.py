"""Data models for LinkedIn profile sections."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Experience:
    title: str
    company: str
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    employment_type: str = ""
    description: str = ""
    skills: list[str] = field(default_factory=list)


@dataclass
class Education:
    school: str
    degree: str
    field_of_study: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""


@dataclass
class Project:
    title: str
    description: str
    url: str = ""
    associated_with: str = ""
    stack: str = ""


@dataclass
class LinkedInProfile:
    """Complete LinkedIn profile content."""

    # Basic info
    first_name: str = ""
    last_name: str = ""
    headline: str = ""
    about: str = ""
    location: str = ""
    email: str = ""
    custom_url: str = ""

    # Sections
    experiences: list[Experience] = field(default_factory=list)
    educations: list[Education] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    top_skills: list[str] = field(default_factory=list)
    languages: dict[str, str] = field(default_factory=dict)

    # Job preferences
    open_to_roles: list[str] = field(default_factory=list)
    open_to_locations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict) -> LinkedInProfile:
        experiences = [Experience(**e) for e in data.pop("experiences", [])]
        educations = [Education(**e) for e in data.pop("educations", [])]
        projects = [Project(**p) for p in data.pop("projects", [])]
        return cls(
            experiences=experiences,
            educations=educations,
            projects=projects,
            **data,
        )

    @classmethod
    def from_json(cls, json_str: str) -> LinkedInProfile:
        return cls.from_dict(json.loads(json_str))


# LinkedIn character limits
LIMITS = {
    "headline": 220,
    "about": 2600,
    "experience_description": 2000,
    "education_description": 1000,
    "project_description": 2000,
    "skills_max": 50,
    "top_skills": 5,
}
