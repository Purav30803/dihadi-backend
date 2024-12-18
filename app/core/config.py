from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_uri: str
    user_email: str
    user_password: str

    class Config:
        env_file = ".env"  # Specify the .env file to load environment variables

settings = Settings()  # This will automatically load the settings from the .env file

SECRET_KEY = "dihadi"
ALGORITHM = "HS256"