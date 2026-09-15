from dataclasses import dataclass
from sshtunnel import SSHTunnelForwarder
from config.Config import settings
from sqlmodel import create_engine, Session
import urllib
from sqlalchemy.engine import Engine

@dataclass
class Database():
    _tunel: SSHTunnelForwarder | None = None
    _engine: Engine | None = None

    def start_tunnel(self):
        self._tunel = SSHTunnelForwarder(
            (settings.ssh_host,settings.ssh_port),
            ssh_username=settings.ssh_user,
            ssh_password=settings.ssh_password,
            remote_bind_address=(settings.db_host,settings.db_port)
        )
        self._tunel.start()

        encoded_password = urllib.parse.quote_plus(settings.db_password)

        url=(f"mysql+pymysql://{settings.db_user}:{encoded_password}"
             f"@127.0.0.1:{self._tunel.local_bind_port}"
             f"/{settings.db_name}")
        self._engine= create_engine(
            url,
            echo=True,
            pool_pre_ping=True,       # valida conexão antes de reutilizar
            pool_recycle=1800,        # recicla conexões a cada 30 min
            pool_size=5, 
        )
        if not self._engine:
            raise ConnectionError("Erro de conexão com o BdD")

    def get_db(self):
        with Session(self._engine) as s:
            yield s


            
    