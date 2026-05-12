from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ONEC_BASE_URL: str
    ONEC_USER: str
    ONEC_PASS: str

    METER_BASE_API: str
    METER_USER: str
    METER_PASS: str

    TIMESHEET_URL: str

    ENERGY_DEVICE_ID_1: str
    ENERGY_DEVICE_ID_2: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()

DATABASES = {
    "timesheet": settings.TIMESHEET_URL,
}