import os
import sys

import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
HEALTH_CHECKS = {
    "/": "RetailIQ API is running",
    "/eval/health": "Evaluation Harness Ready",
}


def run_eval() -> int:
    failures = []
    for path, expected_message in HEALTH_CHECKS.items():
        try:
            response = requests.get(f"{API_BASE_URL}{path}", timeout=5)
            response.raise_for_status()
            if expected_message not in response.json().values():
                failures.append(f"{path}: unexpected response body")
        except (requests.RequestException, ValueError) as exc:
            failures.append(f"{path}: {exc}")

    if failures:
        print("API smoke checks failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"API smoke checks passed ({len(HEALTH_CHECKS)}/{len(HEALTH_CHECKS)}).")
    return 0


if __name__ == "__main__":
    sys.exit(run_eval())
