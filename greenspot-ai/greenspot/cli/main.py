"""
GreenSpot AI Developer CLI.
Built with Typer and Rich.
Commands:
  greenspot radar               - Live global radar of spot discounts and clean energy
  greenspot run                 - Arbitrage and dispatch a batch workload
  greenspot estimate            - Quick cost & emissions comparison
"""

import asyncio
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from greenspot.core.scorer import ArbitrageScorer
from greenspot.runtime.launcher import WorkloadLauncher
from greenspot.schemas import JobSubmission
from greenspot.receipt.generator import ReceiptFormatter

app = typer.Typer(
    name="greenspot",
    help="🌱 GreenSpot AI — Cloud Compute, Priced by the Planet.",
    add_completion=False
)
console = Console()

@app.command("radar")
def radar(
    instance_type: str = typer.Option("g4dn.xlarge", "--instance", "-i", help="Target instance type"),
    carbon_weight: float = typer.Option(0.5, "--carbon-weight", "-w", help="Weight (0.0=cheapest, 1.0=cleanest)")
):
    """
    Displays the live global radar table of cloud spot pricing and clean energy levels.
    """
    console.print(f"\n[bold green]🌱 GreenSpot AI — Global Regional Arbitrage Radar[/bold green]")
    console.print(f"[dim]Instance Class: [bold]{instance_type}[/bold] | Optimization Weight: [bold]{carbon_weight}[/bold][/dim]\n")

    scorer = ArbitrageScorer()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        progress.add_task(description="Scanning AWS/GCP spot markets and regional electrical grids...", total=None)
        try:
            candidates = asyncio.run(scorer.rank_candidates(instance_type=instance_type, carbon_weight=carbon_weight))
        except Exception as e:
            progress.stop()
            console.print(Panel(f"Failed to fetch market data:\n{str(e)}", title="Backend Error", style="bold red"))
            raise typer.Exit(1)

    table = Table(title="Live Global Compute Arbitrage Matrix", header_style="bold magenta")
    table.add_column("Rank", justify="center", style="bold")
    table.add_column("Region", style="cyan")
    table.add_column("Location", style="white")
    table.add_column("Spot Rate", justify="right", style="green bold")
    table.add_column("Retail Rate", justify="right", style="dim")
    table.add_column("Discount", justify="right", style="bold yellow")
    table.add_column("Grid Carbon", justify="right")
    table.add_column("Energy Mix", style="blue")

    for c in candidates:
        if c.carbon_intensity_gco2_per_kwh < 100:
            carbon_disp = f"[bold green]{c.carbon_intensity_gco2_per_kwh} g[/bold green]"
        elif c.carbon_intensity_gco2_per_kwh < 300:
            carbon_disp = f"[bold yellow]{c.carbon_intensity_gco2_per_kwh} g[/bold yellow]"
        else:
            carbon_disp = f"[bold red]{c.carbon_intensity_gco2_per_kwh} g[/bold red]"

        rank_badge = f"🥇 #{c.rank}" if c.rank == 1 else (f"🥈 #{c.rank}" if c.rank == 2 else f"   #{c.rank}")

        table.add_row(
            rank_badge,
            c.region_id,
            f"{c.region_name} ({c.country})",
            f"${c.spot_price_usd_per_hr:.3f}/hr",
            f"${c.ondemand_price_usd_per_hr:.3f}/hr",
            f"-{c.discount_pct:.0f}%",
            carbon_disp,
            f"{c.clean_energy_pct:.0f}% {c.primary_energy_source}"
        )

    console.print(table)
    console.print("[dim]💡 Tip: Use `greenspot run --task='...'` to automatically dispatch to the top candidate.[/dim]\n")


@app.command("run")
def run(
    task: str = typer.Option("python train_bert.py", "--task", "-t", help="Command or workload to run"),
    budget: float = typer.Option(25.0, "--budget", "-b", help="Max budget in USD"),
    hours: float = typer.Option(2.0, "--duration", "-d", help="Estimated job duration in hours"),
    instance: str = typer.Option("g4dn.xlarge", "--instance", "-i", help="Target instance type"),
    carbon_weight: float = typer.Option(0.5, "--carbon-weight", "-w", help="Weight for carbon (0.0 to 1.0)"),
    simulate_preemption: bool = typer.Option(True, "--simulate-preemption/--no-simulate-preemption", help="Simulate a 2-min spot eviction & recovery")
):
    """
    Arbitrates and dispatches a batch workload to the optimal clean spot instance.
    """
    console.print(f"\n[bold green]🌱 GreenSpot AI Dispatcher[/bold green]")
    console.print(f"Task: [bold white]{task}[/bold white] | Budget: [bold green]${budget:.2f}[/bold green]\n")

    scorer = ArbitrageScorer()
    launcher = WorkloadLauncher()

    submission = JobSubmission(
        task_command=task,
        max_budget_usd=budget,
        estimated_duration_hours=hours,
        preferred_instance_type=instance,
        carbon_weight=carbon_weight
    )

    try:
        candidates = asyncio.run(scorer.rank_candidates(
            instance_type=instance,
            carbon_weight=carbon_weight,
            max_budget_usd=budget,
            estimated_hours=hours
        ))
    except Exception as e:
        console.print(Panel(f"Failed to rank candidates:\n{str(e)}", title="Backend Error", style="bold red"))
        raise typer.Exit(1)

    if not candidates:
        console.print("[bold red]❌ Error: No regions found within your budget parameters.[/bold red]")
        raise typer.Exit(1)

    top_pick = candidates[0]
    console.print(f"🎯 [bold]Optimal Target Identified:[/bold] [cyan]{top_pick.region_id}[/cyan] ({top_pick.region_name})")
    console.print(f"   💸 [bold]{top_pick.discount_pct:.0f}% cheaper[/bold] (${top_pick.spot_price_usd_per_hr:.3f}/hr vs ${top_pick.ondemand_price_usd_per_hr:.3f}/hr)")
    console.print(f"   🍃 [bold]{top_pick.clean_energy_pct:.0f}% clean energy[/bold] ({top_pick.carbon_intensity_gco2_per_kwh} gCO2/kWh)\n")

    receipt = asyncio.run(launcher.execute_job(
        submission=submission,
        ranked_candidates=candidates,
        simulate_preemption=simulate_preemption
    ))

    console.print("\n")
    console.print(ReceiptFormatter.render_terminal_receipt(receipt))
    console.print("\n")


if __name__ == "__main__":
    app()
