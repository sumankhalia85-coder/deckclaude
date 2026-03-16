"""
DeckClaude CLI — Generate PowerPoint presentations from the command line.

Usage:
  python cli.py generate --prompt "..." --theme mckinsey --slides 10
  python cli.py generate --file data.csv --prompt "..." --theme default
  python cli.py generate --form
  python cli.py status
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

load_dotenv()

app = typer.Typer(
    name="deckclaude",
    help="DeckClaude — AI-powered multi-agent PowerPoint generation system",
    add_completion=False,
)

generate_app = typer.Typer(help="Generate a PowerPoint presentation")
app.add_typer(generate_app, name="generate")


def _get_rich():
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
        from rich.table import Table
        from rich import print as rprint
        return Console(), Panel, Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, Table, rprint
    except ImportError:
        return None, None, None, None, None, None, None, None, None


def _open_file(path: str):
    """Open the generated file with the default application."""
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])
    except Exception as e:
        typer.echo(f"Could not open file automatically: {e}")
        typer.echo(f"File saved at: {path}")


def _run_generation(user_input: dict, open_output: bool = True):
    """Execute the workflow and display results."""
    console, Panel, Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, Table, rprint = _get_rich()

    if console:
        console.print("\n[bold blue]╔══════════════════════════════════╗")
        console.print("[bold blue]║      DeckClaude AI Generator     ║")
        console.print("[bold blue]╚══════════════════════════════════╝\n")

        prompt_preview = (user_input.get("prompt") or "")[:80]
        console.print(f"[dim]Request:[/dim] [italic]{prompt_preview}[/italic]")
        if user_input.get("file_path"):
            console.print(f"[dim]File:[/dim]    [cyan]{user_input['file_path']}[/cyan]")
        console.print(f"[dim]Theme:[/dim]   [yellow]{user_input.get('requested_theme', 'default')}[/yellow]")
        console.print(f"[dim]Slides:[/dim]  {user_input.get('requested_slides') or 'auto'}\n")

    start = time.time()

    try:
        from workflows.deck_workflow import run_workflow

        agents = [
            ("IntentAgent", "Classifying presentation intent"),
            ("ResearchDataAgent", "Processing uploaded data"),
            ("BlueprintAgent", "Generating slide blueprint"),
            ("InsightGeneratorAgent", "Creating consulting insights"),
            ("VisualDesignAgent", "Planning visual design"),
            ("ChartGeneratorAgent", "Generating charts"),
            ("ImageIntelligenceAgent", "Acquiring slide images"),
            ("DeckBuilderAgent", "Building PowerPoint file"),
            ("SlideCriticAgent", "Quality review & revisions"),
        ]

        if console and Progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Running multi-agent pipeline...", total=len(agents))

                result = run_workflow(user_input, show_progress=False)
                progress.update(task, completed=len(agents), description="[green]Pipeline complete!")
        else:
            result = run_workflow(user_input, show_progress=True)

    except ImportError as e:
        typer.echo(f"\nError: Missing dependency — {e}", err=True)
        typer.echo("Run: pip install -r requirements.txt", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"\nGeneration error: {e}", err=True)
        raise typer.Exit(1)

    elapsed = time.time() - start

    if result.get("success"):
        output_path = result["output_path"]
        quality = result.get("quality_report", {}) or {}
        score = quality.get("overall_deck_score", "N/A")
        ready = quality.get("ready_for_client", False)
        slide_count = len(result.get("blueprint", {}).get("slides", []))

        if console and Table:
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Key", style="dim")
            table.add_column("Value", style="bold")
            table.add_row("Status", "[green]SUCCESS[/green]")
            table.add_row("Output", f"[cyan]{output_path}[/cyan]")
            table.add_row("Slides", str(slide_count))
            table.add_row("Quality Score", f"[yellow]{score}/10[/yellow]")
            table.add_row("Client Ready", "[green]Yes[/green]" if ready else "[yellow]Needs Review[/yellow]")
            table.add_row("Total Time", f"{elapsed:.1f}s")
            console.print("\n")
            console.print(Panel(table, title="[bold green]Generation Complete[/bold green]", expand=False))

            # Show timing breakdown
            timings = result.get("timings", {})
            if timings:
                timing_table = Table(title="Agent Timings", show_header=True)
                timing_table.add_column("Agent", style="cyan")
                timing_table.add_column("Time (s)", justify="right")
                for agent, t in sorted(timings.items(), key=lambda x: x[1], reverse=True):
                    timing_table.add_row(agent, f"{t:.2f}")
                console.print(timing_table)

            if result.get("errors"):
                console.print(f"\n[yellow]Warnings ({len(result['errors'])}):[/yellow]")
                for err in result["errors"][:5]:
                    console.print(f"  [dim]• {err}[/dim]")
        else:
            typer.echo(f"\n✓ Success! Output: {output_path}")
            typer.echo(f"  Slides: {slide_count} | Quality: {score}/10 | Time: {elapsed:.1f}s")

        if open_output:
            _open_file(output_path)

    else:
        errors = result.get("errors", ["Unknown failure"])
        if console:
            console.print(f"\n[bold red]Generation failed:[/bold red]")
            for err in errors[:5]:
                console.print(f"  [red]• {err}[/red]")
        else:
            typer.echo(f"\nGeneration failed: {'; '.join(errors[:3])}", err=True)
        raise typer.Exit(1)


@app.command("generate")
def generate_cmd(
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="Free-text presentation description"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Path to data file (CSV/PDF/Excel/JSON)"),
    theme: str = typer.Option("default", "--theme", "-t", help="Brand theme: default|mckinsey|dark_tech|consulting_green"),
    slides: Optional[int] = typer.Option(None, "--slides", "-s", help="Number of slides (overrides auto-selection)"),
    form: bool = typer.Option(False, "--form", help="Interactive form mode (guided input)"),
    no_open: bool = typer.Option(False, "--no-open", help="Do not open the file after generation"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Custom output path for .pptx file"),
):
    """
    Generate a PowerPoint presentation using the multi-agent AI pipeline.

    Examples:\n
      python cli.py generate --prompt "AI adoption strategy for retail" --theme mckinsey --slides 12\n
      python cli.py generate --file data.csv --prompt "Analyze our sales performance" --theme default\n
      python cli.py generate --form
    """
    valid_themes = {"default", "mckinsey", "dark_tech", "consulting_green"}
    if theme not in valid_themes:
        typer.echo(f"Invalid theme '{theme}'. Choose from: {', '.join(valid_themes)}", err=True)
        raise typer.Exit(1)

    if slides and (slides < 4 or slides > 50):
        typer.echo("Slides must be between 4 and 50.", err=True)
        raise typer.Exit(1)

    if file and not file.exists():
        typer.echo(f"File not found: {file}", err=True)
        raise typer.Exit(1)

    # Interactive form mode
    if form:
        typer.echo("\nDeckClaude Interactive Form\n" + "=" * 30)
        prompt = prompt or typer.prompt("Describe your presentation")
        intent_choices = "strategy_deck|executive_update|proposal_deck|training_deck|project_status|research_summary|pitch_deck|board_presentation"
        intent = typer.prompt(f"Deck type [{intent_choices}]", default="strategy_deck")
        audience = typer.prompt("Target audience", default="Senior executives")
        tone_choices = "formal|semi-formal|conversational|technical|inspirational"
        tone_val = typer.prompt(f"Tone [{tone_choices}]", default="semi-formal")
        if not slides:
            slides = typer.prompt("Number of slides", default=12, type=int)
        theme = typer.prompt("Theme [default|mckinsey|dark_tech|consulting_green]", default=theme)

        form_data = {"intent": intent, "audience": audience, "tone": tone_val}
    else:
        form_data = None

    if not prompt and not form:
        typer.echo("Error: Provide --prompt or use --form for interactive mode.", err=True)
        raise typer.Exit(1)

    # Check API key
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    key_var = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
    if not os.getenv(key_var):
        typer.echo(f"\nWarning: {key_var} not set. Copy .env.example to .env and add your API key.", err=True)
        typer.echo("  cp .env.example .env && nano .env", err=True)
        raise typer.Exit(1)

    user_input = {
        "prompt": prompt or "",
        "form_data": form_data,
        "file_path": str(file) if file else None,
        "file_name": file.name if file else None,
        "requested_slides": slides,
        "requested_theme": theme,
        "output_path": str(output) if output else None,
    }

    _run_generation(user_input, open_output=not no_open)


@app.command("status")
def status_cmd():
    """Show system status and configuration."""
    console, *_ = _get_rich()
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    model = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
    anthropic_key = "✓" if os.getenv("ANTHROPIC_API_KEY") else "✗ NOT SET"
    openai_key = "✓" if os.getenv("OPENAI_API_KEY") else "✗ NOT SET"
    unsplash_key = "✓" if os.getenv("UNSPLASH_ACCESS_KEY") else "✗ (fallback: generated images)"
    output_dir = os.getenv("OUTPUT_DIR", "./output")

    info = f"""
DeckClaude System Status
========================
LLM Provider:    {provider}
LLM Model:       {model}
Anthropic Key:   {anthropic_key}
OpenAI Key:      {openai_key}
Unsplash Key:    {unsplash_key}
Output Dir:      {output_dir}
Python:          {sys.version.split()[0]}
"""
    typer.echo(info)

    # Check required packages
    packages = ["langgraph", "langchain", "anthropic", "openai", "pptx", "matplotlib", "pandas", "fitz"]
    typer.echo("Package Status:")
    for pkg in packages:
        try:
            __import__(pkg.replace("pptx", "pptx").replace("fitz", "fitz"))
            status = "✓"
        except ImportError:
            status = "✗ MISSING"
        typer.echo(f"  {pkg:<20} {status}")


if __name__ == "__main__":
    app()
