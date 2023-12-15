from datetime import datetime

from geopy import Nominatim


class AddressParser:
    """
    This class is responsible for normalizing addresses.

    The current backend is Nominatim which has a rate limit of 1 request per second,
    thus requiring this class instead of a more trivial solution.
    """

    def __init__(self):
        self._geolocator: Nominatim = Nominatim(user_agent="normalize_addresses")
        self._last_request: datetime | None = None

    def normalize(self, address: str) -> str | None:
        if self._last_request:
            while (datetime.now() - self._last_request).total_seconds() < 1:
                pass
        print("normalizing", address, "...")
        location = self._geolocator.geocode(address)
        self._last_request = datetime.now()
        if not location:
            return
        return location.address
