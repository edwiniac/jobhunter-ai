#!/usr/bin/env python3
"""CLI interface for JobHunter AI."""

import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from openai import OpenAI

from .models import Profile, ApplicationStatus, WorkType
from .profile import ProfileManager, parse_resume_with_llm, extract_text_from_pdf, extract_text_from_docx
from .scraper import JobSearchAggregator
from .matcher import JobMatcher, CoverLetterGenerator
from .tracker import ApplicationTracker


console = Console()


def get_client():
    """Get OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("[red]Error: OPENAI_API_KEY environment variable not set[/red]")
        sys.exit(1)
    return OpenAI(api_key=api_key)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """🎯 JobHunter AI - Your AI-powered job hunting assistant."""
    pass


# ============ Profile Commands ============

@cli.group()
def profile():
    """Manage your profile."""
    pass


@profile.command("setup")
def profile_setup():
    """Interactive profile setup."""
    console.print(Panel.fit(
        "[bold blue]Profile Setup[/bold blue]\n"
        "Let's set up your job hunting profile.",
        border_style="blue"
    ))
    
    manager = ProfileManager()
    
    # Basic info
    name = click.prompt("Full name")
    email = click.prompt("Email")
    phone = click.prompt("Phone (optional)", default="", show_default=False)
    location = click.prompt("Location (e.g., Dublin, Ireland)")
    
    # Summary
    console.print("\n[dim]Write a brief professional summary (press Enter twice to finish):[/dim]")
    summary_lines = []
    while True:
        line = input()
        if line == "":
            break
        summary_lines.append(line)
    summary = " ".join(summary_lines) if summary_lines else None
    
    # Skills
    skills_input = click.prompt("\nSkills (comma-separated)", default="")
    skills = [s.strip() for s in skills_input.split(",") if s.strip()]
    
    # Target roles
    roles_input = click.prompt("Target job titles (comma-separated)", default="")
    target_roles = [r.strip() for r in roles_input.split(",") if r.strip()]
    
    # Work preferences
    work_types = []
    if click.confirm("Open to remote work?", default=True):
        work_types.append(WorkType.REMOTE)
    if click.confirm("Open to hybrid work?", default=True):
        work_types.append(WorkType.HYBRID)
    if click.confirm("Open to on-site work?", default=True):
        work_types.append(WorkType.ONSITE)
    
    # Visa
    visa_needed = click.confirm("Do you need visa sponsorship?", default=False)
    
    # Create profile
    new_profile = Profile(
        name=name,
        email=email,
        phone=phone if phone else None,
        location=location,
        summary=summary,
        skills=skills,
        target_roles=target_roles,
        work_types=work_types,
        visa_sponsorship_needed=visa_needed,
    )
    
    manager.save(new_profile)
    console.print("\n[green]✓ Profile saved![/green]")
    console.print(f"[dim]Location: {manager.profile_path}[/dim]")


@profile.command("import")
@click.argument("file_path", type=click.Path(exists=True))
def profile_import(file_path):
    """Import profile from resume (PDF or DOCX)."""
    path = Path(file_path)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Parsing resume...", total=None)
        
        # Extract text based on file type
        if path.suffix.lower() == ".pdf":
            text = extract_text_from_pdf(str(path))
        elif path.suffix.lower() in [".docx", ".doc"]:
            text = extract_text_from_docx(str(path))
        else:
            console.print(f"[red]Unsupported file type: {path.suffix}[/red]")
            return
        
        progress.update(task, description="Analyzing with AI...")
        
        client = get_client()
        new_profile = parse_resume_with_llm(text, client)
        
        progress.update(task, description="Saving profile...")
        
        manager = ProfileManager()
        manager.save(new_profile)
    
    console.print("\n[green]✓ Profile imported successfully![/green]")
    console.print(f"\n[bold]Name:[/bold] {new_profile.name}")
    console.print(f"[bold]Email:[/bold] {new_profile.email}")
    console.print(f"[bold]Skills:[/bold] {', '.join(new_profile.get_all_skills()[:10])}")
    console.print(f"\n[dim]Edit with: jobhunter profile edit[/dim]")


@profile.command("show")
def profile_show():
    """Display current profile."""
    manager = ProfileManager()
    user_profile = manager.load()
    
    if not user_profile:
        console.print("[yellow]No profile found. Run 'jobhunter profile setup' first.[/yellow]")
        return
    
    # Display profile
    console.print(Panel.fit(f"[bold blue]{user_profile.name}[/bold blue]", border_style="blue"))
    
    table = Table(show_header=False, box=None)
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    
    table.add_row("📧 Email", user_profile.email)
    if user_profile.phone:
        table.add_row("📱 Phone", user_profile.phone)
    if user_profile.location:
        table.add_row("📍 Location", user_profile.location)
    
    console.print(table)
    
    if user_profile.summary:
        console.print(f"\n[bold]Summary:[/bold]\n{user_profile.summary}")
    
    if user_profile.experience:
        console.print("\n[bold]Experience:[/bold]")
        for exp in user_profile.experience:
            console.print(f"  • {exp.title} at {exp.company}")
    
    if user_profile.get_all_skills():
        console.print(f"\n[bold]Skills:[/bold] {', '.join(user_profile.get_all_skills())}")
    
    if user_profile.target_roles:
        console.print(f"\n[bold]Target Roles:[/bold] {', '.join(user_profile.target_roles)}")


# ============ Search Commands ============

@cli.command("search")
@click.argument("query")
@click.option("--location", "-l", default="", help="Location filter")
@click.option("--remote", "-r", is_flag=True, help="Remote jobs only")
@click.option("--limit", "-n", default=20, help="Maximum results")
@click.option("--score", "-s", is_flag=True, help="Score jobs against your profile")
def search(query, location, remote, limit, score):
    """Search for jobs."""
    manager = ProfileManager()
    user_profile = manager.load()
    
    if score and not user_profile:
        console.print("[yellow]No profile found. Run 'jobhunter profile setup' first to enable scoring.[/yellow]")
        score = False
    
    aggregator = JobSearchAggregator()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Searching job boards...", total=None)
        
        jobs = aggregator.search(
            query=query,
            location=location,
            remote=remote,
            max_per_source=limit // 3 + 1
        )
        
        if score and jobs and user_profile:
            progress.update(task, description=f"Scoring {len(jobs)} jobs...")
            client = get_client()
            matcher = JobMatcher(client)
            jobs = matcher.score_jobs(jobs[:limit], user_profile)
    
    if not jobs:
        console.print("[yellow]No jobs found. Try different keywords or location.[/yellow]")
        return
    
    console.print(f"\n[green]Found {len(jobs)} jobs[/green]\n")
    
    # Display results
    table = Table(title=f"Jobs matching '{query}'")
    table.add_column("#", style="dim")
    table.add_column("Title", style="bold")
    table.add_column("Company", style="cyan")
    table.add_column("Location")
    if score:
        table.add_column("Match", style="green")
    table.add_column("Source", style="dim")
    
    for i, job in enumerate(jobs[:limit], 1):
        row = [
            str(i),
            job.title[:40],
            job.company[:25],
            job.location[:20],
        ]
        if score:
            score_str = f"{job.match_score}%" if job.match_score else "-"
            row.append(score_str)
        row.append(job.source)
        table.add_row(*row)
    
    console.print(table)
    
    # Show top match analysis if scored
    if score and jobs[0].match_analysis:
        console.print(f"\n[bold]Top Match Analysis ({jobs[0].title} @ {jobs[0].company}):[/bold]")
        console.print(f"[green]✓ Matching skills:[/green] {', '.join(jobs[0].skill_matches[:5])}")
        if jobs[0].skill_gaps:
            console.print(f"[yellow]⚠ Gaps:[/yellow] {', '.join(jobs[0].skill_gaps[:3])}")
        console.print(f"\n{jobs[0].match_analysis}")


@cli.command("recommend")
@click.option("--limit", "-n", default=10, help="Number of recommendations")
def recommend(limit):
    """Get job recommendations based on your profile."""
    manager = ProfileManager()
    user_profile = manager.load()
    
    if not user_profile:
        console.print("[red]No profile found. Run 'jobhunter profile setup' first.[/red]")
        return
    
    if not user_profile.target_roles:
        console.print("[yellow]No target roles set. Update your profile with target job titles.[/yellow]")
        return
    
    aggregator = JobSearchAggregator()
    client = get_client()
    matcher = JobMatcher(client)
    
    all_jobs = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Search for each target role
        for role in user_profile.target_roles[:3]:
            task = progress.add_task(f"Searching for '{role}'...", total=None)
            
            jobs = aggregator.search(
                query=role,
                location=user_profile.location or "",
                max_per_source=10
            )
            all_jobs.extend(jobs)
            progress.remove_task(task)
        
        # Score all jobs
        task = progress.add_task(f"Analyzing {len(all_jobs)} jobs...", total=None)
        scored_jobs = matcher.score_jobs(all_jobs, user_profile)
    
    # Get top recommendations
    top_jobs = [j for j in scored_jobs if (j.match_score or 0) >= 60][:limit]
    
    if not top_jobs:
        console.print("[yellow]No strong matches found. Try updating your profile or target roles.[/yellow]")
        return
    
    console.print(f"\n[bold green]🎯 Top {len(top_jobs)} Recommendations for You[/bold green]\n")
    
    for i, job in enumerate(top_jobs, 1):
        console.print(f"[bold]{i}. [{job.match_score}% Match] {job.title}[/bold]")
        console.print(f"   🏢 {job.company} | 📍 {job.location}")
        if job.skill_matches:
            console.print(f"   [green]✓[/green] {', '.join(job.skill_matches[:4])}")
        if job.skill_gaps:
            console.print(f"   [yellow]⚠[/yellow] Gaps: {', '.join(job.skill_gaps[:2])}")
        console.print()


# ============ Cover Letter Commands ============

@cli.command("cover")
@click.argument("job_url")
@click.option("--tone", "-t", default="professional", type=click.Choice(["professional", "casual", "enthusiastic"]))
@click.option("--length", "-l", default="medium", type=click.Choice(["short", "medium", "long"]))
@click.option("--output", "-o", help="Output file path")
def cover(job_url, tone, length, output):
    """Generate a cover letter for a job."""
    manager = ProfileManager()
    user_profile = manager.load()
    
    if not user_profile:
        console.print("[red]No profile found. Run 'jobhunter profile setup' first.[/red]")
        return
    
    # For now, create a placeholder job from URL
    # In full implementation, would scrape the job details
    from .models import Job
    import hashlib
    
    job_id = hashlib.md5(job_url.encode()).hexdigest()[:8]
    
    console.print("[dim]Note: Paste the job description when prompted for best results.[/dim]")
    console.print("\n[bold]Paste the job description (press Enter twice when done):[/bold]")
    
    description_lines = []
    while True:
        line = input()
        if line == "":
            if description_lines:
                break
        else:
            description_lines.append(line)
    
    description = "\n".join(description_lines)
    
    # Extract title and company (simple heuristics)
    lines = description.split("\n")
    title = lines[0][:50] if lines else "Position"
    company = "Company"  # Would be extracted properly
    
    job = Job(
        id=job_id,
        title=title,
        company=company,
        location="",
        description=description,
        url=job_url,
        source="manual"
    )
    
    client = get_client()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # First score the job to get skill analysis
        task = progress.add_task("Analyzing job match...", total=None)
        matcher = JobMatcher(client)
        job = matcher.score_job(job, user_profile)
        
        # Generate cover letter
        progress.update(task, description="Writing cover letter...")
        generator = CoverLetterGenerator(client)
        letter = generator.generate(job, user_profile, tone=tone, length=length)
    
    console.print("\n" + "="*60 + "\n")
    console.print(Markdown(letter))
    console.print("\n" + "="*60)
    
    # Save if output specified
    if output:
        with open(output, "w") as f:
            f.write(letter)
        console.print(f"\n[green]✓ Saved to {output}[/green]")
    else:
        # Offer to save
        if click.confirm("\nSave cover letter?"):
            default_name = f"cover_letter_{job_id}.md"
            filename = click.prompt("Filename", default=default_name)
            with open(filename, "w") as f:
                f.write(letter)
            console.print(f"[green]✓ Saved to {filename}[/green]")


# ============ Tracking Commands ============

@cli.group()
def track():
    """Track your applications."""
    pass


@track.command("list")
@click.option("--status", "-s", type=click.Choice([s.value for s in ApplicationStatus]), help="Filter by status")
def track_list(status):
    """List all tracked applications."""
    tracker = ApplicationTracker()
    
    status_filter = ApplicationStatus(status) if status else None
    applications = tracker.list_all(status_filter)
    
    if not applications:
        console.print("[dim]No applications tracked yet.[/dim]")
        return
    
    table = Table(title="Your Applications")
    table.add_column("ID", style="dim")
    table.add_column("Company", style="cyan")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Updated")
    
    status_colors = {
        "saved": "dim",
        "applied": "blue",
        "screening": "yellow",
        "interview": "green",
        "offer": "bold green",
        "rejected": "red",
        "withdrawn": "dim",
    }
    
    for app in applications:
        status_style = status_colors.get(app["status"], "")
        table.add_row(
            app["id"],
            app["company"][:20],
            app["title"][:30],
            f"[{status_style}]{app['status']}[/{status_style}]",
            app["updated_at"][:10],
        )
    
    console.print(table)
    
    # Stats
    stats = tracker.get_stats()
    console.print(f"\n[dim]Total: {stats['total']} | " + 
                  " | ".join(f"{k}: {v}" for k, v in stats["by_status"].items()) + "[/dim]")


@track.command("add")
@click.argument("company")
@click.argument("title")
@click.option("--status", "-s", default="applied", type=click.Choice([s.value for s in ApplicationStatus]))
@click.option("--url", "-u", default="", help="Job posting URL")
def track_add(company, title, status, url):
    """Add a new application to track."""
    from .models import Job
    import uuid
    
    job = Job(
        id=str(uuid.uuid4())[:8],
        title=title,
        company=company,
        location="",
        description="",
        url=url,
        source="manual",
    )
    
    tracker = ApplicationTracker()
    application = tracker.add(job, ApplicationStatus(status))
    
    console.print(f"[green]✓ Added application: {title} @ {company}[/green]")
    console.print(f"[dim]ID: {application.id}[/dim]")


@track.command("update")
@click.argument("app_id")
@click.argument("new_status", type=click.Choice([s.value for s in ApplicationStatus]))
@click.option("--notes", "-n", default="", help="Notes about the update")
def track_update(app_id, new_status, notes):
    """Update application status."""
    tracker = ApplicationTracker()
    application = tracker.update_status(app_id, ApplicationStatus(new_status), notes)
    
    if application:
        console.print(f"[green]✓ Updated {app_id} to '{new_status}'[/green]")
    else:
        console.print(f"[red]Application {app_id} not found[/red]")


@track.command("stats")
def track_stats():
    """Show application statistics."""
    tracker = ApplicationTracker()
    stats = tracker.get_stats()
    
    console.print(Panel.fit("[bold]📊 Application Statistics[/bold]", border_style="blue"))
    
    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold")
    
    table.add_row("Total Applications", str(stats["total"]))
    
    for status, count in stats["by_status"].items():
        table.add_row(f"  {status.title()}", str(count))
    
    console.print(table)
    
    # Calculate rates
    if stats["total"] > 0:
        interview_rate = stats["by_status"].get("interview", 0) / stats["total"] * 100
        console.print(f"\n[dim]Interview rate: {interview_rate:.1f}%[/dim]")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
