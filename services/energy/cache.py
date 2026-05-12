from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any


class EnergyCache:
    """
    Monthly va yearly ma'lumotlarni cache qiladi.
    Har soatda avtomatik yangilaydi.

    Ishlatish:
        cache = EnergyCache(device_ids, calculate_period_fn)
        await cache.start()
        data = cache.get()
    """

    REFRESH_INTERVAL = 3600  # 1 soat

    def __init__(
        self,
        device_ids: list[str],
        refresh_fn,  # async callable(device_ids) -> dict
    ):
        self._device_ids = device_ids
        self._refresh_fn = refresh_fn
        self._data: dict[str, Any] = {}
        self._last_updated: datetime | None = None
        self._task: asyncio.Task | None = None
        self._ready = asyncio.Event()

    async def start(self) -> None:
        """Background refresh task ni boshlaydi."""
        self._task = asyncio.create_task(self._run())
        # Birinchi ma'lumot tayyor bo'lgunicha kut
        await self._ready.wait()

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def get(self) -> dict[str, Any]:
        return self._data

    @property
    def last_updated(self) -> datetime | None:
        return self._last_updated

    async def _run(self) -> None:
        while True:
            try:
                self._data = await self._refresh_fn(self._device_ids)
                self._last_updated = datetime.now()
                self._ready.set()
            except Exception as e:
                print(f"[EnergyCache] Refresh error: {e}")
                self._ready.set()  # xato bo'lsa ham block qilmasin

            await asyncio.sleep(self.REFRESH_INTERVAL)