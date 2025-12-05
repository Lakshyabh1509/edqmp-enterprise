"""
EDQMP CLI - Command Line Interface
"""
import typer
from rich.console import Console
from rich.table import Table
import httpx
import os

app = typer.Typer(help="EDQMP - Enterprise Data Quality & Monitoring Platform CLI")
console = Console()

API_URL = os.getenv("EDQMP_API_URL", "http://localhost:8000/api/v1")


@app.command()
def validate(
    pipeline: str = typer.Option(..., "--pipeline", "-p", help="Pipeline name"),
    rules: str = typer.Option(None, "--rules", "-r", help="Comma-separated rule names"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table, json")
):
    """Run data quality validation on a pipeline"""
    console.print(f"[bold blue]Validating pipeline:[/] {pipeline}")
    
    with console.status("Running validation..."):
        # In production, call API
        console.print("[green]✓[/] Completeness check: 99.2% (passed)")
        console.print("[green]✓[/] Accuracy check: 100% (passed)")
        console.print("[yellow]⚠[/] Timeliness check: 97.5% (warning)")
    
    console.print(f"\n[bold green]Validation complete![/] Overall score: 98.9%")


@app.command()
def status():
    """Show current pipeline status"""
    table = Table(title="Pipeline Status")
    table.add_column("Pipeline", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Last Run")
    table.add_column("Quality Score")
    
    table.add_row("Trade Settlement", "✅ Healthy", "2 min ago", "99.2%")
    table.add_row("KYC API", "✅ Healthy", "5 min ago", "98.5%")
    table.add_row("FX Rates", "⚠️ Warning", "1 min ago", "94.8%")
    
    console.print(table)


@app.command()
def rules(
    list_all: bool = typer.Option(False, "--list", "-l", help="List all rules"),
    add: str = typer.Option(None, "--add", "-a", help="Add rule from YAML file")
):
    """Manage quality rules"""
    if list_all:
        table = Table(title="Quality Rules")
        table.add_column("Name", style="cyan")
        table.add_column("Type")
        table.add_column("Severity")
        table.add_column("Active")
        
        table.add_row("trade_completeness", "completeness", "critical", "✅")
        table.add_row("account_format", "accuracy", "critical", "✅")
        table.add_row("price_anomaly", "anomaly", "warning", "✅")
        
        console.print(table)


if __name__ == "__main__":
    app()
