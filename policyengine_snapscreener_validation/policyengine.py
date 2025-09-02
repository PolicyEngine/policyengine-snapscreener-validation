"""PolicyEngine US calculation wrapper"""

from typing import Dict, Optional

from policyengine_us import Simulation

from .calculator import SNAPHousehold


class PolicyEngineCalculator:
    """Wrapper for PolicyEngine US SNAP calculations"""

    def __init__(self):
        pass

    def calculate(
        self,
        household: SNAPHousehold,
        year: int = 2025,
        include_tanf: bool = True,
        trigger_sua: bool = False,
    ) -> Dict:
        """
        Calculate SNAP benefits using PolicyEngine US.

        Args:
            household: Household configuration
            year: Tax year for calculation
            include_tanf: Whether to allow TANF calculation
            trigger_sua: Whether to trigger Standard Utility Allowance

        Returns:
            Dictionary with calculation details and benefit amount
        """
        # Build simulation situation
        situation = self._build_situation(household, year, trigger_sua)

        # Create simulation
        sim = Simulation(situation=situation)

        # Calculate key values
        employment_income = sum(sim.calculate("employment_income", year))
        tanf = sim.calculate("tanf", year)[0] if include_tanf else 0

        snap_earned_income = sim.calculate("snap_earned_income", year)[0]
        snap_unearned_income = sim.calculate("snap_unearned_income", year)[0]
        snap_gross_income = sim.calculate("snap_gross_income", year)[0]

        snap_standard_deduction = sim.calculate(
            "snap_standard_deduction", year
        )[0]
        snap_earned_income_deduction = sim.calculate(
            "snap_earned_income_deduction", year
        )[0]
        snap_utility_allowance = sim.calculate("snap_utility_allowance", year)[
            0
        ]
        housing_cost = sim.calculate("housing_cost", year)[0]
        snap_excess_shelter_expense_deduction = sim.calculate(
            "snap_excess_shelter_expense_deduction", year
        )[0]

        snap_net_income = sim.calculate("snap_net_income", year)[0]
        snap_max_allotment = sim.calculate("snap_max_allotment", year)[0]
        snap_expected_contribution = sim.calculate(
            "snap_expected_contribution", year
        )[0]
        snap_benefit = sim.calculate("snap", year)[0]

        # Check eligibility
        meets_gross_test = sim.calculate("meets_snap_gross_income_test", year)[
            0
        ]
        meets_net_test = sim.calculate("meets_snap_net_income_test", year)[0]
        meets_asset_test = sim.calculate("meets_snap_asset_test", year)[0]
        is_eligible = sim.calculate("is_snap_eligible", year)[0]

        return {
            "year": year,
            "employment_income": employment_income,
            "tanf_benefit": tanf,
            "snap_earned_income": snap_earned_income,
            "snap_unearned_income": snap_unearned_income,
            "gross_income": snap_gross_income / 12,  # Convert to monthly
            "standard_deduction": snap_standard_deduction / 12,
            "earned_income_deduction": snap_earned_income_deduction / 12,
            "utility_allowance": snap_utility_allowance / 12,
            "housing_cost": housing_cost / 12,
            "excess_shelter_deduction": snap_excess_shelter_expense_deduction
            / 12,
            "net_income": snap_net_income / 12,
            "max_allotment": snap_max_allotment / 12,
            "expected_contribution": snap_expected_contribution / 12,
            "benefit_amount": snap_benefit / 12,  # Monthly benefit
            "annual_benefit": snap_benefit,
            "meets_gross_test": bool(meets_gross_test),
            "meets_net_test": bool(meets_net_test),
            "meets_asset_test": bool(meets_asset_test),
            "is_eligible": bool(is_eligible),
        }

    def _build_situation(
        self, household: SNAPHousehold, year: int, trigger_sua: bool
    ) -> Dict:
        """Build PolicyEngine simulation situation from household data."""

        # Distribute income between two parents if household size > 1
        if household.size >= 2:
            parent1_income = household.monthly_earned_income * 12 / 2
            parent2_income = household.monthly_earned_income * 12 / 2
        else:
            parent1_income = household.monthly_earned_income * 12
            parent2_income = 0

        # Build people dictionary
        people = {
            "parent1": {
                "age": {str(year): 30},
                "employment_income": {str(year): parent1_income},
                "pre_subsidy_rent": {str(year): household.monthly_rent * 12},
            }
        }

        members = ["parent1"]

        if household.size >= 2:
            people["parent2"] = {
                "age": {str(year): 30},
                "employment_income": {str(year): parent2_income},
            }
            members.append("parent2")

        # Add children if needed
        for i in range(household.size - 2):
            child_name = f"child{i+1}"
            people[child_name] = {
                "age": {str(year): 5}  # Default age for children
            }
            members.append(child_name)

        # Build marital units
        marital_units = {}
        if household.size >= 2:
            marital_units["marital_unit"] = {"members": ["parent1", "parent2"]}
            marital_unit_counter = 2
        else:
            marital_units["marital_unit"] = {"members": ["parent1"]}
            marital_unit_counter = 2

        # Add children to separate marital units
        for i in range(household.size - 2):
            child_name = f"child{i+1}"
            marital_units[f"marital_unit_{marital_unit_counter}"] = {
                "members": [child_name]
            }
            marital_unit_counter += 1

        # Build SPM unit
        spm_units = {
            "spm_unit": {
                "members": members,
                "snap_emergency_allotment": {str(year): False},
            }
        }

        # Add heating/cooling expense if we want to trigger SUA
        if trigger_sua:
            spm_units["spm_unit"]["heating_cooling_expense"] = {str(year): 1}

        # Add dependent care if specified
        if household.monthly_dependent_care > 0:
            spm_units["spm_unit"]["childcare_expenses"] = {
                str(year): household.monthly_dependent_care * 12
            }

        # Build complete situation
        situation = {
            "people": people,
            "families": {"family": {"members": members}},
            "marital_units": marital_units,
            "tax_units": {"tax_unit": {"members": members}},
            "spm_units": spm_units,
            "households": {
                "household": {
                    "members": members,
                    "state_code": {str(year): household.state},
                }
            },
        }

        return situation
