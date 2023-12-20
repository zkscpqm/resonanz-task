from sqlalchemy import Column, Integer, String, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import relationship

from src.db.base import Base


class AddressModel(Base):
    __tablename__ = 'addresses'

    id: int = Column(Integer, primary_key=True)
    full_address: str = Column(String, nullable=False, unique=True)
    lat: float = Column(Float, nullable=True)
    lon: float = Column(Float, nullable=True)


class TenantModel(Base):
    __tablename__ = 'tenants'

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String, nullable=False)
    address_id: int = Column(Integer, ForeignKey('addresses.id'), nullable=False)
    address = relationship('AddressModel', back_populates='tenants')

    __table_args__ = (
        UniqueConstraint('name', 'address_id', name='_name_address_uc'),  # Enforce unique combination
    )
