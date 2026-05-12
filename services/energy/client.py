import httpx
from core.config import settings


class MeterClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=settings.METER_BASE_API,
            auth=(settings.METER_USER, settings.METER_PASS),
            timeout=20.0,
        )

    async def get_current(self, device_id: str):
        return await self.client.get(f"/v2/current/{device_id}")

    async def get_billing(self, device_id: str, params: dict):
        return await self.client.get(f"/v2/billing/{device_id}", params=params)