import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default="postgresql://promptuser:promptpass@localhost:5432/promptbench",
        validation_alias="DATABASE_URL"
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="REDIS_URL"
    )
    GOOGLE_API_KEY: str = Field(
        default="mock-key-if-not-set",
        validation_alias="GOOGLE_API_KEY"
    )
    GEMINI_MODEL: str = Field(
        default="gemini-2.5-pro",
        validation_alias="GEMINI_MODEL"
    )
    JUDGE_MODEL: str = Field(
        default="gemini-2.5-flash",
        validation_alias="JUDGE_MODEL"
    )
    GEMINI_MAX_TOKENS: int = Field(
        default=1800,
        validation_alias="GEMINI_MAX_TOKENS"
    )
    JUDGE_MAX_TOKENS: int = Field(
        default=800,
        validation_alias="JUDGE_MAX_TOKENS"
    )
    BACKEND_PORT: int = Field(
        default=8000,
        validation_alias="BACKEND_PORT"
    )
    HOST: str = Field(
        default="0.0.0.0",
        validation_alias="HOST"
    )

    class Config:
        env_file = (
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
            ".env"
        )
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
