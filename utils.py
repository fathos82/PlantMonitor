from datetime import datetime, timezone


def get_instant() -> str:
    """Retorna o instante atual em formato ISO 8601 UTC."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")