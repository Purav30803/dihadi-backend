from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_uri: str

    class Config:
        env_file = ".env"  # Specify the .env file to load environment variables

settings = Settings()  # This will automatically load the settings from the .env file
