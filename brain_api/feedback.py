"""User feedback on answers: thumbs up/down under every Chat and Design
response.

A thumbs-down stores the question and the answer it rated into a CSV on
the data volume. Every time the batch threshold is reached (10 rows by
default) the rows are emailed to the maintainer through the Resend API,
moved into an archive CSV (never deleted: the archive is future
evaluation data), and the active file starts again empty. If the email
cannot be sent (no key configured, network down) nothing is lost: rows
keep accumulating and the send is retried on the next thumbs-down.
"""

import csv
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

import requests

DATA_DIR = Path(os.environ["DATA_DIR"]) if os.environ.get("DATA_DIR") \
    else Path(__file__).resolve().parents[1] / "data"
ACTIVE_CSV = DATA_DIR / "feedback.csv"
ARCHIVE_CSV = DATA_DIR / "feedback_archive.csv"
UP_CSV = DATA_DIR / "feedback_up.csv"

FIELDS = ["timestamp_utc", "mode", "question", "answer"]
BATCH_SIZE = int(os.environ.get("FEEDBACK_BATCH_SIZE", "10"))
EMAIL_TO = os.environ.get("FEEDBACK_EMAIL_TO", "pierreguyatangana@yahoo.fr")
MAX_FIELD_CHARS = 8000  # keep one runaway answer from bloating the file

_lock = threading.Lock()


def _append(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


def _read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _send_report(rows: list[dict]) -> bool:
    key = os.environ.get("RESEND_API_KEY")
    if not key:
        print("[feedback] RESEND_API_KEY not set; report deferred "
              f"({len(rows)} rows waiting)")
        return False
    parts = [f"GeoTutor received {len(rows)} thumbs-down ratings.", ""]
    for i, r in enumerate(rows, 1):
        parts += [f"--- #{i}  [{r['mode']}]  {r['timestamp_utc']} ---",
                  "QUESTION:", r["question"], "",
                  "ANSWER GIVEN:", r["answer"], ""]
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {key}"},
            json={"from": "GeoTutor Feedback <onboarding@resend.dev>",
                  "to": [EMAIL_TO],
                  "subject": f"GeoTutor feedback report: {len(rows)} "
                             "unsatisfied answers",
                  "text": "\n".join(parts)},
            timeout=30)
        if resp.status_code in (200, 201):
            return True
        print(f"[feedback] Resend refused the report: {resp.status_code} "
              f"{resp.text[:200]}")
        return False
    except Exception as e:
        print(f"[feedback] report email failed: {e}")
        return False


def record(mode: str, rating: str, question: str, answer: str) -> dict:
    """Store one rating; on a full thumbs-down batch, email + archive it."""
    row = {"timestamp_utc": datetime.now(timezone.utc)
           .strftime("%Y-%m-%d %H:%M:%S"),
           "mode": mode,
           "question": (question or "")[:MAX_FIELD_CHARS],
           "answer": (answer or "")[:MAX_FIELD_CHARS]}
    with _lock:
        if rating == "up":
            _append(UP_CSV, row)
            return {"saved": True, "reported": False}
        _append(ACTIVE_CSV, row)
        rows = _read_rows(ACTIVE_CSV)
        if len(rows) < BATCH_SIZE:
            return {"saved": True, "reported": False}
        if not _send_report(rows):
            return {"saved": True, "reported": False}
        # sent: move the batch to the archive, restart the active file
        for r in rows:
            _append(ARCHIVE_CSV, r)
        with open(ACTIVE_CSV, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()
        return {"saved": True, "reported": True}
