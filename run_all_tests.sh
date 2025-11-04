#!/usr/bin/env bash

# Optional: use local venv if it exists
if [ -d ".venv" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
  echo "Using virtualenv from .venv/"
fi

# Ensure reports dir exists
mkdir -p reports

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
  echo "Installing dependencies from requirements.txt (if already installed, this is a no-op)..."
  python -m pip install --upgrade pip >/dev/null 2>&1 || true
  python -m pip install -r requirements.txt
fi

# Clean previous allure raw results
rm -rf reports/allure-results
mkdir -p reports/allure-results

# Run pytest (allow failures so we can still generate the report)
python -m pytest \
  -n 2 \
  --maxfail=0 \
  --alluredir=reports/allure-results || echo "pytest finished with failures (expected for defective builds)"

# Generate a timestamped allure report
TS=$(date +"%Y-%m-%d_%H-%M-%S")
OUT_DIR="reports/allure-report-$TS"

if command -v allure >/dev/null 2>&1; then
  allure generate reports/allure-results -o "$OUT_DIR" --clean
  allure open "$OUT_DIR"
else
  echo "allure CLI not found on PATH."
  echo "Install with: brew install allure   or   pip install allure-commandline"
  echo "Raw results are in reports/allure-results"
fi
