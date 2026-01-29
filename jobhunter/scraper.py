"""Job scraping from various sources."""

import hashlib
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from .models import Job, WorkType


class JobScraper(ABC):
    """Base class for job scrapers."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
    
    @abstractmethod
    def search(self, query: str, location: str = "", **kwargs) -> list[Job]:
        """Search for jobs."""
        pass
    
    @abstractmethod
    def get_job_details(self, job_id: str) -> Optional[Job]:
        """Get detailed job information."""
        pass
    
    def _generate_id(self, *args) -> str:
        """Generate a unique ID from arguments."""
        content = "|".join(str(a) for a in args)
        return hashlib.md5(content.encode()).hexdigest()[:12]


class LinkedInScraper(JobScraper):
    """Scraper for LinkedIn jobs."""
    
    BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    
    def search(
        self, 
        query: str, 
        location: str = "",
        remote: bool = False,
        experience_level: Optional[str] = None,
        max_results: int = 25
    ) -> list[Job]:
        """Search LinkedIn for jobs."""
        jobs = []
        
        params = {
            "keywords": query,
            "location": location,
            "start": 0,
            "sortBy": "R",  # Relevance
        }
        
        if remote:
            params["f_WT"] = "2"  # Remote filter
        
        if experience_level:
            level_map = {
                "entry": "1",
                "mid": "2", 
                "senior": "3",
                "director": "4",
                "executive": "5",
            }
            if experience_level.lower() in level_map:
                params["f_E"] = level_map[experience_level.lower()]
        
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            job_cards = soup.find_all("div", class_="base-card")
            
            for card in job_cards[:max_results]:
                try:
                    title_elem = card.find("h3", class_="base-search-card__title")
                    company_elem = card.find("h4", class_="base-search-card__subtitle")
                    location_elem = card.find("span", class_="job-search-card__location")
                    link_elem = card.find("a", class_="base-card__full-link")
                    
                    if not all([title_elem, company_elem, link_elem]):
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    company = company_elem.get_text(strip=True)
                    job_location = location_elem.get_text(strip=True) if location_elem else location
                    url = link_elem.get("href", "").split("?")[0]
                    
                    job_id = self._generate_id("linkedin", url)
                    
                    jobs.append(Job(
                        id=job_id,
                        title=title,
                        company=company,
                        location=job_location,
                        description="",  # Needs separate fetch
                        url=url,
                        source="linkedin",
                    ))
                except Exception:
                    continue
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"LinkedIn search error: {e}")
        
        return jobs
    
    def get_job_details(self, job_id: str) -> Optional[Job]:
        """Get detailed job info from LinkedIn."""
        # Would need to fetch individual job page
        # Simplified for now
        return None


class IndeedScraper(JobScraper):
    """Scraper for Indeed jobs."""
    
    BASE_URL = "https://www.indeed.com/jobs"
    
    def search(
        self,
        query: str,
        location: str = "",
        remote: bool = False,
        max_results: int = 25
    ) -> list[Job]:
        """Search Indeed for jobs."""
        jobs = []
        
        params = {
            "q": query,
            "l": location,
            "sort": "date",
        }
        
        if remote:
            params["remotejob"] = "032b3046-06a3-4876-8dfd-474eb5e7ed11"
        
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            job_cards = soup.find_all("div", class_="job_seen_beacon")
            
            for card in job_cards[:max_results]:
                try:
                    title_elem = card.find("h2", class_="jobTitle")
                    company_elem = card.find("span", {"data-testid": "company-name"})
                    location_elem = card.find("div", {"data-testid": "text-location"})
                    
                    if not all([title_elem, company_elem]):
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    company = company_elem.get_text(strip=True)
                    job_location = location_elem.get_text(strip=True) if location_elem else location
                    
                    # Get job key for URL
                    job_key = card.find("a", {"data-jk": True})
                    if job_key:
                        jk = job_key.get("data-jk", "")
                        url = f"https://www.indeed.com/viewjob?jk={jk}"
                    else:
                        url = ""
                    
                    job_id = self._generate_id("indeed", title, company)
                    
                    jobs.append(Job(
                        id=job_id,
                        title=title,
                        company=company,
                        location=job_location,
                        description="",
                        url=url,
                        source="indeed",
                    ))
                except Exception:
                    continue
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Indeed search error: {e}")
        
        return jobs
    
    def get_job_details(self, job_id: str) -> Optional[Job]:
        return None


class GreenhouseScraper(JobScraper):
    """Scraper for Greenhouse job boards."""
    
    def __init__(self, company_boards: list[str] = None):
        super().__init__()
        # Popular tech companies using Greenhouse
        self.company_boards = company_boards or [
            "stripe",
            "intercom",
            "notion",
            "figma",
            "airbnb",
            "coinbase",
            "databricks",
            "discord",
        ]
    
    def search(
        self,
        query: str,
        location: str = "",
        max_results: int = 25
    ) -> list[Job]:
        """Search Greenhouse job boards."""
        jobs = []
        
        for company in self.company_boards:
            try:
                url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
                response = self.session.get(url, timeout=10)
                
                if response.status_code != 200:
                    continue
                
                data = response.json()
                
                for job_data in data.get("jobs", []):
                    title = job_data.get("title", "")
                    job_location = job_data.get("location", {}).get("name", "")
                    
                    # Filter by query and location
                    if query.lower() not in title.lower():
                        continue
                    if location and location.lower() not in job_location.lower():
                        continue
                    
                    job_id = self._generate_id("greenhouse", company, job_data.get("id"))
                    
                    jobs.append(Job(
                        id=job_id,
                        title=title,
                        company=company.title(),
                        location=job_location,
                        description=job_data.get("content", ""),
                        url=job_data.get("absolute_url", ""),
                        source="greenhouse",
                    ))
                    
                    if len(jobs) >= max_results:
                        break
                
                time.sleep(0.5)
                
            except Exception as e:
                continue
        
        return jobs[:max_results]
    
    def get_job_details(self, job_id: str) -> Optional[Job]:
        return None


class JobSearchAggregator:
    """Aggregates results from multiple job sources."""
    
    def __init__(self):
        self.scrapers = {
            "linkedin": LinkedInScraper(),
            "indeed": IndeedScraper(),
            "greenhouse": GreenhouseScraper(),
        }
    
    def search(
        self,
        query: str,
        location: str = "",
        sources: Optional[list[str]] = None,
        remote: bool = False,
        max_per_source: int = 20
    ) -> list[Job]:
        """Search across all sources."""
        all_jobs = []
        
        sources = sources or list(self.scrapers.keys())
        
        for source in sources:
            if source not in self.scrapers:
                continue
            
            scraper = self.scrapers[source]
            
            try:
                jobs = scraper.search(
                    query=query,
                    location=location,
                    remote=remote,
                    max_results=max_per_source
                )
                all_jobs.extend(jobs)
            except Exception as e:
                print(f"Error searching {source}: {e}")
        
        # Deduplicate by title + company
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            key = f"{job.title.lower()}|{job.company.lower()}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs
