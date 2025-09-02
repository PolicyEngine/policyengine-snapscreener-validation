# PolicyEngine SNAP Screener Validation

A Python package for validating PolicyEngine US calculations against the SNAP screener (snapscreener.com) to identify and document calculation differences.

## Overview

This tool helps identify discrepancies between PolicyEngine's SNAP benefit calculations and the official SNAP screener. Key differences often include:

- **TANF Integration**: PolicyEngine automatically calculates TANF eligibility and includes it in SNAP gross income calculations
- **Utility Allowances**: Different handling of Standard Utility Allowances (SUA) 
- **Parameter Years**: PolicyEngine uses current year parameters while SNAP screener may use previous year values

## Installation

```bash
# Clone the repository
git clone https://github.com/PolicyEngine/policyengine-snapscreener-validation.git
cd policyengine-snapscreener-validation

# Install the package
pip install -e .

# For development
pip install -e ".[dev]"

# Install Playwright browsers (for web scraping)
playwright install chromium
```

## Quick Start

### Command Line Interface

```bash
# Basic comparison
snap-validate compare --income 2500 --rent 1500

# Without TANF (more comparable to SNAP screener)
snap-validate compare --income 2500 --rent 1500 --no-tanf

# With Standard Utility Allowance
snap-validate compare --income 4000 --rent 1500 --with-sua

# Output as JSON
snap-validate compare --income 2500 --rent 1500 --json

# Use web scraper (experimental)
snap-validate compare --income 2500 --rent 1500 --scrape
```

### Python API

```python
from policyengine_snapscreener_validation import (
    SNAPHousehold,
    SNAPValidator
)

# Create a household
household = SNAPHousehold(
    size=4,
    monthly_earned_income=2500,
    monthly_unearned_income=0,
    monthly_rent=1500,
    state="CA"
)

# Create validator
validator = SNAPValidator()

# Run comparison
result = validator.validate_single(
    household,
    year=2025,
    include_tanf=True,  # PolicyEngine default
    trigger_sua=False
)

# Print formatted comparison
validator.print_comparison(result)
```

### Batch Validation

Create a scenarios file (`scenarios.json`):

```json
[
    {
        "name": "Low income family",
        "household": {
            "size": 4,
            "monthly_earned_income": 2500,
            "monthly_unearned_income": 0,
            "monthly_rent": 1500,
            "state": "CA"
        },
        "options": {
            "include_tanf": true,
            "trigger_sua": false
        }
    }
]
```

Run batch validation:

```bash
snap-validate batch --scenarios scenarios.json --output results.csv
```

## Key Findings

### Example: Family of 4 with $2,500/month income

| Calculator | SNAP Benefit | Notes |
|------------|-------------|-------|
| SNAP Screener | $622/month | Based on reported income only |
| PolicyEngine | $419/month | Includes $466/month TANF in gross income |
| PolicyEngine (no TANF) | $622/month | Matches SNAP screener |

### Why the Difference?

1. **TANF Auto-calculation**: PolicyEngine automatically determines TANF eligibility and includes it as unearned income for SNAP, while the SNAP screener only includes benefits you explicitly report.

2. **Standard Utility Allowance**: PolicyEngine may apply California's SUA ($645/month) differently than the SNAP screener.

3. **Parameter Updates**: PolicyEngine uses 2025 values while SNAP screener may use 2024 values.

## Components

### `SNAPScreenerCalculator`
Implements the SNAP screener's calculation methodology using 2024 federal SNAP rules.

### `PolicyEngineCalculator`
Wrapper around PolicyEngine US for SNAP calculations with options to control TANF and SUA.

### `SNAPScreenerScraper`
Playwright-based web scraper for getting results directly from snapscreener.com (experimental).

### `SNAPValidator`
Main validation class that compares results and generates reports.

## Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest tests/ --cov=policyengine_snapscreener_validation
```

## Development

```bash
# Format code
black policyengine_snapscreener_validation/
isort policyengine_snapscreener_validation/

# Lint
flake8 policyengine_snapscreener_validation/
```

## Limitations

- Web scraping is fragile and may break with website changes
- SNAP screener calculations are approximations based on observed methodology
- State-specific rules may not be fully captured
- Categorical eligibility rules may differ

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
- Open an issue on GitHub
- Contact PolicyEngine at hello@policyengine.org