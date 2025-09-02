"""Web scraper for SNAP screener using Playwright"""

import re
import time
from typing import Dict, Optional

from playwright.sync_api import Page, sync_playwright

from .calculator import SNAPHousehold


class SNAPScreenerScraper:
    """Scrapes SNAP screener website for benefit calculations using Playwright"""

    BASE_URL = "https://www.snapscreener.com"

    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize the scraper.

        Args:
            headless: Run browser in headless mode
            timeout: Default timeout in milliseconds
        """
        self.headless = headless
        self.timeout = timeout

    def calculate(self, household: SNAPHousehold) -> Optional[Dict]:
        """
        Calculate SNAP benefits by scraping the screener website.

        Args:
            household: Household configuration

        Returns:
            Dictionary with scraped results or None if failed
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()
            page.set_default_timeout(self.timeout)

            try:
                result = self._run_calculation(page, household)
                return result
            except Exception as e:
                print(f"Scraping error: {e}")
                return None
            finally:
                browser.close()

    def _run_calculation(
        self, page: Page, household: SNAPHousehold
    ) -> Optional[Dict]:
        """Run the actual calculation on the website."""

        # Navigate to the screener
        page.goto(self.BASE_URL)
        page.wait_for_load_state("networkidle")

        # Select state
        if not self._select_state(page, household.state):
            return None

        # Fill out the form
        if not self._fill_form(page, household):
            return None

        # Submit and get results
        return self._get_results(page)

    def _select_state(self, page: Page, state: str) -> bool:
        """Select the state from dropdown or link."""
        try:
            # Map state code to full name
            state_names = {
                "CA": "California",
                "NY": "New York",
                "TX": "Texas",
                "FL": "Florida",
                # Add more as needed
            }

            state_name = state_names.get(state, state)

            # Try dropdown first
            state_select = page.locator("select").first
            if state_select.is_visible():
                state_select.select_option(label=state_name)
                time.sleep(1)
                return True

            # Try clicking state link
            state_link = page.locator(f'text="{state_name}"').first
            if state_link.is_visible():
                state_link.click()
                page.wait_for_load_state("networkidle")
                return True

            # Try direct URL
            page.goto(f"{self.BASE_URL}/screener?state={state}")
            page.wait_for_load_state("networkidle")
            return True

        except Exception as e:
            print(f"Failed to select state: {e}")
            return False

    def _fill_form(self, page: Page, household: SNAPHousehold) -> bool:
        """Fill out the SNAP screener form."""
        try:
            # Wait for form to be ready
            time.sleep(2)

            # Look for "Get Started" or similar button
            start_buttons = [
                "Get Started",
                "Start",
                "Begin",
                "Check Eligibility",
            ]
            for btn_text in start_buttons:
                btn = page.locator(f'button:has-text("{btn_text}")').first
                if btn.is_visible():
                    btn.click()
                    time.sleep(2)
                    break

            # Try to fill inputs by position (common order)
            inputs = page.locator(
                'input[type="number"], input[type="text"]'
            ).all()

            if len(inputs) >= 7:
                # Household size
                inputs[0].fill(str(household.size))

                # Monthly earned income
                inputs[1].fill(str(int(household.monthly_earned_income)))

                # Monthly unearned income
                inputs[2].fill(str(int(household.monthly_unearned_income)))

                # Dependent care
                inputs[3].fill(str(int(household.monthly_dependent_care)))

                # Child support
                inputs[4].fill(str(int(household.monthly_child_support)))

                # Rent
                inputs[5].fill(str(int(household.monthly_rent)))

                # Homeowners costs
                inputs[6].fill("0")

            # Handle radio buttons (elderly/disabled, student, homeless)
            radio_buttons = page.locator(
                'input[type="radio"][value="false"]'
            ).all()
            for radio in radio_buttons:
                if radio.is_visible():
                    radio.click()

            # Handle utility checkboxes if needed
            if household.has_utility_expenses:
                # Check heating/cooling to trigger SUA
                heating_checkbox = page.locator(
                    'input[type="checkbox"][name*="heating"], '
                    'input[type="checkbox"][value*="heating"]'
                ).first
                if heating_checkbox.is_visible():
                    heating_checkbox.check()

            return True

        except Exception as e:
            print(f"Failed to fill form: {e}")
            return False

    def _get_results(self, page: Page) -> Optional[Dict]:
        """Submit form and extract results."""
        try:
            # Submit the form
            submit_buttons = ["Calculate", "Get Results", "Submit", "Check"]
            for btn_text in submit_buttons:
                btn = page.locator(f'button:has-text("{btn_text}")').first
                if btn.is_visible():
                    btn.click()
                    break

            # Wait for results
            time.sleep(3)
            page.wait_for_load_state("networkidle")

            # Extract benefit amount
            page_text = page.inner_text("body")

            # Look for benefit amount patterns
            patterns = [
                r"may be \$(\d+)",
                r"benefit.*?\$(\d+)",
                r"\$(\d+).*?per month",
                r"could receive.*?\$(\d+)",
                r"estimated.*?\$(\d+)",
                r"eligible for.*?\$(\d+)",
            ]

            for pattern in patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    benefit = int(matches[0])

                    # Extract other details if available
                    result = {
                        "benefit_amount": benefit,
                        "is_eligible": benefit > 0,
                        "source": "snapscreener.com",
                    }

                    # Try to extract gross/net income if shown
                    gross_match = re.search(
                        r"gross income.*?\$(\d+)", page_text, re.IGNORECASE
                    )
                    if gross_match:
                        result["gross_income"] = int(gross_match.group(1))

                    net_match = re.search(
                        r"net income.*?\$(\d+)", page_text, re.IGNORECASE
                    )
                    if net_match:
                        result["net_income"] = int(net_match.group(1))

                    return result

            # Check if not eligible
            if (
                "not eligible" in page_text.lower()
                or "ineligible" in page_text.lower()
            ):
                return {
                    "benefit_amount": 0,
                    "is_eligible": False,
                    "source": "snapscreener.com",
                }

            return None

        except Exception as e:
            print(f"Failed to get results: {e}")
            return None
