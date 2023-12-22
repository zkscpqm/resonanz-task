import contextlib
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker as SessionFactory, relationship
from sqlalchemy.engine.base import Engine

from config import DatabaseConfig
from src.db.base import Base
from src.db.model import AddressModel
from src.web.model import Address, Tenant
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
        AddressModel.tenants = relationship('TenantModel', order_by=Tenant.id, back_populates='address')

    @contextlib.contextmanager
    def in_session(self) -> Session:
        raw_session = self._session_factory()
        sess = Session(raw_session, self._logger.new_from("Session"))
        try:
            yield sess
            raw_session.commit()
        except Exception as e:
            self._logger.debug(f"Exception in session: {e}, rolling back...")
            raw_session.rollback()
            raise
        finally:
            raw_session.close()

    def new_tenant(self, address: Address, tenant_name: str) -> Tenant | None:
        """
        Insert a new tenant into the database. First, insert the address and upon success, insert the tenant
        """
        try:
            with self.in_session() as session:
                session.insert_address(address)
                if not address.id:
                    self._logger.error(f"Could not insert address into database\n{address}")
                    raise

                tenant = Tenant(name=tenant_name, address=address)
                session.insert_tenant(tenant)
                if not tenant.id:
                    self._logger.error(f"Could not insert tenant into database\n{tenant}")
                    raise
                return tenant

        except Exception as e:
            self._logger.error(f"Could not insert new entry for tenant {tenant_name}\n{address}\nError: `{e}`")
            raise

    def batch_insert_tenants(self, batch: list[tuple[str, Address]]) -> int:
        """
        Insert a batch of tenants into the database. See `session.insert_tenant`
        This does them one by one so that we can verify IDs are set correctly
        :param batch: a list of pairs of tenant names and addresses to insert
        :return: the number of successfully inserted tenants
        """
        success_count = 0

        with self.in_session() as session:
            for tenant_name, address in batch:
                try:
                    session.insert_address(address)
                    if not address.id:
                        self._logger.error(f"Could not insert address into database\n{address}")
                        continue

                    tenant = Tenant(name=tenant_name, address=address)
                    session.insert_tenant(tenant)
                    if tenant.id:
                        success_count += 1
                except Exception as e:
                    self._logger.error(
                        f"Error during batch insert\nTenant: {tenant_name}, Address: {address}\nError: `{e}`")
                    continue

        return success_count

    def get_all_tenants(self) -> list[Tenant]:
        try:
            with self.in_session() as session:
                return session.get_all_tenants()
        except Exception as e:
            self._logger.error(f"Could not get all tenants\nError: `{e}`")
            return []

    def get_tenants_at_address(self, address: Address) -> list[Tenant]:
        """
        Get all tenants at an address. See `session.find_tenants_at_address`
        """
        try:
            with self.in_session() as session:
                if not (res := session.get_address(address.full_address)):
                    self._logger.error(f"Could not find address in database\n{address}")
                    return []
                return session.find_tenants_at_address(res.id)
        except Exception as e:
            self._logger.error(f"Could not get tenants at address\n{address}\nError: `{e}`")
            return []

    def get_addresses_for_tenant_name(self, tenant_name: str) -> list[Tenant]:
        """
        See `session.search_addresses_by_tenant`
        """
        try:
            with self.in_session() as session:
                return session.search_addresses_by_tenant(tenant_name)
        except Exception as e:
            self._logger.error(f"Could not get addresses for tenant name {tenant_name}\nError: `{e}`")
            return []

    def get_address_location(self, address: Address) -> tuple[float, float] | None:
        # Not used, was going to have a Google Maps integration on the Frontend, but it would have taken too long
        try:
            with self.in_session() as session:
                if not (res := session.get_address(address.full_address)):
                    self._logger.error(f"Could not find address in database\n{address}")
                    return
                return res.lat, res.lon
        except Exception as e:
            self._logger.error(f"Could not get address with ID {address}\nError: `{e}`")
            return
