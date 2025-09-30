from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    GEMINI_API_KEY: str

    DISCORD_TOKEN: str

    LANGSMITH_TRACING: bool = True
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGSMITH_API_KEY: str
    LANGSMITH_PROJECT: str = "discord-agentic-bot"
    GOOGLE_CLIENT_SECRET: str

    model_config = SettingsConfigDict(env_file="./.env")


settings = Settings()
