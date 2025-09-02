"""Tests for the validator module"""

import pandas as pd

from policyengine_snapscreener_validation import (
    SNAPHousehold,
    SNAPValidator,
)


class TestSNAPValidator:
    """Test the main validator class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.validator = SNAPValidator(use_scraper=False)
        self.household = SNAPHousehold(
            size=4,
            monthly_earned_income=2500,
            monthly_unearned_income=0,
            monthly_rent=1500,
            state="CA",
        )

    def test_validate_single_basic(self):
        """Test single household validation"""
        result = self.validator.validate_single(self.household)

        assert "screener_benefit" in result
        assert "policyengine_benefit" in result
        assert "difference" in result
        assert "tanf_included" in result
        assert result["household_size"] == 4
        assert result["monthly_income"] == 2500
        assert result["monthly_rent"] == 1500

    def test_validate_single_with_tanf(self):
        """Test that TANF affects the calculation"""
        result_with_tanf = self.validator.validate_single(
            self.household, include_tanf=True
        )
        result_without_tanf = self.validator.validate_single(
            self.household, include_tanf=False
        )

        # With TANF should have lower SNAP benefits (or same if no TANF)
        if result_with_tanf["tanf_included"]:
            assert (
                result_with_tanf["policyengine_benefit"]
                <= result_without_tanf["policyengine_benefit"]
            )
        else:
            # If no TANF, benefits should be the same
            assert (
                result_with_tanf["policyengine_benefit"]
                == result_without_tanf["policyengine_benefit"]
            )

    def test_validate_single_with_sua(self):
        """Test Standard Utility Allowance effect"""
        result_without_sua = self.validator.validate_single(
            self.household, trigger_sua=False
        )
        result_with_sua = self.validator.validate_single(
            self.household, trigger_sua=True
        )

        # With SUA should have higher benefits
        assert (
            result_with_sua["policyengine_benefit"]
            >= result_without_sua["policyengine_benefit"]
        )

    def test_validate_scenarios(self):
        """Test batch scenario validation"""
        scenarios = [
            {
                "name": "Low income",
                "household": {
                    "size": 4,
                    "monthly_earned_income": 2500,
                    "monthly_unearned_income": 0,
                    "monthly_rent": 1500,
                },
                "options": {
                    "include_tanf": True,
                },
            },
            {
                "name": "High income",
                "household": {
                    "size": 4,
                    "monthly_earned_income": 5000,
                    "monthly_unearned_income": 0,
                    "monthly_rent": 1500,
                },
                "options": {
                    "include_tanf": False,
                },
            },
        ]

        df = self.validator.validate_scenarios(scenarios)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "scenario" in df.columns
        assert df.iloc[0]["scenario"] == "Low income"
        assert df.iloc[1]["scenario"] == "High income"

    def test_print_comparison(self, capsys):
        """Test that print_comparison outputs correctly"""
        result = self.validator.validate_single(self.household)
        self.validator.print_comparison(result)

        captured = capsys.readouterr()
        assert "SNAP BENEFIT COMPARISON" in captured.out
        assert "PolicyEngine" in captured.out
        assert "SNAP Screener" in captured.out

    def test_print_summary_table(self, capsys):
        """Test summary table printing"""
        scenarios = [
            {
                "name": "Test 1",
                "household": {
                    "size": 4,
                    "monthly_earned_income": 2500,
                    "monthly_unearned_income": 0,
                    "monthly_rent": 1500,
                },
            },
        ]

        df = self.validator.validate_scenarios(scenarios)
        self.validator.print_summary_table(df)

        captured = capsys.readouterr()
        assert "VALIDATION SUMMARY" in captured.out
