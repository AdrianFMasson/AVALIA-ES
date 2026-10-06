from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings (BaseSettings):
    ssh_host: str 
    ssh_port: int = 22
    ssh_user: str
    ssh_password: str | None = None

    #Mysql
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_name: str
    db_user: str
    db_password: str

    model_config = SettingsConfigDict(env_file=".env",env_file_encoding="UTF-8")



#Informações para autenticação
    JWT_SECRET_KEY: str              # openssl rand -hex 32
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 7
    JWT_ISSUER: str = "sistema-emprestimo"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
#Variável que armazena os valores lidos do arquivo .env
settings = Settings()