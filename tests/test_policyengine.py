"""Tests for PolicyEngine calculator wrapper"""

import pytest

from policyengine_snapscreener_validation import (
    PolicyEngineCalculator,
    SNAPHousehold,
)


class TestPolicyEngineCalculator:
    """Test PolicyEngine calculation wrapper"""

    def setup_method(self):
        """Set up test fixtures"""
        self.calculator = PolicyEngineCalculator()

    def test_basic_calculation(self):
        """Test basic PolicyEngine calculation"""
        household = SNAPHousehold(
            size=4,
            monthly_earned_income=2500,
            monthly_unearned_income=0,
            monthly_rent=1500,
            state="CA",
        )

        result = self.calculator.calculate(household, year=2025)

        assert "benefit_amount" in result
        assert "gross_income" in result
        assert "net_income" in result
        assert "is_eligible" in result
        assert result["year"] == 2025

    def test_tanf_inclusion(self):
        """Test that TANF can be included or excluded"""
        household = SNAPHousehold(
            size=4,
            monthly_earned_income=2000,  # Low enough for TANF
            monthly_unearned_income=0,
            monthly_rent=1500,
            state="CA",
        )

        result_with = self.calculator.calculate(household, include_tanf=True)
        result_without = self.calculator.calculate(
            household, include_tanf=False
        )

        # Gross income should be higher with TANF
        if result_with["tanf_benefit"] > 0:
            assert result_with["gross_income"] > result_without["gross_income"]

    def test_sua_trigger(self):
        """Test Standard Utility Allowance trigger"""
        household = SNAPHousehold(
            size=4,
            monthly_earned_income=3000,
            monthly_unearned_income=0,
            monthly_rent=1500,
            state="CA",
        )

        result_without = self.calculator.calculate(
            household, trigger_sua=False
        )
        result_with = self.calculator.calculate(household, trigger_sua=True)

        # Utility allowance should be higher with SUA
        assert (
            result_with["utility_allowance"]
            >= result_without["utility_allowance"]
        )

    def test_single_person_household(self):
        """Test single person household structure"""
        household = SNAPHousehold(
            size=1,
            monthly_earned_income=1500,
            monthly_unearned_income=0,
            monthly_rent=1000,
            state="CA",
        )

        result = self.calculator.calculate(household)

        assert result["benefit_amount"] >= 0
        assert result["is_eligible"] in [True, False]

    def test_large_household(self):
        """Test large household (6+ people)"""
        household = SNAPHousehold(
            size=8,
            monthly_earned_income=4000,
            monthly_unearned_income=0,
            monthly_rent=2000,
            state="CA",
        )

        result = self.calculator.calculate(household)

        assert result["benefit_amount"] >= 0
        assert "max_allotment" in result

    def test_dependent_care(self):
        """Test dependent care costs inclusion"""
        household = SNAPHousehold(
            size=4,
            monthly_earned_income=3000,
            monthly_unearned_income=0,
            monthly_rent=1500,
            monthly_dependent_care=600,
            state="CA",
        )

        result = self.calculator.calculate(household)

        # Should calculate with dependent care
        assert result["benefit_amount"] >= 0

    def test_different_states(self):
        """Test calculations for different states"""
        for state in ["CA", "NY", "TX"]:
            household = SNAPHousehold(
                size=4,
                monthly_earned_income=2500,
                monthly_unearned_income=0,
                monthly_rent=1500,
                state=state,
            )

            result = self.calculator.calculate(household)

            assert result["benefit_amount"] >= 0
            assert "is_eligible" in result
