"""Main validation class for comparing PolicyEngine with SNAP screener"""

from dataclasses import replace
from typing import Dict, List

import pandas as pd
from tabulate import tabulate

from .calculator import SNAPHousehold, SNAPScreenerCalculator
from .policyengine import PolicyEngineCalculator
from .scraper import SNAPScreenerScraper


class SNAPValidator:
    """Validates PolicyEngine calculations against SNAP screener"""

    def __init__(self, use_scraper: bool = False, headless: bool = True):
        """
        Initialize the validator.

        Args:
            use_scraper: Whether to use web scraper for SNAP screener
            headless: Run browser in headless mode (if using scraper)
        """
        self.screener_calc = SNAPScreenerCalculator()
        self.policyengine_calc = PolicyEngineCalculator()
        self.scraper = (
            SNAPScreenerScraper(headless=headless) if use_scraper else None
        )

    def validate_single(
        self,
        household: SNAPHousehold,
        year: int = 2025,
        include_tanf: bool = True,
        trigger_sua: bool = False,
        use_scraper: bool = False,
    ) -> Dict:
        """
        Validate a single household configuration.

        Returns:
            Dictionary with comparison results
        """
        # First calculate using PolicyEngine to get TANF amount if applicable
        pe_result = self.policyengine_calc.calculate(
            household,
            year=year,
            include_tanf=include_tanf,
            trigger_sua=trigger_sua,
        )

        # If PolicyEngine calculated TANF, add it to unearned income for screener
        household_for_screener = household
        if include_tanf and pe_result.get("tanf_benefit", 0) > 0:
            # Create a modified household with TANF as unearned income
            household_for_screener = replace(
                household,
                monthly_unearned_income=household.monthly_unearned_income
                + (pe_result["tanf_benefit"] / 12),
            )

        # Calculate using SNAP screener methodology
        if use_scraper and self.scraper:
            screener_result = self.scraper.calculate(household_for_screener)
            if screener_result is None:
                # Fall back to calculator
                screener_result = self.screener_calc.calculate(
                    household_for_screener
                )
        else:
            screener_result = self.screener_calc.calculate(
                household_for_screener
            )

        # Compare results
        comparison = {
            "household_size": household.size,
            "monthly_income": household.monthly_earned_income,
            "monthly_rent": household.monthly_rent,
            "screener_benefit": screener_result.get("benefit_amount", 0),
            "policyengine_benefit": pe_result.get("benefit_amount", 0),
            "difference": (
                pe_result.get("benefit_amount", 0)
                - screener_result.get("benefit_amount", 0)
            ),
            "tanf_included": include_tanf
            and pe_result.get("tanf_benefit", 0) > 0,
            "tanf_amount": (
                pe_result.get("tanf_benefit", 0) / 12
                if pe_result.get("tanf_benefit", 0)
                else 0
            ),
            "screener_details": screener_result,
            "policyengine_details": pe_result,
        }

        return comparison

    def validate_scenarios(
        self, scenarios: List[Dict], year: int = 2025
    ) -> pd.DataFrame:
        """
        Validate multiple scenarios.

        Args:
            scenarios: List of scenario configurations
            year: Tax year for calculations

        Returns:
            DataFrame with comparison results
        """
        results = []

        for scenario in scenarios:
            household = SNAPHousehold(**scenario.get("household", {}))
            options = scenario.get("options", {})

            comparison = self.validate_single(
                household,
                year=year,
                include_tanf=options.get("include_tanf", True),
                trigger_sua=options.get("trigger_sua", False),
                use_scraper=options.get("use_scraper", False),
            )

            # Add scenario name if provided
            if "name" in scenario:
                comparison["scenario"] = scenario["name"]

            results.append(comparison)

        return pd.DataFrame(results)

    def print_comparison(self, comparison: Dict):
        """Print a formatted comparison of results."""

        print("\n" + "=" * 70)
        print("SNAP BENEFIT COMPARISON")
        print("=" * 70)

        # Household info
        print("\nHousehold Configuration:")
        print(f"  Size: {comparison['household_size']} people")
        print(
            f"  Monthly Employment Income: "
            f"${comparison['monthly_income']:,.0f}"
        )
        print(f"  Monthly Rent: ${comparison['monthly_rent']:,.0f}")

        # Results
        print("\nBenefit Calculations:")
        print(
            f"  SNAP Screener:  ${comparison['screener_benefit']:,.2f}/month"
        )
        print(
            f"  PolicyEngine:   "
            f"${comparison['policyengine_benefit']:,.2f}/month"
        )
        print(f"  Difference:     ${comparison['difference']:+,.2f}")

        if comparison["tanf_included"]:
            print(
                f"\n  ⚠️  PolicyEngine included TANF: "
                f"${comparison['tanf_amount']:,.2f}/month"
            )

        # Detailed breakdown
        print("\n--- SNAP Screener Details ---")
        screener = comparison["screener_details"]
        print(f"  Gross Income:       ${screener.get('gross_income', 0):,.2f}")
        print(f"  Net Income:         ${screener.get('net_income', 0):,.2f}")
        print(
            f"  Max Allotment:      ${screener.get('max_allotment', 0):,.2f}"
        )
        print(
            f"  Expected Contrib:   "
            f"${screener.get('expected_contribution', 0):,.2f}"
        )

        print("\n--- PolicyEngine Details ---")
        pe = comparison["policyengine_details"]
        print(f"  Gross Income:       ${pe.get('gross_income', 0):,.2f}")
        print(f"  Net Income:         ${pe.get('net_income', 0):,.2f}")
        print(f"  Max Allotment:      ${pe.get('max_allotment', 0):,.2f}")
        print(
            f"  Expected Contrib:   ${pe.get('expected_contribution', 0):,.2f}"
        )

        if pe.get("utility_allowance", 0) > 0:
            print(
                f"  Utility Allowance:  ${pe.get('utility_allowance', 0):,.2f}"
            )

        print("=" * 70)

    def print_summary_table(self, df: pd.DataFrame):
        """Print a summary table of multiple comparisons."""

        # Select key columns for display
        display_cols = [
            "scenario",
            "household_size",
            "monthly_income",
            "monthly_rent",
            "screener_benefit",
            "policyengine_benefit",
            "difference",
            "tanf_included",
        ]

        # Filter to available columns
        display_cols = [col for col in display_cols if col in df.columns]

        # Format the DataFrame for display
        display_df = df[display_cols].copy()

        # Format currency columns
        currency_cols = [
            "monthly_income",
            "monthly_rent",
            "screener_benefit",
            "policyengine_benefit",
            "difference",
        ]
        for col in currency_cols:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"${x:,.0f}")

        # Print table
        print("\n" + "=" * 100)
        print("VALIDATION SUMMARY")
        print("=" * 100)
        print(
            tabulate(
                display_df,
                headers="keys",
                tablefmt="grid",
                showindex=False,
            )
        )
        print("=" * 100)
