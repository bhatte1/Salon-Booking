from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Loads variables from .env in the backend folder
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)
    DATABASE_URL: str

settings = Settings()
