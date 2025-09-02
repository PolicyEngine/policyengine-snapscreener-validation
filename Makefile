.PHONY: install test format lint clean

install:
	pip install -e ".[dev]"
	playwright install chromium

test:
	pytest tests/ -v --cov=policyengine_snapscreener_validation --cov-report=term

format:
	black policyengine_snapscreener_validation/ tests/
	isort policyengine_snapscreener_validation/ tests/

lint:
	black --check policyengine_snapscreener_validation/ tests/
	isort --check-only policyengine_snapscreener_validation/ tests/
	flake8 policyengine_snapscreener_validation/ tests/ --max-line-length=79 --extend-ignore=E203,W503

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -f *.png *.html results.csv