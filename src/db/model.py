from typing import Optional, Any
from sqlalchemy import Column, Integer, String, UniqueConstraint

from src.db.base import Base


class Address(Base):
    __tablename__ = 'addresses'

    id: int = Column(Integer, primary_key=True)
    street_number: str = Column(String)
    street_name: str = Column(String)
    neighborhood: str = Column(String)
    city: str = Column(String)
    region: str = Column(String)
    postcode: str = Column(String)
    country: str = Column(String)
    block: Optional[str] = Column(String, nullable=True)
    entrance: Optional[str] = Column(String, nullable=True)
    floor: Optional[str] = Column(String, nullable=True)
    apartment_number: Optional[str] = Column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<Address(street_number='{self.street_number}', street_name='{self.street_name}', " \
               f"neighborhood='{self.neighborhood}', city='{self.city}', region='{self.region}', " \
               f"postcode='{self.postcode}', country='{self.country}', block='{self.block}', " \
               f"entrance='{self.entrance}', floor='{self.floor}', apartment_number='{self.apartment_number}')>"

    @classmethod
    def from_google_maps_result(cls, geocode_result: dict[str, Any]) -> 'Address':
        components = {c['types'][0]: c['long_name'] for c in geocode_result['address_components']}

        return cls(
            street_number=components.get('street_number'),
            street_name=components.get('route'),
            neighborhood=components.get('sublocality_level_1') or components.get('neighborhood'),
            city=components.get('locality'),
            region=components.get('administrative_area_level_1'),
            postcode=components.get('postal_code'),
            country=components.get('country'),
            block=components.get('subpremise'),
            entrance=None,
            floor=None,
            apartment_number=components.get('subpremise')
        )

    def to_dict(self) -> dict:
        # Convert the address object to a dictionary for JSON encoding
        return {
            'street_number': self.street_number,
            'street_name': self.street_name,
            'neighborhood': self.neighborhood,
            'city': self.city,
            'region': self.region,
            'postcode': self.postcode,
            'country': self.country,
            'block': self.block,
            'entrance': self.entrance,
            'floor': self.floor,
            'apartment_number': self.apartment_number
        }


# Example usage
# config = DatabaseConfig(db_type='sqlite', database='local')
# db = Database(config)
# db.create_tables()

# Example usage for PostgreSQL
# config = DatabaseConfig(db_type='postgres', username='user', password='pass', host='localhost', port='5432', database='mydb')
# db = Database(config)
# db.create_tables()

# Assuming you have a valid geocode result from Google Maps API
# address = Address.from_google_maps_result(geocode_result)
# session = db.Session()
# session.add(address)
# session.commit()