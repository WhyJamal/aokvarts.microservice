from typing import Any
from datetime import datetime


def unwrap(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("data", payload)


def safe_float(value: Any) -> float:
    try:
        return float(value) if value is not None else 0.0
    except:
        return 0.0


def ts_to_date(ts: str | int):
    try:
        return datetime.fromtimestamp(int(ts) / 1000).date()
    except:
        return None