from pathlib import Path
import subprocess

process = None

BASE_DIR = Path(__file__).resolve().parent.parent

GO2RTC_DIR = BASE_DIR / "app" / "go2rtc"
GO2RTC_EXE = GO2RTC_DIR / "go2rtc.exe"


def start_go2rtc():
    global process

    if process is None:
        process = subprocess.Popen(
            [str(GO2RTC_EXE)],
            cwd=str(GO2RTC_DIR)
        )


def stop_go2rtc():
    global process

    if process:
        process.kill()
        process = None