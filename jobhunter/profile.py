"""Profile management for JobHunter AI."""

import json
import os
from pathlib import Path
from typing import Optional

import yaml

from .models import Profile, Experience, Education, WorkType


class ProfileManager:
    """Manages user profile storage and retrieval."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".jobhunter"
        self.profile_path = self.config_dir / "profile.yaml"
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def exists(self) -> bool:
        """Check if profile exists."""
        return self.profile_path.exists()
    
    def load(self) -> Optional[Profile]:
        """Load profile from disk."""
        if not self.exists():
            return None
        
        with open(self.profile_path, "r") as f:
            data = yaml.safe_load(f)
        
        return Profile.from_dict(data)
    
    def save(self, profile: Profile) -> None:
        """Save profile to disk."""
        with open(self.profile_path, "w") as f:
            yaml.dump(profile.to_dict(), f, default_flow_style=False, sort_keys=False)
    
    def delete(self) -> None:
        """Delete profile."""
        if self.exists():
            self.profile_path.unlink()


def parse_resume_with_llm(resume_text: str, client) -> Profile:
    """Parse resume text into a Profile using LLM."""
    
    system_prompt = """You are a resume parser. Extract structured information from resumes.
Return a JSON object with the following structure:
{
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "+1234567890",
    "location": "City, Country",
    "summary": "Professional summary...",
    "experience": [
        {
            "title": "Job Title",
            "company": "Company Name",
            "start_date": "Month Year",
            "end_date": "Month Year or Present",
            "location": "City",
            "highlights": ["Achievement 1", "Achievement 2"]
        }
    ],
    "education": [
        {
            "degree": "Degree Name",
            "school": "University Name",
            "year": 2020,
            "field": "Field of Study"
        }
    ],
    "skills": ["Skill 1", "Skill 2"],
    "languages": ["Python", "JavaScript"],
    "frameworks": ["TensorFlow", "PyTorch"],
    "tools": ["Docker", "AWS"],
    "domains": ["Machine Learning", "NLP"]
}

Be thorough but accurate. Only include information explicitly stated in the resume."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Parse this resume:\n\n{resume_text}"}
        ],
        response_format={"type": "json_object"}
    )
    
    data = json.loads(response.choices[0].message.content)
    
    # Convert to Profile
    experience = [
        Experience(
            title=exp.get("title", ""),
            company=exp.get("company", ""),
            start_date=exp.get("start_date", ""),
            end_date=exp.get("end_date"),
            location=exp.get("location"),
            highlights=exp.get("highlights", [])
        )
        for exp in data.get("experience", [])
    ]
    
    education = [
        Education(
            degree=edu.get("degree", ""),
            school=edu.get("school", ""),
            year=edu.get("year", 0),
            field=edu.get("field")
        )
        for edu in data.get("education", [])
    ]
    
    return Profile(
        name=data.get("name", ""),
        email=data.get("email", ""),
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
    )


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        import pypdf
        
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except ImportError:
        raise ImportError("pypdf is required for PDF parsing. Install with: pip install pypdf")


def extract_text_from_docx(docx_path: str) -> str:
    """Extract text from a DOCX file."""
    try:
        import docx
        
        doc = docx.Document(docx_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except ImportError:
        raise ImportError("python-docx is required for DOCX parsing. Install with: pip install python-docx")
