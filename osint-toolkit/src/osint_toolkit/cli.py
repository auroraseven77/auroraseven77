from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.table import Table
from .correlator import write_report
from .pipeline import run as run_pipeline
from .policy import AuthorizationError

app = typer.Typer(add_completion=False, help="Aurora-safe OSINT toolkit (passive, authorized).")
console = Console()


@app.command()
def run(
    target: str = typer.Argument(..., help="Domain or HTTP(S) URL."),
    allow: list[str] = typer.Option(..., "--allow", help="Explicitly authorized domain/host scope. Repeatable."),
    out: str = typer.Option("observations.jsonl", "--out", "-o"),
    evidence: str = typer.Option("evidence", "--evidence"),
) -> None:
    """Run passive collectors against an explicitly authorized target."""
    try:
        observations = run_pipeline(target, allow, out_path=out, evidence_root=evidence)
    except AuthorizationError as exc:
        raise typer.BadParameter(str(exc)) from exc
    table = Table(title=f"Observations for {target}")
    for column in ("source", "entity_type", "confidence", "status", "value"):
        table.add_column(column)
    for item in observations:
        table.add_row(item.source, item.entity_type, f"{item.confidence:.2f}", item.status, item.value[:80])
    console.print(table)
    console.print(f"{len(observations)} observations written to {out}")


@app.command()
def report(
    observations: str = typer.Option("observations.jsonl", "--observations", "-i"),
    out: str = typer.Option("report.json", "--out", "-o"),
    threshold: float = typer.Option(0.7, "--threshold", min=0.0, max=1.0),
) -> None:
    """Correlate existing observations; does not collect network data."""
    result = write_report(observations, out, threshold)
    console.print_json(json.dumps(result))


@app.command()
def show(out: str = typer.Option("observations.jsonl", "--out", "-o")) -> None:
    """Pretty-print an observations JSONL file."""
    with open(out, encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                console.print_json(line)


if __name__ == "__main__":
    app()
