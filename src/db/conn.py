import contextlib
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker as SessionFactory, Session
from sqlalchemy.engine.base import Engine

from config import DatabaseConfig
from src.db.base import Base
from src.db.model import Address
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

    @contextlib.contextmanager
    def in_session(self) -> Session:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            self._logger.error(f"Exception in session: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    def insert_address(self, address: Address) -> dict[str, Any]:
        self._logger.debug(f"Inserting address\n{address}")
        try:
            with self.in_session() as session:
                addr_d = address.to_dict()

                if self._address_exists_session(session, address):
                    self._logger.debug(f"Address already exists\n{address}")
                    return addr_d

                session.add(address)
                self._logger.debug(f"Inserted address\n{address}")
                return addr_d
        except Exception as e:
            self._logger.error(f"Could not insert address\n{address}\nError: `{e}`")
            return {}

    def _address_exists(self, address: Address) -> bool:
        with self.in_session() as session:
            return self._address_exists_session(session, address)

    def _address_exists_session(self, session: Session, address: Address) -> bool:
        query = session.query(Address).filter(
            (Address.street_number == address.street_number) if address.street_number is not None else True,
            (Address.street_name == address.street_name) if address.street_name is not None else True,
            (Address.neighborhood == address.neighborhood) if address.neighborhood is not None else True,
            (Address.city == address.city) if address.city is not None else True,
            (Address.region == address.region) if address.region is not None else True,
            (Address.postcode == address.postcode) if address.postcode is not None else True,
            (Address.country == address.country) if address.country is not None else True,
            (Address.block == address.block) if address.block is not None else True,
            (Address.entrance == address.entrance) if address.entrance is not None else True,
            (Address.floor == address.floor) if address.floor is not None else True,
            (Address.apartment_number == address.apartment_number) if address.apartment_number is not None else True
        )
        return session.query(query.exists()).scalar()
