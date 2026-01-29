# 🎯 JobHunter AI

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green.svg)](https://openai.com/)

**Your AI-powered job hunting assistant.** Automatically finds relevant jobs, scores them against your profile, generates tailored cover letters, and tracks your applications.

## 🔥 Why JobHunter AI?

Job hunting is exhausting. You spend hours:
- Scrolling through job boards
- Reading descriptions to check if you're a fit
- Writing cover letters from scratch
- Tracking what you applied to

**JobHunter AI automates the grunt work so you can focus on what matters: preparing for interviews.**

```
$ jobhunter search "AI Engineer" --location "Dublin"

🔍 Found 47 jobs matching your criteria...

📊 Top Matches for Your Profile:

1. [98% Match] Senior ML Engineer @ Stripe
   💰 €120k-150k | 📍 Dublin | 🏢 Hybrid
   ✅ Strong match: Python, PyTorch, ML Systems
   ⚠️ Gap: Kubernetes (mentioned but you have Docker)
   
2. [94% Match] AI Engineer @ Intercom  
   💰 €100k-130k | 📍 Dublin | 🏢 Remote OK
   ✅ Strong match: NLP, RAG, Production ML
   
3. [91% Match] Data Scientist @ Google
   💰 Competitive | 📍 Dublin | 🏢 On-site
   ✅ Strong match: TensorFlow, Python, Statistics
   
Generate cover letters? [y/n]: y
✍️ Generating tailored cover letters...
✅ Saved to ./applications/
```

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Smart Job Search** | Search across multiple job boards simultaneously |
| 🎯 **AI Matching** | Score jobs against your resume using LLM analysis |
| ✍️ **Cover Letter Gen** | Generate tailored cover letters for each position |
| 📊 **Gap Analysis** | Identify skill gaps and suggest improvements |
| 📁 **Application Tracker** | Track status, deadlines, follow-ups |
| 🌐 **Multi-Source** | LinkedIn, Indeed, Glassdoor, company career pages |
| 🤖 **Auto-Apply** | Browser automation for one-click applications |

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/edwiniac/jobhunter-ai.git
cd jobhunter-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up API key
export OPENAI_API_KEY="your-key"
```

### Set Up Your Profile

```bash
# Interactive profile setup
jobhunter profile setup

# Or import from resume
jobhunter profile import resume.pdf
```

### Start Hunting

```bash
# Search for jobs
jobhunter search "Machine Learning Engineer" --location "Dublin, Ireland"

# Search with filters
jobhunter search "AI Engineer" --remote --min-salary 80000 --experience mid

# Get job recommendations based on your profile
jobhunter recommend

# Generate cover letter for a specific job
jobhunter cover "https://linkedin.com/jobs/view/12345"

# Track an application
jobhunter track add "Stripe" "ML Engineer" --status applied --deadline 2026-02-15
```

## 🛠️ CLI Commands

```bash
# Profile Management
jobhunter profile setup          # Interactive profile creation
jobhunter profile import FILE    # Import from resume (PDF/DOCX)
jobhunter profile show           # Display current profile
jobhunter profile edit           # Edit profile

# Job Search
jobhunter search QUERY           # Search for jobs
jobhunter recommend              # Get AI recommendations
jobhunter analyze URL            # Analyze a specific job posting

# Applications
jobhunter cover URL              # Generate cover letter
jobhunter apply URL              # Auto-apply (with browser automation)
jobhunter track list             # List all tracked applications
jobhunter track add              # Add application manually
jobhunter track update ID        # Update application status

# Utilities
jobhunter stats                  # Show job hunt statistics
jobhunter export                 # Export data to CSV/JSON
```

## 🧠 How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                        JobHunter AI                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐                           ┌──────────────┐   │
│  │    Your      │                           │     Job      │   │
│  │   Profile    │                           │   Listings   │   │
│  └──────┬───────┘                           └──────┬───────┘   │
│         │                                          │            │
│         │    ┌────────────────────────────┐       │            │
│         └───▶│      AI Matching Engine     │◀─────┘            │
│              │   (GPT-4 Analysis)          │                    │
│              └─────────────┬──────────────┘                    │
│                            │                                    │
│              ┌─────────────▼──────────────┐                    │
│              │     Match Score + Analysis  │                    │
│              │  • Skill alignment          │                    │
│              │  • Experience fit           │                    │
│              │  • Gap identification       │                    │
│              └─────────────┬──────────────┘                    │
│                            │                                    │
│         ┌──────────────────┼──────────────────┐                │
│         ▼                  ▼                  ▼                │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐           │
│  │   Cover    │    │Application │    │   Apply    │           │
│  │  Letter    │    │  Tracker   │    │   Agent    │           │
│  │ Generator  │    │            │    │ (Browser)  │           │
│  └────────────┘    └────────────┘    └────────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 📋 Profile Structure

Your profile contains:

```yaml
# ~/.jobhunter/profile.yaml
personal:
  name: "Edwin Isac"
  email: "edwinisac007@gmail.com"
  phone: "+353 894-108-327"
  location: "Dublin, Ireland"
  
summary: |
  AI Engineer with 3.5 years of experience building and deploying 
  machine learning models. Expertise in NLP, Computer Vision, and 
  production ML systems.

experience:
  - title: "Data Scientist"
    company: "Globussoft Technologies"
    duration: "Sep 2021 - Feb 2023"
    highlights:
      - "Built brand detection system using TensorFlow"
      - "Created reverse image search handling 10K+ daily queries"

skills:
  languages: [Python, R, SQL]
  ml_frameworks: [TensorFlow, PyTorch, Scikit-learn, Hugging Face]
  tools: [Docker, AWS, Flask, Kafka, Grafana]
  domains: [NLP, Computer Vision, Time Series, RAG]

education:
  - degree: "MSc Data & Computational Science"
    school: "University College Dublin"
    year: 2025

preferences:
  roles: ["AI Engineer", "ML Engineer", "Data Scientist"]
  locations: ["Dublin", "Remote"]
  salary_min: 70000
  work_type: ["remote", "hybrid"]
  visa_sponsorship: true  # Important for filtering
```

## 🎯 Match Scoring

JobHunter AI analyzes jobs on multiple dimensions:

| Factor | Weight | Description |
|--------|--------|-------------|
| **Skills Match** | 35% | How well your skills align with requirements |
| **Experience Level** | 25% | Years of experience vs. job requirements |
| **Domain Fit** | 20% | Industry/domain relevance |
| **Preferences** | 15% | Location, salary, work type alignment |
| **Growth Potential** | 5% | Learning opportunities identified |

## ✍️ Cover Letter Generation

JobHunter AI generates tailored cover letters by:

1. **Analyzing the job posting** — Extracting key requirements and company info
2. **Matching your experience** — Finding relevant accomplishments
3. **Highlighting fit** — Emphasizing your strongest alignments
4. **Addressing gaps** — Framing any gaps positively
5. **Company research** — Including company-specific details

```bash
$ jobhunter cover "https://linkedin.com/jobs/view/12345" --tone professional

✍️ Generating cover letter for: ML Engineer @ Stripe

📄 Cover Letter Generated:

Dear Hiring Manager,

I am writing to express my strong interest in the Machine Learning Engineer 
position at Stripe. With 3.5 years of experience building production ML 
systems and a recent MSc in Data Science from UCD, I am excited about the 
opportunity to contribute to Stripe's mission of increasing the GDP of 
the internet...

[Full letter saved to ./applications/stripe_ml_engineer_cover.md]
```

## 📊 Application Tracking

```bash
$ jobhunter track list

📋 Your Applications (12 total)

┌─────────────┬──────────────────┬────────────┬────────────┬──────────┐
│ Company     │ Role             │ Status     │ Applied    │ Next     │
├─────────────┼──────────────────┼────────────┼────────────┼──────────┤
│ Stripe      │ ML Engineer      │ Interview  │ Jan 15     │ Feb 2    │
│ Intercom    │ AI Engineer      │ Applied    │ Jan 20     │ Follow up│
│ Google      │ Data Scientist   │ Screening  │ Jan 18     │ Pending  │
│ Meta        │ ML Engineer      │ Rejected   │ Jan 10     │ -        │
└─────────────┴──────────────────┴────────────┴────────────┴──────────┘

📈 Stats: 12 applied | 3 interviewing | 1 rejected | 8 pending
```

## 🔧 Configuration

```yaml
# ~/.jobhunter/config.yaml
llm:
  provider: openai
  model: gpt-4o
  temperature: 0.7

search:
  sources:
    - linkedin
    - indeed
    - glassdoor
    - greenhouse
    - lever
  max_results_per_source: 50
  
matching:
  min_score: 70  # Only show jobs with 70%+ match
  
cover_letter:
  tone: professional  # professional, casual, enthusiastic
  length: medium      # short, medium, long
```

## 🌐 Supported Job Sources

| Source | Method | Notes |
|--------|--------|-------|
| LinkedIn | API + Scraping | Requires cookies for full access |
| Indeed | Scraping | Rate limited |
| Glassdoor | Scraping | Rate limited |
| Greenhouse | API | Many startups use this |
| Lever | API | Many tech companies |
| Company Sites | Scraping | Custom per company |

## ⚠️ Disclaimer

- This tool is for **personal use** in your job search
- Respect rate limits and terms of service of job boards
- Auto-apply features should be used responsibly
- Always review generated cover letters before sending

## 🗺️ Roadmap

- [x] Core job search
- [x] AI matching engine
- [x] Cover letter generation
- [x] Application tracking
- [ ] Browser automation (auto-apply)
- [ ] Email integration (track responses)
- [ ] Interview prep assistant
- [ ] Salary negotiation helper
- [ ] Chrome extension

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built for job seekers, by someone who's been there.** Good luck with your search! 🍀
