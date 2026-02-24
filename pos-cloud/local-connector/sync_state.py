import json, os, sys
from datetime import date, timedelta
import config as cfg

# Use sys.executable dir when frozen as .exe, __file__ dir when running as script
if getattr(sys, 'frozen', False):
    _BASE = os.path.dirname(sys.executable)
else:
    _BASE = os.path.dirname(os.path.abspath(__file__))
_STATE_PATH = os.path.join(_BASE, "last_sync.json")


def get_from_date() -> date:
    if os.path.exists(_STATE_PATH):
        try:
            with open(_STATE_PATH) as f:
                return date.fromisoformat(json.load(f)["last_sync_date"]) + timedelta(days=1)
        except Exception:
            pass
    return date.today() - timedelta(days=cfg.INITIAL_LOOKBACK_DAYS)


def save_sync_date(sync_date: date) -> None:
    with open(_STATE_PATH, "w") as f:
        json.dump({"last_sync_date": sync_date.isoformat()}, f)
