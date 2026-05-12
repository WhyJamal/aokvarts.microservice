import httpx
from core.config import settings

_client = httpx.AsyncClient(
    base_url=settings.ONEC_BASE_URL,
    auth=(settings.ONEC_USER, settings.ONEC_PASS),
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
    timeout=15.0,
)

async def get_hr_data():
    res = await _client.get("/v1/hr/data")
    res.raise_for_status()
    return res.json()

async def get_production_data():
    res = await _client.get("/v1/production/data")
    res.raise_for_status()
    return res.json()