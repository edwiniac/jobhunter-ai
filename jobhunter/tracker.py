"""Application tracking for JobHunter AI."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Application, ApplicationStatus, Job


class ApplicationTracker:
    """Tracks job applications."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path.home() / ".jobhunter" / "applications"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.data_dir / "index.json"
        self._load_index()
    
    def _load_index(self):
        """Load application index."""
        if self.index_path.exists():
            with open(self.index_path, "r") as f:
                self.index = json.load(f)
        else:
            self.index = {"applications": {}}
    
    def _save_index(self):
        """Save application index."""
        with open(self.index_path, "w") as f:
            json.dump(self.index, f, indent=2, default=str)
    
    def add(self, job: Job, status: ApplicationStatus = ApplicationStatus.SAVED) -> Application:
        """Add a new application."""
        app_id = str(uuid.uuid4())[:8]
        
        application = Application(
            id=app_id,
            job=job,
            status=status,
            applied_date=datetime.now() if status != ApplicationStatus.SAVED else None,
        )
        
        application.add_event("created", f"Application created with status: {status.value}")
        
        # Save to index
        self.index["applications"][app_id] = {
            "id": app_id,
            "job_id": job.id,
            "company": job.company,
            "title": job.title,
            "status": status.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        self._save_index()
        
        # Save full application data
        self._save_application(application)
        
        return application
    
    def _save_application(self, application: Application):
        """Save full application data."""
        app_path = self.data_dir / f"{application.id}.json"
        with open(app_path, "w") as f:
            json.dump(application.to_dict(), f, indent=2, default=str)
    
    def get(self, app_id: str) -> Optional[Application]:
        """Get an application by ID."""
        if app_id not in self.index["applications"]:
            return None
        
        app_path = self.data_dir / f"{app_id}.json"
        if not app_path.exists():
            return None
        
        with open(app_path, "r") as f:
            data = json.load(f)
        
        # Reconstruct Application object
        job_data = data["job"]
        job = Job(
            id=job_data["id"],
            title=job_data["title"],
            company=job_data["company"],
            location=job_data["location"],
            description=job_data["description"],
            url=job_data["url"],
            source=job_data["source"],
        )
        
        return Application(
            id=data["id"],
            job=job,
            status=ApplicationStatus(data["status"]),
            applied_date=datetime.fromisoformat(data["applied_date"]) if data.get("applied_date") else None,
            cover_letter_path=data.get("cover_letter_path"),
            notes=data.get("notes", ""),
            events=data.get("events", []),
        )
    
    def update_status(self, app_id: str, status: ApplicationStatus, notes: str = "") -> Optional[Application]:
        """Update application status."""
        application = self.get(app_id)
        if not application:
            return None
        
        old_status = application.status
        application.status = status
        application.add_event("status_change", f"Status changed from {old_status.value} to {status.value}. {notes}")
        
        # Update index
        self.index["applications"][app_id]["status"] = status.value
        self.index["applications"][app_id]["updated_at"] = datetime.now().isoformat()
        self._save_index()
        
        # Save application
        self._save_application(application)
        
        return application
    
    def list_all(self, status_filter: Optional[ApplicationStatus] = None) -> list[dict]:
        """List all applications."""
        applications = list(self.index["applications"].values())
        
        if status_filter:
            applications = [a for a in applications if a["status"] == status_filter.value]
        
        # Sort by updated_at descending
        applications.sort(key=lambda a: a.get("updated_at", ""), reverse=True)
        
        return applications
    
    def get_stats(self) -> dict:
        """Get application statistics."""
        apps = self.index["applications"].values()
        
        stats = {
            "total": len(apps),
            "by_status": {},
        }
        
        for status in ApplicationStatus:
            count = sum(1 for a in apps if a["status"] == status.value)
            if count > 0:
                stats["by_status"][status.value] = count
        
        return stats
    
    def delete(self, app_id: str) -> bool:
        """Delete an application."""
        if app_id not in self.index["applications"]:
            return False
        
        # Remove from index
        del self.index["applications"][app_id]
        self._save_index()
        
        # Remove file
        app_path = self.data_dir / f"{app_id}.json"
        if app_path.exists():
            app_path.unlink()
        
        return True
    
    def search(self, query: str) -> list[dict]:
        """Search applications by company or title."""
        query = query.lower()
        results = []
        
        for app in self.index["applications"].values():
            if query in app["company"].lower() or query in app["title"].lower():
                results.append(app)
        
        return results
