import json
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]

LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "audit.jsonl"

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def write_audit_log(event: dict):

    event = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),

        **event
    }

    with open(
        LOG_FILE,
        "a",
        encoding="utf-8"
    ) as file:

        file.write(
            json.dumps(event) + "\n"
        )