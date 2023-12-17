import abc
from datetime import datetime

from googlemaps import Client as GoogleMapsClient
from googlemaps.geocoding import geocode as googlemaps_geocode
from geopy import Nominatim

from src.db.model import Address
from src.util.logging import Logger


class AddressParser(metaclass=abc.ABCMeta):

    NOMINATIM: str = "nominatim"
    GOOGLE_MAPS: str = "googlemaps"

    def __init__(self, logger: Logger):
        self._logger: Logger = logger

    @abc.abstractmethod
    def normalize(self, address: str) -> Address | None:
        raise NotImplementedError


class _AddressParserNominatim(AddressParser):
    """
    This class is responsible for normalizing addresses.

    The current backend is Nominatim which has a rate limit of 1 request per second,
    thus requiring this class instead of a more trivial solution.
    """

    def __init__(self, logger: Logger):
        AddressParser.__init__(self, logger)
        self._geolocator: Nominatim = Nominatim(user_agent="normalize_addresses")
        self._last_request: datetime | None = None

    def normalize(self, address: str) -> Address | None:
        if self._last_request:
            while (datetime.now() - self._last_request).total_seconds() < 1:
                pass
        location = self._geolocator.geocode(address)
        self._last_request = datetime.now()
        if not location:
            return
        return location.address


class _AddressParserGoogleMaps(AddressParser):
    """
    This class is responsible for normalizing addresses using Google Maps Geocoding API.
    """

    def __init__(self, api_key: str, logger: Logger = None):
        AddressParser.__init__(self, logger)
        self._client = GoogleMapsClient(key=api_key)
        self._last_request: datetime | None = None

    def normalize(self, address: str) -> Address | None:
        if self._last_request:
            # Google's limit is 50 QPS, so 0.2 seconds is a safe delay
            while (datetime.now() - self._last_request).total_seconds() < 0.2:
                pass
        try:
            geocode_result = googlemaps_geocode(self._client, address, language="en-gb")
            self._last_request = datetime.now()
            if not geocode_result:
                return
            # TODO: See why some Eastern EU addresses do not return the bloc number even when specified
            return Address.from_google_maps_result(geocode_result[0])
        except Exception as e:
            self._logger.error(f"An error occurred while normalizing address with Google Maps API: `{e}`")
            return


def new_parser(engine: str, *, logger: Logger, **kwargs) -> AddressParser:
    if engine == AddressParser.NOMINATIM:
        return _AddressParserNominatim(logger=logger.new_from("PARSER_NOMINATIM"))
    if engine == AddressParser.GOOGLE_MAPS:
        return _AddressParserGoogleMaps(logger=logger.new_from("PARSER_GOOGLE_MAPS"), **kwargs)
    raise ValueError(f"Unknown engine {engine}")
