from datetime import datetime, timedelta
from typing import Any
from .parser import unwrap, safe_float, ts_to_date

from .constants import PRICE_PER_KWH
from .client import MeterClient
from .date_range import get_date_range

def get_current_a_minus(payload: dict[str, Any]) -> float:
    return safe_float(unwrap(payload).get("A-", 0))


def get_billing_records(payload: dict[str, Any]) -> dict[str, Any]:
    data = unwrap(payload)
    return data.get("billing", data)


def find_yesterday_row(records: dict[str, Any], target_date):
    best = None

    for ts, row in records.items():
        if ts_to_date(ts) == target_date:
            ts_int = int(ts)
            if best is None or ts_int > best[0]:
                best = (ts_int, row)

    return best if best else (0, {"A-": 0})

async def calculate_period_energy(device_id: str, period: str):
    client = MeterClient()

    date1, date2 = get_date_range(period)

    res = await client.get_billing(device_id, {
        "date1": date1,
        "date2": date2,
        "limit": 1000,
        "page": 1,
    })

    data = get_billing_records(res.json())

    total = 0

    for row in data.values():
        total += float(row.get("A-", 0))

    return total

async def calculate_energy(device_id: str):
    client = MeterClient()

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    date1 = yesterday.strftime("%Y-%m-%d") + "T00:00:00.000"
    date2 = today.strftime("%Y-%m-%d") + "T00:00:00.000"

    current_res = await client.get_current(device_id)
    billing_res = await client.get_billing(device_id, {
        "date1": date1,
        "date2": date2,
        "limit": 100,
        "page": 1,
    })

    current_payload = current_res.json()
    billing_payload = billing_res.json()

    current = get_current_a_minus(current_payload)
    records = get_billing_records(billing_payload)

    _, row = find_yesterday_row(records, yesterday)
    yesterday_val = row.get("A-", 0)

    consumed = max(current - yesterday_val, 0)
    total = consumed * PRICE_PER_KWH

    return {
        "success": True,
        "device_id": device_id,
        "date": str(yesterday),
        "used_kwh": round(consumed, 3),
        "total_sum": round(total, 2),
    }
