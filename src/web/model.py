import dataclasses
from typing import Any

from src.db.model import AddressModel, TenantModel


@dataclasses.dataclass
class Address:

    full_address: str
    id: int | None = None
    lat: float | None = None
    lon: float | None = None

    @classmethod
    def from_google_maps_result(cls, geocode_result: dict[str, Any]) -> 'Address':
        return Address(
            full_address=geocode_result['formatted_address'],
            lat=geocode_result['geometry']['location']['lat'],
            lon=geocode_result['geometry']['location']['lng']
        )

    @classmethod
    def from_address_model(cls, address_model: AddressModel) -> 'Address':
        return Address(
            full_address=address_model.full_address,
            id=address_model.id,
            lat=address_model.lat,
            lon=address_model.lon
        )

    def to_dict(self) -> dict[str, Any]:
        d = {
            'address': self.full_address,
        }
        if self.id:
            d['id'] = self.id
        if self.lat:
            d['lat'] = self.lat
        if self.lon:
            d['lon'] = self.lon
        return d

    def to_address_model(self) -> AddressModel:
        return AddressModel(
            full_address=self.full_address,
            lat=self.lat,
            lon=self.lon
        )


@dataclasses.dataclass
class Tenant:

    name: str
    id: int | None = None
    address: Address | None = None

    def to_dict(self) -> dict[str, Any]:
        d = {
            'name': self.name,
        }
        if self.id:
            d['id'] = self.id
        if self.address:
            d['address'] = self.address.to_dict()
        return d

    @classmethod
    def from_tenant_model(cls, tenant_model: TenantModel) -> 'Tenant':
        return Tenant(
            name=tenant_model.name,
            id=tenant_model.id,
            address=Address.from_address_model(tenant_model.address) if tenant_model.address else None
        )

    def to_tenant_model(self) -> TenantModel:
        return TenantModel(
            name=self.name,
            name_lower=self.name.lower(),
            address_id=self.address.id if self.address else None,
        )
