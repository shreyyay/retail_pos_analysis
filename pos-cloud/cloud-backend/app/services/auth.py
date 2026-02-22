import hashlib

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tally import Store


def _hash_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_sync_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> Store:
    key_hash = _hash_key(x_api_key)
    store = db.query(Store).filter(
        Store.api_key_hash == key_hash,
        Store.is_active == True,  # noqa: E712
    ).first()
    if not store:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    return store


def generate_api_key(store_id: str) -> tuple[str, str]:
    """Return (plaintext_key, sha256_hash). Store only the hash."""
    import secrets
    plaintext = f"sk_{store_id}_{secrets.token_hex(24)}"
    return plaintext, _hash_key(plaintext)
