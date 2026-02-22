"""HTTPS POST to cloud API with retry + exponential backoff."""
import json, logging, time
import requests
import config as cfg

logger = logging.getLogger(__name__)
MAX_RETRIES = 3
BACKOFF_BASE = 5


def _headers():
    return {"X-API-Key": cfg.API_KEY, "Content-Type": "application/json"}


def test_health() -> bool:
    url = cfg.API_ENDPOINT.rstrip("/") + "/health"
    try:
        resp = requests.post(url, headers=_headers(), timeout=15)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error("Health check failed: %s", e); return False


def push_sync(payload: dict) -> dict:
    body = json.dumps(payload, default=str)
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info("Pushing sync (attempt %d/%d)…", attempt, MAX_RETRIES)
            resp = requests.post(cfg.API_ENDPOINT, data=body, headers=_headers(), timeout=120)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP %s on attempt %d: %s", e.response.status_code, attempt, e.response.text[:300])
            last_error = e
            if e.response.status_code < 500: raise
        except Exception as e:
            logger.error("Network error attempt %d: %s", attempt, e); last_error = e
        if attempt < MAX_RETRIES:
            secs = BACKOFF_BASE * (2 ** (attempt - 1))
            logger.info("Retrying in %ds…", secs); time.sleep(secs)
    raise RuntimeError(f"Cloud push failed after {MAX_RETRIES} attempts: {last_error}")
