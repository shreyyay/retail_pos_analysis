import configparser, os

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_cfg = configparser.ConfigParser()
_cfg.read(os.path.join(_BASE_DIR, "config.ini"))

TALLY_HOST: str = _cfg.get("tally", "host", fallback="localhost")
TALLY_PORT: int = int(_cfg.get("tally", "port", fallback="9000"))
TALLY_URL: str = f"http://{TALLY_HOST}:{TALLY_PORT}"

API_ENDPOINT: str = _cfg.get("cloud", "api_endpoint")
API_KEY: str = _cfg.get("cloud", "api_key")
STORE_ID: str = _cfg.get("cloud", "store_id")

INITIAL_LOOKBACK_DAYS: int = int(_cfg.get("sync", "initial_lookback_days", fallback="7"))
MAX_DAYS_PER_SYNC: int = int(_cfg.get("sync", "max_days_per_sync", fallback="30"))
