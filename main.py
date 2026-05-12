from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import timesheet_ws, onec_ws, energy_ws
from services.go2rtc_service import start_go2rtc, stop_go2rtc

app = FastAPI()

# @app.on_event("startup")
# async def startup():
#     start_go2rtc()


# @app.on_event("shutdown")
# async def shutdown():
#     stop_go2rtc()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(timesheet_ws.router)
app.include_router(onec_ws.router)
app.include_router(energy_ws.router)

