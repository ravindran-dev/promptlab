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
        default="",
        validation_alias="GOOGLE_API_KEY"
    )
    LLM_PROVIDER: str = Field(
        default="ollama",
        validation_alias="LLM_PROVIDER"
    )
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        validation_alias="OLLAMA_BASE_URL"
    )
    OLLAMA_MODEL: str = Field(
        default="qwen3.5",
        validation_alias="OLLAMA_MODEL"
    )
    OLLAMA_JUDGE_MODEL: str = Field(
        default="qwen3.5",
        validation_alias="OLLAMA_JUDGE_MODEL"
    )
    OLLAMA_TIMEOUT_SECONDS: int = Field(
        default=120,
        validation_alias="OLLAMA_TIMEOUT_SECONDS"
    )
    OLLAMA_KEEP_ALIVE: str = Field(
        default="5m",
        validation_alias="OLLAMA_KEEP_ALIVE"
    )
    OLLAMA_MAX_TOKENS: int = Field(default=1800, validation_alias="OLLAMA_MAX_TOKENS")
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

    @property
    def provider(self) -> str:
        provider = self.LLM_PROVIDER.strip().lower()
        if provider not in {"ollama", "gemini"}:
            raise ValueError(f"Unsupported LLM_PROVIDER: {provider}. Use ollama or gemini.")
        return provider

    @property
    def generator_model(self) -> str:
        return self.OLLAMA_MODEL if self.provider == "ollama" else self.GEMINI_MODEL

    @property
    def judge_model(self) -> str:
        return self.OLLAMA_JUDGE_MODEL if self.provider == "ollama" else self.JUDGE_MODEL

    @property
    def generator_max_tokens(self) -> int:
        return self.OLLAMA_MAX_TOKENS if self.provider == "ollama" else self.GEMINI_MAX_TOKENS

    class Config:
        env_file = (
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
            ".env"
        )
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
