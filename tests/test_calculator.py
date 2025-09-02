"""Tests for SNAP screener calculator"""

from policyengine_snapscreener_validation.calculator import (
    SNAPHousehold,
    SNAPScreenerCalculator,
)


class TestSNAPScreenerCalculator:
    """Test SNAP screener calculation methodology"""

    def setup_method(self):
        """Set up test fixtures"""
        self.calculator = SNAPScreenerCalculator()

    def test_basic_calculation(self):
        """Test basic SNAP calculation"""
        household = SNAPHousehold(
            size=4,
            monthly_earned_income=2500,
            monthly_unearned_income=0,
            monthly_rent=1500,
        )

        result = self.calculator.calculate(household)

        assert "benefit_amount" in result
        assert result["gross_income"] == 2500
        assert result["is_eligible"] is True
        # Expected benefit is around $622 based on SNAP screener
        assert 600 <= result["benefit_amount"] <= 650

    def test_high_income_ineligible(self):
        """Test that high income makes household ineligible"""
        household = SNAPHousehold(
            size=4,
            monthly_earned_income=10000,
            monthly_unearned_income=0,
            monthly_rent=1500,
        )

        result = self.calculator.calculate(household)

        assert result["is_eligible"] is False
        assert result["benefit_amount"] == 0

    def test_single_person_household(self):
        """Test calculation for single person"""
        household = SNAPHousehold(
            size=1,
            monthly_earned_income=1000,
            monthly_unearned_income=0,
            monthly_rent=800,
        )

        result = self.calculator.calculate(household)

        assert result["gross_income"] == 1000
        assert result["max_allotment"] == 292  # 2024 value for size 1

    def test_deductions(self):
        """Test that deductions are calculated correctly"""
        household = SNAPHousehold(
            size=4,
            monthly_earned_income=3000,
            monthly_unearned_income=0,
            monthly_rent=1200,
            monthly_dependent_care=500,
            monthly_child_support=200,
        )

        result = self.calculator.calculate(household)

        # Check deductions are applied
        assert result["earned_income_deduction"] == 600  # 20% of 3000
        assert result["dependent_care_deduction"] == 500
        assert result["child_support_deduction"] == 200
        assert result["standard_deduction"] == 217  # Size 4 standard deduction

    def test_excess_shelter_cap(self):
        """Test that excess shelter deduction is capped for non-elderly"""
        household = SNAPHousehold(
            size=4,
            monthly_earned_income=2000,
            monthly_unearned_income=0,
            monthly_rent=2000,  # Very high rent
            has_elderly_disabled=False,
        )

        result = self.calculator.calculate(household)

        # Excess shelter should be capped at $624
        assert result["excess_shelter_deduction"] <= 624

    def test_utility_allowance(self):
        """Test that utility allowance increases shelter costs"""
        household_without = SNAPHousehold(
            size=4,
            monthly_earned_income=2500,
            monthly_unearned_income=0,
            monthly_rent=1000,
            has_utility_expenses=False,
        )

        household_with = SNAPHousehold(
            size=4,
            monthly_earned_income=2500,
            monthly_unearned_income=0,
            monthly_rent=1000,
            has_utility_expenses=True,
        )

        result_without = self.calculator.calculate(household_without)
        result_with = self.calculator.calculate(household_with)

        # Benefit should be higher with utility allowance
        assert result_with["benefit_amount"] > result_without["benefit_amount"]
