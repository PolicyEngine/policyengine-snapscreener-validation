"""SNAP Screener calculation methodology implementation"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class SNAPHousehold:
    """Represents a household for SNAP calculations"""
    
    size: int
    monthly_earned_income: float
    monthly_unearned_income: float
    monthly_rent: float
    monthly_dependent_care: float = 0
    monthly_child_support: float = 0
    monthly_medical_expenses: float = 0
    has_elderly_disabled: bool = False
    has_utility_expenses: bool = False
    state: str = "CA"


class SNAPScreenerCalculator:
    """
    Implements SNAP screener calculation methodology.
    Based on 2024 federal SNAP rules and deductions.
    """
    
    # 2024 Standard deductions by household size
    STANDARD_DEDUCTIONS = {
        1: 198, 2: 198, 3: 198, 4: 217, 5: 255, 6: 294
    }
    
    # 2024 Maximum allotments by household size
    MAX_ALLOTMENTS = {
        1: 292, 2: 536, 3: 768, 4: 975, 5: 1158, 6: 1390, 7: 1536, 8: 1756
    }
    
    # 2024 Gross income limits (130% of poverty)
    GROSS_INCOME_LIMITS = {
        1: 1632, 2: 2198, 3: 2765, 4: 3331, 5: 3897, 6: 4463, 7: 5030, 8: 5596
    }
    
    # 2024 Net income limits (100% of poverty)
    NET_INCOME_LIMITS = {
        1: 1255, 2: 1691, 3: 2127, 4: 2563, 5: 2998, 6: 3434, 7: 3870, 8: 4305
    }
    
    # Excess shelter deduction cap (for non-elderly/disabled households)
    EXCESS_SHELTER_CAP = 624
    
    # Earned income deduction rate
    EARNED_INCOME_DEDUCTION_RATE = 0.20
    
    def __init__(self):
        pass
    
    def calculate(self, household: SNAPHousehold) -> Dict:
        """
        Calculate SNAP benefits using screener methodology.
        
        Returns:
            Dictionary with calculation details and benefit amount
        """
        # Step 1: Calculate gross income
        gross_income = (
            household.monthly_earned_income + household.monthly_unearned_income
        )
        
        # Step 2: Check gross income eligibility
        gross_limit = self._get_limit(
            household.size, self.GROSS_INCOME_LIMITS
        )
        passes_gross_test = gross_income <= gross_limit
        
        # Step 3: Calculate deductions
        standard_deduction = self._get_limit(
            household.size, self.STANDARD_DEDUCTIONS
        )
        
        earned_income_deduction = (
            household.monthly_earned_income * self.EARNED_INCOME_DEDUCTION_RATE
        )
        
        # Medical expense deduction (only for elderly/disabled, over $35)
        medical_deduction = 0
        if household.has_elderly_disabled and household.monthly_medical_expenses > 35:
            medical_deduction = household.monthly_medical_expenses - 35
        
        # Step 4: Calculate adjusted income
        adjusted_income = (
            gross_income
            - standard_deduction
            - earned_income_deduction
            - household.monthly_dependent_care
            - household.monthly_child_support
            - medical_deduction
        )
        
        # Step 5: Calculate excess shelter deduction
        half_adjusted_income = adjusted_income / 2
        
        total_shelter_costs = household.monthly_rent
        if household.has_utility_expenses:
            # Add standard utility allowance (varies by state)
            # Using simplified amount for demonstration
            total_shelter_costs += 500  # Approximate SUA
        
        excess_shelter = max(0, total_shelter_costs - half_adjusted_income)
        
        # Apply cap if no elderly/disabled member
        if not household.has_elderly_disabled:
            excess_shelter = min(excess_shelter, self.EXCESS_SHELTER_CAP)
        
        # Step 6: Calculate net income
        net_income = adjusted_income - excess_shelter
        
        # Step 7: Check net income eligibility
        net_limit = self._get_limit(household.size, self.NET_INCOME_LIMITS)
        passes_net_test = net_income <= net_limit
        
        # Step 8: Calculate benefit amount
        max_allotment = self._get_limit(household.size, self.MAX_ALLOTMENTS)
        expected_contribution = max(0, net_income * 0.30)
        benefit_amount = max(0, max_allotment - expected_contribution)
        
        # Round benefit to nearest dollar
        benefit_amount = round(benefit_amount)
        
        return {
            "gross_income": gross_income,
            "gross_income_limit": gross_limit,
            "passes_gross_test": passes_gross_test,
            "standard_deduction": standard_deduction,
            "earned_income_deduction": earned_income_deduction,
            "dependent_care_deduction": household.monthly_dependent_care,
            "child_support_deduction": household.monthly_child_support,
            "medical_deduction": medical_deduction,
            "adjusted_income": adjusted_income,
            "excess_shelter_deduction": excess_shelter,
            "net_income": net_income,
            "net_income_limit": net_limit,
            "passes_net_test": passes_net_test,
            "max_allotment": max_allotment,
            "expected_contribution": expected_contribution,
            "benefit_amount": benefit_amount,
            "is_eligible": passes_gross_test and passes_net_test and benefit_amount > 0,
        }
    
    def _get_limit(self, household_size: int, limits: Dict[int, float]) -> float:
        """Get limit for household size, extrapolating if needed."""
        if household_size in limits:
            return limits[household_size]
        
        # For households larger than 8, add amount per additional person
        if household_size > 8:
            base = limits[8]
            # Approximate additional amount per person
            per_person = (limits[8] - limits[7])
            return base + (household_size - 8) * per_person
        
        return 0