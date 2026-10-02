from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="API_", env_file=".env", extra="ignore")
    host: str = "127.0.0.1"  # solo localhost
    port: int = 8000
    max_items: int = 100


settings = Settings()
