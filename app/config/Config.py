
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ssh_host: str
    ssh_port: int = 22
    ssh_user: str
    ssh_password: str | None = None

    # MySQL
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_name: str
    db_user: str
    db_password: str

    # Autenticação JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 7
    JWT_ISSUER: str = "sistema-emprestimo"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Carrega as configurações do arquivo .env
settings = Settings()
