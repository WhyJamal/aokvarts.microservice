import asyncio
import httpx

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketState

from core.config import settings
from services.energy.service import calculate_energy_total

router = APIRouter()


DEFAULT_DEVICE_IDS = [
    settings.ENERGY_DEVICE_ID_1,
    settings.ENERGY_DEVICE_ID_2,
]


async def stream_energy(
    websocket: WebSocket,
    device_ids: list[str | int],
):
    await websocket.accept()

    try:
        while True:
            try:
                energy_data = await calculate_energy_total(device_ids)

                if websocket.client_state != WebSocketState.CONNECTED:
                    break

                await websocket.send_json({
                    "device_ids": device_ids,
                    "energy": energy_data,
                })

            except httpx.HTTPStatusError as e:
                print(f"Energy HTTP error: {e.response.status_code}")

                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json({
                        "error": "energy_http_error"
                    })

            except httpx.RequestError as e:
                print(f"Energy connection error: {e}")

                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json({
                        "error": "energy_connection_error"
                    })

            except asyncio.CancelledError:
                print("WebSocket cancelled")
                break

            await asyncio.sleep(5)

    except Exception as e:
        print("WebSocket crashed:", e)

    finally:
        print("Connection closed")

        try:
            await websocket.close()
        except:
            pass


# ALL DEVICES
@router.websocket("/ws/data/energy")
async def energy_ws(websocket: WebSocket):
    await stream_energy(
        websocket,
        DEFAULT_DEVICE_IDS
    )


# SINGLE DEVICE
@router.websocket("/ws/data/energy/{device_id}")
async def energy_device_ws(
    websocket: WebSocket,
    device_id: str,
):
    await stream_energy(
        websocket,
        [device_id]
    )