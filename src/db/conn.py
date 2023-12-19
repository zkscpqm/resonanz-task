import contextlib
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker as SessionFactory, relationship
from sqlalchemy.engine.base import Engine

from config import DatabaseConfig
from src.db.base import Base
from src.db.model import Address, Tenant
from src.db.session import Session
from src.util.logging import Logger


class Database:
    TYPE_SQLITE = 'sqlite'
    TYPE_POSTGRES = 'postgres'

    def __init__(self, config: DatabaseConfig, logger: Logger):
        self._logger: Logger = logger
        self._config: DatabaseConfig = config
        self.engine: Engine = self._create_engine()
        self._session_factory: SessionFactory = SessionFactory(bind=self.engine)
        self.create_tables()

    def _instrument_postgres_db(self) -> None:
        default_engine = create_engine(
            f'postgresql://{self._config.username}:{self._config.password}@{self._config.host}:{self._config.port}/postgres')
        with default_engine.connect() as conn:
            conn.execute(text('commit'))  # Required to execute CREATE DATABASE outside of a transaction block
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{self._config.db_name}'"))
            if not result.fetchone():
                conn.execute(text(f'CREATE DATABASE {self._config.db_name}'))
            conn.execute(text('commit'))

    def _create_engine(self) -> Engine:
        match self._config.db_type:
            case Database.TYPE_SQLITE:
                connstr = f'sqlite:///{self._config.db_name}.db'
            case Database.TYPE_POSTGRES:
                self._instrument_postgres_db()
                connstr = f'postgresql://{self._config.username}:{self._config.password}@{self._config.host}:{self._config.port}/{self._config.db_name}'
            case _:
                raise ValueError(f"Unsupported database type: {self._config.db_type}")
        return create_engine(connstr)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

        # This has to be done here because the relationship must be defined in both models
        # Since one model must always be written above the other, this is the only place where it can be done
        Address.tenants = relationship('Tenant', order_by=Tenant.id, back_populates='address')

    @contextlib.contextmanager
    def in_session(self) -> Session:
        raw_session = self._session_factory()
        sess = Session(raw_session, self._logger.new_from("Session"))
        try:
            yield sess
            self._logger.debug("Committing...")
            raw_session.commit()
        except Exception as e:
            self._logger.debug(f"Exception in session: {e}, rolling back...")
            raw_session.rollback()
            raise
        finally:
            raw_session.close()

    def new_tenant(self, address: Address, tenant_name: str) -> dict[str, Any]:
        try:
            with self.in_session() as session:

                if not (
                        addr_data := session.insert_address(address)
                ) or not (
                        addr_id := addr_data.get('id')
                ):
                    self._logger.error(f"Could not insert address into database\n{address}")
                    return {}
                tenant = Tenant(name=tenant_name, address_id=addr_id)
                if not (tenant_data := session.insert_tenant(tenant)):
                    self._logger.error(f"Could not insert tenant into database\n{tenant}")
                    return {}
                return tenant_data | {"address": addr_data}

        except Exception as e:
            self._logger.error(f"Could not insert new entry for tenant {tenant_name}\n{address}\nError: `{e}`")
            return {}
