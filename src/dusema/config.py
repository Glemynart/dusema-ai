from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DUSEMA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    environment: Literal["development", "test", "production"] = "development"
    database_host: str = Field(default="127.0.0.1", pattern=r"^[A-Za-z0-9.:-]+$")
    database_port: int = Field(default=55436, ge=1, le=65535)
    database_name: str = Field(default="dusema", pattern=r"^[a-z_][a-z0-9_]{0,62}$")
    database_user: str = Field(default="dusema", pattern=r"^[a-z_][a-z0-9_]{0,62}$")
    database_password: SecretStr | None = Field(default=None, min_length=1, repr=False)

    @property
    def database_url(self) -> URL | None:
        if self.database_password is None:
            return None
        return URL.create(
            "postgresql+psycopg",
            username=self.database_user,
            password=self.database_password.get_secret_value(),
            host=self.database_host,
            port=self.database_port,
            database=self.database_name,
        )
