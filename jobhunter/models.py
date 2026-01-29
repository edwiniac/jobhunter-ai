"""Data models for JobHunter AI."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import json


class ApplicationStatus(Enum):
    """Status of a job application."""
    SAVED = "saved"
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class WorkType(Enum):
    """Type of work arrangement."""
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"


@dataclass
class Experience:
    """Work experience entry."""
    title: str
    company: str
    start_date: str
    end_date: Optional[str] = None
    location: Optional[str] = None
    highlights: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "company": self.company,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "location": self.location,
            "highlights": self.highlights,
        }


@dataclass
class Education:
    """Education entry."""
    degree: str
    school: str
    year: int
    field: Optional[str] = None
    gpa: Optional[float] = None
    
    def to_dict(self) -> dict:
        return {
            "degree": self.degree,
            "school": self.school,
            "year": self.year,
            "field": self.field,
            "gpa": self.gpa,
        }


@dataclass
class Profile:
    """User profile for job matching."""
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    
    # Experience and education
    experience: list[Experience] = field(default_factory=list)
    education: list[Education] = field(default_factory=list)
    
    # Skills
    skills: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    
    # Preferences
    target_roles: list[str] = field(default_factory=list)
    target_locations: list[str] = field(default_factory=list)
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    work_types: list[WorkType] = field(default_factory=list)
    visa_sponsorship_needed: bool = False
    
    # Links
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "location": self.location,
            "summary": self.summary,
            "experience": [e.to_dict() for e in self.experience],
            "education": [e.to_dict() for e in self.education],
            "skills": self.skills,
            "languages": self.languages,
            "frameworks": self.frameworks,
            "tools": self.tools,
            "domains": self.domains,
            "target_roles": self.target_roles,
            "target_locations": self.target_locations,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "work_types": [w.value for w in self.work_types],
            "visa_sponsorship_needed": self.visa_sponsorship_needed,
            "linkedin": self.linkedin,
            "github": self.github,
            "portfolio": self.portfolio,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        experience = [
            Experience(**exp) for exp in data.get("experience", [])
        ]
        education = [
            Education(**edu) for edu in data.get("education", [])
        ]
        work_types = [
            WorkType(wt) for wt in data.get("work_types", [])
        ]
        
        return cls(
            name=data["name"],
            email=data["email"],
            phone=data.get("phone"),
            location=data.get("location"),
            summary=data.get("summary"),
            experience=experience,
            education=education,
            skills=data.get("skills", []),
            languages=data.get("languages", []),
            frameworks=data.get("frameworks", []),
            tools=data.get("tools", []),
            domains=data.get("domains", []),
            target_roles=data.get("target_roles", []),
            target_locations=data.get("target_locations", []),
            salary_min=data.get("salary_min"),
            salary_max=data.get("salary_max"),
            work_types=work_types,
            visa_sponsorship_needed=data.get("visa_sponsorship_needed", False),
            linkedin=data.get("linkedin"),
            github=data.get("github"),
            portfolio=data.get("portfolio"),
        )
    
    def get_all_skills(self) -> list[str]:
        """Get all skills combined."""
        return list(set(
            self.skills + self.languages + self.frameworks + 
            self.tools + self.domains
        ))
    
    def get_years_experience(self) -> float:
        """Calculate total years of experience."""
        # Simplified calculation
        return len(self.experience) * 1.5  # Rough estimate


@dataclass
class Job:
    """Job listing."""
    id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str  # linkedin, indeed, etc.
    
    # Optional fields
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "EUR"
    work_type: Optional[WorkType] = None
    experience_level: Optional[str] = None  # junior, mid, senior
    posted_date: Optional[datetime] = None
    
    # Extracted data
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    benefits: list[str] = field(default_factory=list)
    visa_sponsorship: Optional[bool] = None
    
    # Match data (populated after scoring)
    match_score: Optional[float] = None
    match_analysis: Optional[str] = None
    skill_matches: list[str] = field(default_factory=list)
    skill_gaps: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "description": self.description,
            "url": self.url,
            "source": self.source,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_currency": self.salary_currency,
            "work_type": self.work_type.value if self.work_type else None,
            "experience_level": self.experience_level,
            "posted_date": self.posted_date.isoformat() if self.posted_date else None,
            "required_skills": self.required_skills,
            "preferred_skills": self.preferred_skills,
            "benefits": self.benefits,
            "visa_sponsorship": self.visa_sponsorship,
            "match_score": self.match_score,
            "match_analysis": self.match_analysis,
            "skill_matches": self.skill_matches,
            "skill_gaps": self.skill_gaps,
        }


@dataclass
class Application:
    """Job application tracking."""
    id: str
    job: Job
    status: ApplicationStatus
    applied_date: Optional[datetime] = None
    
    # Tracking
    cover_letter_path: Optional[str] = None
    resume_version: Optional[str] = None
    notes: str = ""
    
    # Follow-up
    next_action: Optional[str] = None
    next_action_date: Optional[datetime] = None
    
    # Contacts
    recruiter_name: Optional[str] = None
    recruiter_email: Optional[str] = None
    
    # Timeline
    events: list[dict] = field(default_factory=list)
    
    def add_event(self, event_type: str, notes: str = ""):
        """Add an event to the timeline."""
        self.events.append({
            "type": event_type,
            "date": datetime.now().isoformat(),
            "notes": notes,
        })
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "job": self.job.to_dict(),
            "status": self.status.value,
            "applied_date": self.applied_date.isoformat() if self.applied_date else None,
            "cover_letter_path": self.cover_letter_path,
            "resume_version": self.resume_version,
            "notes": self.notes,
            "next_action": self.next_action,
            "next_action_date": self.next_action_date.isoformat() if self.next_action_date else None,
            "recruiter_name": self.recruiter_name,
            "recruiter_email": self.recruiter_email,
            "events": self.events,
        }
