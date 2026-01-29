"""AI-powered job matching engine."""

import json
from typing import Optional

from openai import OpenAI

from .models import Job, Profile


class JobMatcher:
    """Matches jobs to user profile using AI."""
    
    def __init__(self, client: Optional[OpenAI] = None):
        self.client = client or OpenAI()
    
    def score_job(self, job: Job, profile: Profile) -> Job:
        """Score a job against a profile and add analysis."""
        
        # Build profile summary for matching
        profile_summary = self._build_profile_summary(profile)
        
        # Build job summary
        job_summary = self._build_job_summary(job)
        
        # Get AI analysis
        analysis = self._analyze_match(profile_summary, job_summary)
        
        # Update job with match data
        job.match_score = analysis.get("score", 0)
        job.match_analysis = analysis.get("summary", "")
        job.skill_matches = analysis.get("matching_skills", [])
        job.skill_gaps = analysis.get("skill_gaps", [])
        
        # Extract skills from description if not already done
        if not job.required_skills and analysis.get("required_skills"):
            job.required_skills = analysis["required_skills"]
        
        return job
    
    def score_jobs(self, jobs: list[Job], profile: Profile) -> list[Job]:
        """Score multiple jobs and sort by match."""
        scored_jobs = []
        
        for job in jobs:
            try:
                scored_job = self.score_job(job, profile)
                scored_jobs.append(scored_job)
            except Exception as e:
                print(f"Error scoring job {job.title}: {e}")
                job.match_score = 0
                scored_jobs.append(job)
        
        # Sort by match score descending
        scored_jobs.sort(key=lambda j: j.match_score or 0, reverse=True)
        
        return scored_jobs
    
    def _build_profile_summary(self, profile: Profile) -> str:
        """Build a text summary of the profile."""
        parts = [
            f"Name: {profile.name}",
            f"Location: {profile.location}",
        ]
        
        if profile.summary:
            parts.append(f"Summary: {profile.summary}")
        
        # Experience
        exp_strs = []
        for exp in profile.experience:
            exp_str = f"- {exp.title} at {exp.company} ({exp.start_date} - {exp.end_date or 'Present'})"
            if exp.highlights:
                exp_str += "\n  " + "\n  ".join(exp.highlights[:3])
            exp_strs.append(exp_str)
        
        if exp_strs:
            parts.append("Experience:\n" + "\n".join(exp_strs))
        
        # Education
        edu_strs = [
            f"- {edu.degree} from {edu.school} ({edu.year})"
            for edu in profile.education
        ]
        if edu_strs:
            parts.append("Education:\n" + "\n".join(edu_strs))
        
        # Skills
        all_skills = profile.get_all_skills()
        if all_skills:
            parts.append(f"Skills: {', '.join(all_skills)}")
        
        # Preferences
        if profile.target_roles:
            parts.append(f"Target roles: {', '.join(profile.target_roles)}")
        
        if profile.visa_sponsorship_needed:
            parts.append("Note: Requires visa sponsorship")
        
        return "\n\n".join(parts)
    
    def _build_job_summary(self, job: Job) -> str:
        """Build a text summary of the job."""
        parts = [
            f"Title: {job.title}",
            f"Company: {job.company}",
            f"Location: {job.location}",
        ]
        
        if job.salary_min and job.salary_max:
            parts.append(f"Salary: {job.salary_currency} {job.salary_min:,} - {job.salary_max:,}")
        
        if job.work_type:
            parts.append(f"Work type: {job.work_type.value}")
        
        if job.experience_level:
            parts.append(f"Level: {job.experience_level}")
        
        if job.description:
            parts.append(f"Description:\n{job.description[:2000]}")
        
        return "\n".join(parts)
    
    def _analyze_match(self, profile_summary: str, job_summary: str) -> dict:
        """Use AI to analyze the match between profile and job."""
        
        system_prompt = """You are a job matching expert. Analyze how well a candidate matches a job.

Return a JSON object with:
{
    "score": <0-100 integer, how well the candidate matches>,
    "summary": "<2-3 sentence summary of the match>",
    "matching_skills": ["skill1", "skill2", ...],
    "skill_gaps": ["missing skill 1", "missing skill 2", ...],
    "required_skills": ["skills mentioned in job description"],
    "strengths": ["key strength 1", "key strength 2"],
    "concerns": ["potential concern 1"],
    "recommendation": "<brief recommendation for the candidate>"
}

Scoring guide:
- 90-100: Excellent match, meets nearly all requirements
- 80-89: Strong match, meets most requirements
- 70-79: Good match, meets core requirements
- 60-69: Moderate match, meets some requirements
- 50-59: Weak match, significant gaps
- Below 50: Poor match, major misalignment

Be realistic but fair. Consider transferable skills."""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"CANDIDATE PROFILE:\n{profile_summary}\n\n---\n\nJOB POSTING:\n{job_summary}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        return json.loads(response.choices[0].message.content)


class CoverLetterGenerator:
    """Generates tailored cover letters."""
    
    def __init__(self, client: Optional[OpenAI] = None):
        self.client = client or OpenAI()
    
    def generate(
        self,
        job: Job,
        profile: Profile,
        tone: str = "professional",
        length: str = "medium"
    ) -> str:
        """Generate a tailored cover letter."""
        
        length_guide = {
            "short": "2-3 paragraphs, under 200 words",
            "medium": "3-4 paragraphs, 200-350 words",
            "long": "4-5 paragraphs, 350-500 words"
        }
        
        tone_guide = {
            "professional": "formal, polished, business-appropriate",
            "casual": "friendly but professional, conversational",
            "enthusiastic": "energetic, passionate, shows excitement"
        }
        
        # Build context
        profile_summary = self._build_profile_context(profile)
        job_summary = self._build_job_context(job)
        
        system_prompt = f"""You are an expert cover letter writer. Write compelling, tailored cover letters.

Guidelines:
- Tone: {tone_guide.get(tone, tone_guide['professional'])}
- Length: {length_guide.get(length, length_guide['medium'])}
- Always personalize to the specific job and company
- Highlight relevant experience and skills
- Show enthusiasm for the role without being sycophantic
- Address any potential concerns proactively but briefly
- End with a clear call to action
- Do NOT use clichés like "I am writing to apply" or "I believe I would be a great fit"
- Be specific about accomplishments with numbers when possible
- Show you've researched the company

Format:
- Start with the candidate's contact info header
- Include date and company address if known
- Use proper greeting (Dear Hiring Manager if name unknown)
- Body paragraphs
- Professional sign-off"""

        user_prompt = f"""Write a cover letter for this application:

CANDIDATE:
{profile_summary}

JOB:
{job_summary}

Focus on the most relevant experiences and create a compelling narrative."""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def _build_profile_context(self, profile: Profile) -> str:
        """Build profile context for cover letter generation."""
        parts = [
            f"Name: {profile.name}",
            f"Email: {profile.email}",
        ]
        
        if profile.phone:
            parts.append(f"Phone: {profile.phone}")
        
        if profile.location:
            parts.append(f"Location: {profile.location}")
        
        if profile.linkedin:
            parts.append(f"LinkedIn: {profile.linkedin}")
        
        if profile.summary:
            parts.append(f"\nProfessional Summary:\n{profile.summary}")
        
        # Key experiences
        exp_parts = []
        for exp in profile.experience[:3]:  # Top 3 experiences
            exp_str = f"\n{exp.title} at {exp.company} ({exp.start_date} - {exp.end_date or 'Present'})"
            if exp.highlights:
                for h in exp.highlights[:3]:
                    exp_str += f"\n- {h}"
            exp_parts.append(exp_str)
        
        if exp_parts:
            parts.append("\nKey Experience:" + "".join(exp_parts))
        
        # Skills
        all_skills = profile.get_all_skills()
        if all_skills:
            parts.append(f"\nSkills: {', '.join(all_skills[:15])}")
        
        return "\n".join(parts)
    
    def _build_job_context(self, job: Job) -> str:
        """Build job context for cover letter generation."""
        parts = [
            f"Title: {job.title}",
            f"Company: {job.company}",
            f"Location: {job.location}",
        ]
        
        if job.description:
            parts.append(f"\nJob Description:\n{job.description[:2500]}")
        
        if job.required_skills:
            parts.append(f"\nRequired Skills: {', '.join(job.required_skills)}")
        
        if job.skill_matches:
            parts.append(f"\nYour matching skills: {', '.join(job.skill_matches)}")
        
        if job.skill_gaps:
            parts.append(f"\nPotential gaps to address: {', '.join(job.skill_gaps)}")
        
        return "\n".join(parts)
