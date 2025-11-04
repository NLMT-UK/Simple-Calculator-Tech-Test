import os
import shutil
import subprocess
import sys
from datetime import datetime

RESULTS_DIR = "reports/allure-results"
REQ_FILE = "requirements.txt"


def in_venv() -> bool:
    # Works for both venv and virtualenv
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def main() -> None:
    os.makedirs("reports", exist_ok=True)

    # If requirements.txt exists, install it (this is safe to run multiple times)
    if os.path.exists(REQ_FILE):
        print("Installing dependencies from requirements.txt...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            check=False,
        )
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", REQ_FILE],
            check=True,
        )

    # Clean previous results
    if os.path.exists(RESULTS_DIR):
        shutil.rmtree(RESULTS_DIR)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Run pytest (2 workers, do not stop on first failure)
    pytest_cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-n",
        "2",
        "--maxfail=0",
        "--alluredir=reports/allure-results",
    ]
    print("Running:", " ".join(pytest_cmd))
    pytest_proc = subprocess.run(pytest_cmd)
    if pytest_proc.returncode != 0:
        print("pytest finished with failures (this can be expected for defective builds)")

    # Generate timestamped report
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = os.path.join("reports", f"allure-report-{ts}")

    allure_path = shutil.which("allure")
    if not allure_path:
        print("Allure CLI not found on PATH.")
        print("Install with 'brew install allure' or 'pip install allure-commandline'.")
        print(f"Raw results are available in: {RESULTS_DIR}")
        return

    gen_cmd = ["allure", "generate", RESULTS_DIR, "-o", out_dir, "--clean"]
    print("Generating Allure report:", " ".join(gen_cmd))
    subprocess.run(gen_cmd, check=True)

    open_cmd = ["allure", "open", out_dir]
    print("Opening Allure report:", " ".join(open_cmd))
    subprocess.run(open_cmd, check=True)


if __name__ == "__main__":
    main()
