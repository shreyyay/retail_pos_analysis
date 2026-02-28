import configparser, os, sys

if getattr(sys, 'frozen', False):
    # Frozen exe lives in {app}\subdir\ (e.g. tally_sync\ or TallySyncSetup\)
    # config.ini is one level up in {app}\
    _BASE_DIR = os.path.dirname(os.path.dirname(sys.executable))
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_cfg = configparser.ConfigParser()
_cfg.read(os.path.join(_BASE_DIR, "config.ini"))

TALLY_HOST: str = _cfg.get("tally", "host", fallback="localhost")
TALLY_PORT: int = int(_cfg.get("tally", "port", fallback="9000"))
TALLY_URL: str = f"http://{TALLY_HOST}:{TALLY_PORT}"

SUPABASE_DB_URL: str = _cfg.get("supabase", "db_url")
STORE_ID: str = _cfg.get("supabase", "store_id")

INITIAL_LOOKBACK_DAYS: int = int(_cfg.get("sync", "initial_lookback_days", fallback="7"))
MAX_DAYS_PER_SYNC: int = int(_cfg.get("sync", "max_days_per_sync", fallback="30"))

GROQ_API_KEY: str = _cfg.get("groq", "api_key", fallback="")
GROQ_MODEL: str   = _cfg.get("groq", "model", fallback="llama-3.3-70b-versatile")
