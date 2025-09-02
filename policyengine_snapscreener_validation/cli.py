"""Command-line interface for SNAP validation"""

import json

import click
from rich.console import Console

from .calculator import SNAPHousehold
from .validator import SNAPValidator

console = Console()


@click.group()
def main():
    """PolicyEngine SNAP Screener Validation Tool"""
    pass


@main.command()
@click.option(
    "--income",
    type=float,
    required=True,
    help="Monthly employment income",
)
@click.option(
    "--rent",
    type=float,
    required=True,
    help="Monthly rent payment",
)
@click.option(
    "--size",
    type=int,
    default=4,
    help="Household size (default: 4)",
)
@click.option(
    "--state",
    type=str,
    default="CA",
    help="State code (default: CA)",
)
@click.option(
    "--year",
    type=int,
    default=2025,
    help="Tax year (default: 2025)",
)
@click.option(
    "--no-tanf",
    is_flag=True,
    help="Exclude TANF from PolicyEngine calculation",
)
@click.option(
    "--with-sua",
    is_flag=True,
    help="Trigger Standard Utility Allowance in PolicyEngine",
)
@click.option(
    "--scrape",
    is_flag=True,
    help="Use web scraper for SNAP screener (requires Playwright)",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output results as JSON",
)
def compare(
    income, rent, size, state, year, no_tanf, with_sua, scrape, output_json
):
    """Compare SNAP benefits between PolicyEngine and SNAP screener"""

    # Create household
    household = SNAPHousehold(
        size=size,
        monthly_earned_income=income,
        monthly_unearned_income=0,
        monthly_rent=rent,
        state=state,
    )

    # Create validator
    validator = SNAPValidator(use_scraper=scrape)

    # Run comparison
    result = validator.validate_single(
        household,
        year=year,
        include_tanf=not no_tanf,
        trigger_sua=with_sua,
        use_scraper=scrape,
    )

    if output_json:
        # Output as JSON
        console.print_json(json.dumps(result, indent=2, default=str))
    else:
        # Print formatted comparison
        validator.print_comparison(result)


@main.command()
@click.option(
    "--scenarios",
    type=click.Path(exists=True),
    required=True,
    help="JSON file with test scenarios",
)
@click.option(
    "--year",
    type=int,
    default=2025,
    help="Tax year (default: 2025)",
)
@click.option(
    "--output",
    type=click.Path(),
    help="Output CSV file for results",
)
def batch(scenarios, year, output):
    """Run batch validation from scenarios file"""

    # Load scenarios
    with open(scenarios, "r") as f:
        scenarios_data = json.load(f)

    # Create validator
    validator = SNAPValidator()

    # Run validation
    results_df = validator.validate_scenarios(scenarios_data, year=year)

    # Save to CSV if requested
    if output:
        results_df.to_csv(output, index=False)
        console.print(f"[green]Results saved to {output}[/green]")

    # Print summary table
    validator.print_summary_table(results_df)


@main.command()
def examples():
    """Show example scenarios and usage"""

    console.print("\n[bold]Example Usage:[/bold]\n")

    console.print("1. Basic comparison:")
    console.print(
        "   [cyan]snap-validate compare --income 2500 --rent 1500[/cyan]"
    )
    console.print()

    console.print("2. Without TANF:")
    console.print(
        "   [cyan]snap-validate compare --income 2500 "
        "--rent 1500 --no-tanf[/cyan]"
    )
    console.print()

    console.print("3. With Standard Utility Allowance:")
    console.print(
        "   [cyan]snap-validate compare --income 4000 "
        "--rent 1500 --with-sua[/cyan]"
    )
    console.print()

    console.print("4. Using web scraper:")
    console.print(
        "   [cyan]snap-validate compare --income 2500 "
        "--rent 1500 --scrape[/cyan]"
    )
    console.print()

    console.print("5. Batch validation:")
    console.print(
        "   [cyan]snap-validate batch --scenarios "
        "tests/scenarios.json --output results.csv[/cyan]"
    )
    console.print()

    console.print("[bold]Example Scenarios File:[/bold]")
    example_scenarios = [
        {
            "name": "Low income family",
            "household": {
                "size": 4,
                "monthly_earned_income": 2500,
                "monthly_unearned_income": 0,
                "monthly_rent": 1500,
            },
            "options": {
                "include_tanf": True,
                "trigger_sua": False,
            },
        },
        {
            "name": "Medium income family",
            "household": {
                "size": 4,
                "monthly_earned_income": 4000,
                "monthly_unearned_income": 0,
                "monthly_rent": 1500,
            },
            "options": {
                "include_tanf": False,
                "trigger_sua": True,
            },
        },
    ]

    console.print_json(json.dumps(example_scenarios, indent=2))


@main.command()
def install_playwright():
    """Install Playwright browsers for web scraping"""

    console.print("[yellow]Installing Playwright browsers...[/yellow]")

    import subprocess

    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
        console.print(
            "[green]✓ Playwright browsers installed successfully![/green]"
        )
    except subprocess.CalledProcessError as e:
        console.print(
            f"[red]✗ Failed to install Playwright browsers: {e}[/red]"
        )
        console.print(
            "[yellow]Try running: python -m playwright install[/yellow]"
        )


if __name__ == "__main__":
    main()
