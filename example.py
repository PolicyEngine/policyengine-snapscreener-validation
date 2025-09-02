"""Example usage of the SNAP validation package"""

from policyengine_snapscreener_validation import (
    SNAPHousehold,
    SNAPValidator,
)


def main():
    """Run example validation comparisons"""
    
    # Create validator
    validator = SNAPValidator()
    
    print("=" * 70)
    print("PolicyEngine vs SNAP Screener Validation Examples")
    print("=" * 70)
    
    # Example 1: Your original scenario
    print("\nExample 1: Family of 4, $2,500/month income, $1,500/month rent")
    print("-" * 70)
    
    household1 = SNAPHousehold(
        size=4,
        monthly_earned_income=2500,
        monthly_unearned_income=0,
        monthly_rent=1500,
        state="CA"
    )
    
    # With TANF (PolicyEngine default)
    result1a = validator.validate_single(household1, include_tanf=True)
    print(f"With TANF:    SNAP Screener: ${result1a['screener_benefit']:.2f}, "
          f"PolicyEngine: ${result1a['policyengine_benefit']:.2f}")
    if result1a['tanf_included']:
        print(f"              (TANF included: ${result1a['tanf_amount']:.2f}/month)")
    
    # Without TANF (more comparable)
    result1b = validator.validate_single(household1, include_tanf=False)
    print(f"Without TANF: SNAP Screener: ${result1b['screener_benefit']:.2f}, "
          f"PolicyEngine: ${result1b['policyengine_benefit']:.2f}")
    
    # Example 2: Higher income scenario
    print("\nExample 2: Family of 4, $4,000/month income, $1,500/month rent")
    print("-" * 70)
    
    household2 = SNAPHousehold(
        size=4,
        monthly_earned_income=4000,
        monthly_unearned_income=0,
        monthly_rent=1500,
        state="CA"
    )
    
    result2 = validator.validate_single(household2, include_tanf=False)
    print(f"SNAP Screener: ${result2['screener_benefit']:.2f}")
    print(f"PolicyEngine:  ${result2['policyengine_benefit']:.2f}")
    
    # With SUA
    result2_sua = validator.validate_single(household2, include_tanf=False, trigger_sua=True)
    print(f"With SUA:      ${result2_sua['policyengine_benefit']:.2f}")
    
    print("\n" + "=" * 70)
    print("Key Insights:")
    print("- PolicyEngine includes TANF by default, increasing gross income")
    print("- SNAP screener only includes income you explicitly report")
    print("- Standard Utility Allowance can significantly affect benefits")
    print("=" * 70)


if __name__ == "__main__":
    main()