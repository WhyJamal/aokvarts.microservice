import asyncio
import httpx

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from services.onec_service import (
    get_hr_data,
    get_production_data,
)

router = APIRouter()


@router.websocket("/ws/dashboard/data")
async def onec_ws(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            try:
                hr_data, production_data = await asyncio.gather(
                    get_hr_data(),
                    get_production_data(),
                )

                if websocket.client_state != WebSocketState.CONNECTED:
                    break

                await websocket.send_json({
                    "hr": hr_data,
                    "production": production_data,
                })

            except httpx.HTTPStatusError as e:
                print(f"1C HTTP error: {e.response.status_code}")

                try:
                    if websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.send_json({
                            "error": "onec_http_error"
                        })
                except Exception:
                    break

            except httpx.RequestError as e:
                print(f"1C connection error: {e}")

                try:
                    if websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.send_json({
                            "error": "onec_connection_error"
                        })
                except Exception:
                    break

            except WebSocketDisconnect:
                print("Client disconnected")
                break

            await asyncio.sleep(40)

    except asyncio.CancelledError:
        print("WebSocket task cancelled")

    except WebSocketDisconnect:
        print("Client disconnected")

    except Exception as e:
        print("WebSocket crashed:", e)

    finally:
        print("Connection closed")
