from sqlalchemy.orm import Session as SQLAlchemySession

from src.db.base import Base
from src.web.model import Address, Tenant
from src.db.model import AddressModel, TenantModel
from src.util.logging import Logger


class Session:

    def __init__(self, session: SQLAlchemySession, logger: Logger):
        """
        Session wrapper for SQLAlchemy session. This is to allow for multiple DB queries within 1 transaction
        """
        self._logger: Logger = logger
        self._session: SQLAlchemySession = session

    def insert_address(self, address: Address):
        """
        Insert an address into the database. Upon success, the input address ID is set to the ID of the inserted address
        """
        self._logger.debug(f"Inserting address\n{address}")
        try:
            if existing := self.get_address(address.full_address):
                self._logger.debug(f"Address already exists with ID: {existing.id}")
                address.id = existing.id
                return
            addr_model = address.to_address_model()
            self._insert(addr_model)
            address.id = addr_model.id
        except Exception as e:
            self._logger.error(f"Could not insert address\n{address}\nError: `{e}`")
            raise

    def insert_tenant(self, tenant: Tenant):
        """
        Insert a tenant into the database. Upon success, the input tenant ID is set to the ID of the inserted tenant
        The tenant's address must already exist in the database
        """
        self._logger.debug(f"Inserting tenant\n{tenant}")
        try:
            if existing := self.get_tenant(tenant.name, tenant.address.id):
                self._logger.debug(f"Tenant already exists with ID: {existing.id}")
                tenant.id = existing.id
                return
            tenant_model = tenant.to_tenant_model()
            self._insert(tenant_model)
            tenant.id = tenant_model.id

        except Exception as e:
            self._logger.error(f"Could not insert tenant\n{tenant}\nError: `{e}`")
            raise

    def _insert(self, what: Base) -> int:
        """
        Insert a model into the database. We flush changes immediately so we can take the ID before committing session
        """
        self._session.add(what)
        self._session.flush()
        self._logger.debug(f"Inserted {what.__class__.__name__} with ID: {what.id}")
        return what.id

    def get_address(self, full_address: str) -> Address | None:
        if res := self._session.query(AddressModel).filter_by(full_address=full_address).first():
            return Address.from_address_model(res)

    def get_tenant(self, tenant_name: str, address_id: int) -> Tenant | None:
        """
        Get a tenant by name (caseless) and address ID. This is to ensure that the tenant name is unique for the address
        """
        if res := self._session.query(TenantModel).filter_by(name_lower=tenant_name.lower(), address_id=address_id).first():
            return Tenant.from_tenant_model(res)

    def search_addresses_by_tenant(self, tenant_name: str) -> list[Tenant]:
        """
        Get all addresses for a tenant name (caseless)
        Multiple tenants can have the same name if they are at different addresses
        """
        tenants = [Tenant.from_tenant_model(tm) for tm in
                   self._session.query(TenantModel).filter_by(name_lower=tenant_name.lower()).all()]

        return tenants

    def find_tenants_at_address(self, address_id: int) -> list[Tenant]:
        return [Tenant.from_tenant_model(tm) for tm in
                self._session.query(TenantModel).filter_by(address_id=address_id).all()]

    def get_all_tenants(self) -> list[Tenant]:
        return [Tenant.from_tenant_model(tm) for tm in
                self._session.query(TenantModel).all()]
