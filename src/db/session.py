import inspect
from typing import Any

from sqlalchemy import and_
from sqlalchemy.orm import Session as SQLAlchemySession

from src.db.base import Base
from src.db.model import Address, Tenant
from src.util.logging import Logger


class Session:

    _address_search_fields: tuple[str] = (
        "street_number",
        "street_name",
        "neighborhood",
        "city",
        "region",
        "postcode",
        "country",
        "block",
        "entrance",
        "floor",
        "apartment_number",
    )

    _tenant_search_fields: tuple[str] = (
        "name",
    )

    def __init__(self, session: SQLAlchemySession, logger: Logger):
        self._logger: Logger = logger
        self._session: SQLAlchemySession = session

    def insert_address(self, address: Address) -> dict[str, Any]:
        self._logger.debug(f"Inserting address\n{address}")
        try:
            addr_data = address.to_dict()
            if existing_id := self.find_address_id(address):
                self._logger.debug(f"Address already exists with ID: {existing_id}")
                return addr_data | {'id': existing_id}
            return addr_data | {'id': self._insert(address)}
        except Exception as e:
            self._logger.error(f"Could not insert address\n{address}\nError: `{e}`")
            return {}

    def insert_tenant(self, tenant: Tenant) -> dict[str, Any]:
        self._logger.debug(f"Inserting tenant\n{tenant}")
        try:
            tenant_data = tenant.to_dict()
            if existing_id := self.find_tenant_id(tenant):
                self._logger.debug(f"Tenant already exists with ID: {existing_id}")
                return tenant_data | {'id': existing_id}
            return tenant_data | {'id': self._insert(tenant)}

        except Exception as e:
            self._logger.error(f"Could not insert tenant\n{tenant}\nError: `{e}`")
            return {}

    def _insert(self, what: Base) -> int:
        self._session.add(what)
        self._session.flush()
        self._logger.debug(f"Inserted {what.__class__.__name__} with ID: {what.id}")
        return what.id

    def _find_object_id(self, obj: Base, *fields) -> int:
        obj_t = obj.__class__
        kwargs = {col: getattr(obj, col) for col in fields}
        conditions = [getattr(obj_t, field) == value if value is not None else getattr(obj_t, field).is_(None) for
                      field, value in kwargs.items()]
        instance = self._session.query(obj_t).filter(and_(*conditions)).first()
        return instance.id if instance else 0

    def find_address_id(self, address_obj: Address) -> int:
        return self._find_object_id(address_obj, *self._address_search_fields)

    def find_tenant_id(self, tenant_obj: Tenant) -> int:
        return self._find_object_id(tenant_obj, *self._tenant_search_fields)
