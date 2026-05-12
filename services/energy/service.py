from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, date
from calendar import monthrange
from typing import Any

from .client import MeterClient
from .calculator import (
    get_current_a_minus,
    get_billing_records,
    find_yesterday_row,
)
from .constants import PRICE_PER_KWH


def _prev_month_bounds() -> tuple[str, str]:
    """
    Oldingi oyning 1-kunidan oxirgi kuniga qadar.
    Misol: hozir 09.05.2026 -> 2026-04-01 00:00 .. 2026-04-30 23:59 (inclusive)

    Billing API snapshot ma'lumot beradi, ya'ni har kun oxirgi holatni saqlaydi.
    Shuning uchun date2 ni keyingi oy 1-kuni qilib beramiz (exclusive upper bound).
    """
    today = datetime.now().date()
    first_day_this_month = today.replace(day=1)
    first_day_prev_month = (first_day_this_month - timedelta(days=1)).replace(day=1)

    # Oldingi oy necha kun: masalan aprel -> 30 kun
    _, last_day = monthrange(first_day_prev_month.year, first_day_prev_month.month)
    last_day_prev_month = first_day_prev_month.replace(day=last_day)

    # date1 = oldingi oy 1-kuni, date2 = shu oy 1-kuni (exclusive)
    date1 = first_day_prev_month.strftime("%Y-%m-%d") + "T00:00:00.000"
    date2 = first_day_this_month.strftime("%Y-%m-%d") + "T00:00:00.000"

    return date1, date2, first_day_prev_month, last_day_prev_month


def _current_month_bounds() -> tuple[str, str, date, date]:
    today = datetime.now().date()
    first_day_this_month = today.replace(day=1)
    tomorrow = today + timedelta(days=1)

    date1 = first_day_this_month.strftime("%Y-%m-%d") + "T00:00:00.000"
    date2 = tomorrow.strftime("%Y-%m-%d") + "T00:00:00.000"

    return date1, date2, first_day_this_month, today 


def _current_year_bounds() -> tuple[str, str]:
    """
    Joriy yilning 1-yanvaridan bugungi kunga qadar.
    Misol: hozir 09.05.2026 -> 2026-01-01 .. 2026-05-10
    """
    today = datetime.now().date()
    first_day_this_year = today.replace(month=1, day=1)
    tomorrow = today + timedelta(days=1)

    date1 = first_day_this_year.strftime("%Y-%m-%d") + "T00:00:00.000"
    date2 = tomorrow.strftime("%Y-%m-%d") + "T00:00:00.000"

    return date1, date2


def _extract_kwh_from_records(records: dict[str, Any]) -> tuple[float, float]:
    """
    Recordlardan birinchi va oxirgi A- qiymatini qaytaradi.
    Records: { "1774983600000": { "A-": 554.367, ... }, ... }

    Timestamp (millisecond) bo'yicha sort qilinadi.
    Return: (first_a_minus, last_a_minus)
    """
    if not records:
        return 0.0, 0.0

    # Timestamp key larni int ga aylantirib sort qilamiz
    sorted_items = sorted(
        records.items(),
        key=lambda x: int(x[0]) if str(x[0]).isdigit() else 0,
    )

    first_val = float(sorted_items[0][1].get("A-", 0) or 0)
    last_val = float(sorted_items[-1][1].get("A-", 0) or 0)

    return first_val, last_val


def _delta_kwh(records: dict[str, Any]) -> float:
    """Birinchi va oxirgi o'rtasidagi farq (kWh)."""
    first_val, last_val = _extract_kwh_from_records(records)
    return max(last_val - first_val, 0.0)


async def _fetch_period_records(
    client: MeterClient,
    device_id: str,
    date1: str,
    date2: str,
    limit: int = 1000,
) -> dict[str, Any]:
    """Berilgan davr uchun billing recordlarni yuklaydi."""
    res = await client.get_billing(
        device_id,
        {
            "date1": date1,
            "date2": date2,
            "limit": limit,
            "page": 1,
        },
    )
    payload = res.json()
    return get_billing_records(payload)


# ---------------------------------------------------------------------------
# Kecha sarflangan energiya (1 ta device)
# ---------------------------------------------------------------------------

async def calculate_energy(device_id: str) -> dict[str, Any]:
    """
    Kecha sarflangan kWh va summa.
    Hisoblash: current_A_minus - yesterday_snapshot_A_minus
    """
    try:
        client = MeterClient()

        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        date1 = yesterday.strftime("%Y-%m-%d") + "T00:00:00.000"
        date2 = today.strftime("%Y-%m-%d") + "T00:00:00.000"

        current_res = await client.get_current(device_id)
        billing_res = await client.get_billing(
            device_id,
            {"date1": date1, "date2": date2, "limit": 100, "page": 1},
        )

        current_payload = current_res.json()
        billing_payload = billing_res.json()

        current = get_current_a_minus(current_payload)
        records = get_billing_records(billing_payload)

        _, row = find_yesterday_row(records, yesterday)
        yesterday_val = float(row.get("A-", 0) or 0)

        used_kwh = max(current - yesterday_val, 0.0)
        total_sum = used_kwh * PRICE_PER_KWH

        return {
            "success": True,
            "device_id": device_id,
            "date": str(yesterday),
            "current_a_minus": round(current, 3),
            "yesterday_snapshot": round(yesterday_val, 3),
            "used_kwh": round(used_kwh, 3),
            "total_sum": round(total_sum, 2),
            "error": None,
        }

    except Exception as e:
        return {
            "success": False,
            "device_id": device_id,
            "date": None,
            "current_a_minus": 0,
            "yesterday_snapshot": 0,
            "used_kwh": 0,
            "total_sum": 0,
            "error": str(e),
        }


# ---------------------------------------------------------------------------
# Davr bo'yicha energiya (1 ta device)
# ---------------------------------------------------------------------------

async def calculate_period_energy(device_id: str, period: str) -> dict[str, Any]:
    """
    'month' yoki 'year' davri uchun kWh hisoblaydi.

    month -> OLDINGI oy (1-kundan oxirgi kungacha)
    year  -> JORIY yil (1-yanvardan bugunga qadar)

    Hisoblash: last_snapshot_A_minus - first_snapshot_A_minus
    """
    client = MeterClient()

    if period == "month":
        date1, date2, period_start, period_end = _current_month_bounds()
    elif period == "year":
        date1, date2 = _current_year_bounds()
        period_start = None
        period_end = None
    else:
        raise ValueError(f"Unsupported period: {period!r}. Use 'month' or 'year'.")

    records = await _fetch_period_records(client, device_id, date1, date2)

    first_val, last_val = _extract_kwh_from_records(records)
    used_kwh = max(last_val - first_val, 0.0)

    return {
        "device_id": device_id,
        "period": period,
        "date1": date1,
        "date2": date2,
        "first_snapshot": round(first_val, 3),
        "last_snapshot": round(last_val, 3),
        "used_kwh": round(used_kwh, 3),
    }


# ---------------------------------------------------------------------------
# Barcha devicelar uchun umumiy hisob
# ---------------------------------------------------------------------------

async def calculate_energy_total(device_ids: list[str]) -> dict[str, Any]:
    """
    Barcha devicelar bo'yicha:
    - kecha sarflangan kWh va summa
    - oldingi oy sarflangan kWh
    - joriy yil sarflangan kWh

    Har bir device mustaqil hisoblanadi, keyin qo'shiladi.

    Misol (2 ta device, month):
        device1: last(596.727) - first(554.367) = 42.36 kWh
        device2: last(663.018) - first(587.587) = 75.43 kWh  (agar ikkinchi device)
        monthly_used = 42.36 + 75.43 = 117.79 kWh
    """
    daily_results, monthly_results, yearly_results = await asyncio.gather(
        asyncio.gather(*(calculate_energy(did) for did in device_ids)),
        asyncio.gather(*(calculate_period_energy(did, "month") for did in device_ids)),
        asyncio.gather(*(calculate_period_energy(did, "year") for did in device_ids)),
    )

    yesterday_used = sum(r["used_kwh"] for r in daily_results)
    yesterday_sum = round(yesterday_used * PRICE_PER_KWH, 2)
    total_sum = sum(r["total_sum"] for r in daily_results)
    monthly_used = sum(r["used_kwh"] for r in monthly_results)
    yearly_used = sum(r["used_kwh"] for r in yearly_results)

    monthly_sum = round(monthly_used * PRICE_PER_KWH, 2)
    yearly_sum = round(yearly_used * PRICE_PER_KWH, 2)

    return {
        # Har bir device alohida natijalari
        "devices": {
            "daily": list(daily_results),
            "monthly": list(monthly_results),
            "yearly": list(yearly_results),
        },
        # Umumiy ko'rsatkichlar
        "yesterday_used": round(yesterday_used, 3),
        "yesterday_sum": yesterday_sum,
        "total_sum": round(total_sum, 2),
        "monthly_used": round(monthly_used, 3),
        "monthly_sum": monthly_sum,       # 100.471 kWh × 28000 = 2,813,188 so'm
        "yearly_used": round(yearly_used, 3),
        "yearly_sum": yearly_sum,         # yearly_used × 28000
    }