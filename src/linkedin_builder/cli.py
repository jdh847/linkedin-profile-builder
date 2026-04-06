"""CLI entry point for linkedin-profile-builder."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import __version__
from .models import LinkedInProfile
from .parser import extract_text_from_pdf, extract_text_from_multiple
from .generator import generate_profile
from .offline import generate_offline
from .output import to_json, to_txt, to_html

console = Console()


@click.group()
@click.version_option(__version__)
def main():
    """LinkedIn Profile Builder — generate a complete LinkedIn profile from your resume PDF."""
    pass


@main.command()
@click.argument("resume", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--api-key", envvar="ANTHROPIC_API_KEY", help="Anthropic API key")
@click.option("--model", default="claude-sonnet-4-20250514", help="Claude model to use")
@click.option(
    "--format", "fmt",
    type=click.Choice(["all", "json", "txt", "html"]),
    default="all",
    help="Output format (default: all)",
)
@click.option("--output-dir", "-o", default="./output", help="Output directory")
@click.option("--instructions", "-i", default="", help="Extra instructions (e.g., target role, location)")
@click.option("--offline", is_flag=True, help="Use rule-based extraction (no API key needed)")
def build(resume, api_key, model, fmt, output_dir, instructions, offline):
    """Generate a LinkedIn profile from one or more resume PDFs.

    Examples:

        linkedin-builder build resume.pdf

        linkedin-builder build cv1.pdf cv2.pdf --format txt

        linkedin-builder build resume.pdf -i "Target: quant roles in London"
    """
    mode_label = "offline (rule-based)" if offline else f"Claude ({model})"
    console.print(
        Panel(
            "[bold]LinkedIn Profile Builder[/bold]\n"
            f"Resume(s): {', '.join(str(r) for r in resume)}\n"
            f"Mode: {mode_label}\n"
            f"Output: {output_dir}/",
            title="Configuration",
            border_style="blue",
        )
    )

    # Step 1: Parse PDFs
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Parsing resume PDF(s)...", total=None)

        if len(resume) == 1:
            resume_text = extract_text_from_pdf(resume[0])
        else:
            resume_text = extract_text_from_multiple(list(resume))

        progress.update(task, description=f"[green]Parsed {len(resume)} PDF(s) — {len(resume_text)} chars")
        progress.stop()

    console.print(f"\n[dim]Extracted {len(resume_text)} characters from resume[/dim]\n")

    # Step 2: Generate profile
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        gen_label = "Extracting profile (offline)..." if offline else "Generating LinkedIn profile with Claude..."
        task = progress.add_task(gen_label, total=None)

        try:
            if offline:
                profile = generate_offline(resume_text)
            else:
                profile = generate_profile(
                    resume_text,
                    api_key=api_key,
                    model=model,
                    extra_instructions=instructions,
                )
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
            sys.exit(1)

        progress.update(task, description="[green]Profile generated!")
        progress.stop()

    console.print(f"\n[green bold]Profile generated for {profile.first_name} {profile.last_name}[/green bold]")
    console.print(f"[dim]Headline: {profile.headline}[/dim]\n")

    # Step 3: Export
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    outputs = []

    if fmt in ("all", "json"):
        json_path = out / "linkedin_profile.json"
        to_json(profile, str(json_path))
        outputs.append(("JSON", json_path))

    if fmt in ("all", "txt"):
        txt_path = out / "linkedin_profile_copypaste.txt"
        to_txt(profile, str(txt_path))
        outputs.append(("TXT (copy-paste)", txt_path))

    if fmt in ("all", "html"):
        html_path = out / "linkedin_profile_preview.html"
        to_html(profile, str(html_path))
        outputs.append(("HTML preview", html_path))

    console.print(Panel(
        "\n".join(f"  [blue]{label}[/blue]: {path}" for label, path in outputs),
        title="[green]Output files",
        border_style="green",
    ))

    console.print(
        "\n[bold]Next steps:[/bold]\n"
        "  1. Open the TXT file and copy-paste each section into LinkedIn\n"
        "  2. Open the HTML file in a browser to preview your profile\n"
        "  3. Use the JSON file for programmatic access\n"
    )


@main.command()
@click.argument("json_file", type=click.Path(exists=True))
@click.option(
    "--format", "fmt",
    type=click.Choice(["txt", "html", "all"]),
    default="all",
    help="Output format",
)
@click.option("--output-dir", "-o", default="./output", help="Output directory")
def export(json_file, fmt, output_dir):
    """Re-export a previously generated profile JSON to TXT or HTML.

    Example:

        linkedin-builder export output/linkedin_profile.json --format html
    """
    raw = Path(json_file).read_text(encoding="utf-8")
    profile = LinkedInProfile.from_json(raw)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if fmt in ("all", "txt"):
        path = out / "linkedin_profile_copypaste.txt"
        to_txt(profile, str(path))
        console.print(f"[green]TXT[/green]: {path}")

    if fmt in ("all", "html"):
        path = out / "linkedin_profile_preview.html"
        to_html(profile, str(path))
        console.print(f"[green]HTML[/green]: {path}")


if __name__ == "__main__":
    main()
