from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
import asyncio

from services.timesheet_service import get_timesheet_data

router = APIRouter()


@router.websocket("/ws/timesheet/present-employees")
async def timesheet_ws(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            try:
                data = get_timesheet_data()

                if websocket.client_state != WebSocketState.CONNECTED:
                    break

                await websocket.send_json(data)

            except WebSocketDisconnect:
                print("Client disconnected")
                break

            except Exception as e:
                print("Data error:", e)

                try:
                    if websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.send_json({
                            "total_users": 0,
                            "error": "data_fetch_failed"
                        })
                except Exception:
                    break

            await asyncio.sleep(10)

    except asyncio.CancelledError:
        print("WebSocket task cancelled")

    except WebSocketDisconnect:
        print("Client disconnected")

    except Exception as e:
        print("WebSocket crashed:", e)

    finally:
        print("Connection closed")
