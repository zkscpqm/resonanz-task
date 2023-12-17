import dataclasses
import json
import logging
from pathlib import Path
from typing import Any

from src.geo.normalization import AddressParser


class _LogLevelLookup:
    _mapping: dict[str, int] = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    _reverse_mapping: dict[int, str] = {v: k for k, v in _mapping.items()}

    @classmethod
    def lookup(cls, level: str, default: int = logging.ERROR) -> int:
        return cls._mapping.get(level.upper(), default)

    @classmethod
    def reverse_lookup(cls, level: int, default: str = "ERROR") -> str:
        return cls._reverse_mapping.get(level, default)


@dataclasses.dataclass
class DatabaseConfig:

    db_type: str
    username: str | None = None
    password: str | None = None
    host: str | None = None
    port: int | None = None
    db_name: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'DatabaseConfig':
        return cls(
            db_type=data.get("type"),
            username=data.get("username"),
            password=data.get("password"),
            host=data.get("host"),
            port=data.get("port"),
            db_name=data.get("name"),
        )


@dataclasses.dataclass
class Config:
    port: int
    debug_mode: bool
    log_level: int
    address_parser_backend: str | None
    address_parser_api_key: str | None
    database: DatabaseConfig | None = None

    @classmethod
    def from_file(cls, path: Path = Path("config.json")) -> 'Config':
        with open(path, 'r') as f:
            data = json.load(f)

        debug_mode = data.get("debug_mode", False)
        return cls(
            port=data.get("port", 80),
            debug_mode=debug_mode,
            log_level=_LogLevelLookup.lookup(
                data.get("log_level"), default=logging.DEBUG if debug_mode else logging.ERROR
            ),
            address_parser_backend=data.get("address_parser_backend", AddressParser.GOOGLE_MAPS),
            address_parser_api_key=data.get("address_parser_api_key"),
            database=DatabaseConfig.from_dict(data.get("database")) if data.get("database") else None,
        )
