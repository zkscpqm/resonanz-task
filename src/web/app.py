import json
from http import HTTPStatus
from typing import Callable, Any

from flask import Flask, render_template, request, Response, jsonify

from src.db.conn import Database
from src.db.model import Address, Tenant
from src.geo.normalization import AddressParser, new_parser
from src.util.logging import Logger
from src.util.meta import SingletonMeta


class Application(metaclass=SingletonMeta):

    def __init__(self, logger: Logger, db: Database, port: int = 0,
                 parser_engine: str = AddressParser.GOOGLE_MAPS, parser_api_key: str = None
                 ):
        """

        :param port: Where to host the server. If 0, port 80 is chosen (or it can be specified in the run() command)
        :param parser_engine: which backend to use for normalizing GeoLocations (see AddressParser)
        """
        self._app: Flask = Flask(__name__)
        self._port: int = port
        self._db: Database = db
        self._address_parser: AddressParser = new_parser(
            parser_engine, logger=logger.new_from("ADDRESS_PARSER"), api_key=parser_api_key
        )
        self._logger: Logger = logger
        self._route_all()

    def run(self, port: int = 0, debug: bool = False):
        if not port:
            if not self._port:
                port = 80
            else:
                port = self._port
        if debug:
            self._logger.info(f"Running in debug mode (raw flask) on {port=}")
            return self._app.run(host="0.0.0.0", port=port, debug=False)
        import waitress
        self._logger.info(f"Running in production mode (waitress) on {port=}")
        waitress.serve(self._app, host="0.0.0.0", port=port)

    def _parse_address(self, raw_address: str) -> Address | None:
        if not raw_address:
            raise ValueError("No address specified")

        self._logger.debug(f"Got request to normalize address: `{raw_address}`")
        if not (address := self._address_parser.normalize(raw_address)):
            raise ValueError(f"Could not normalize address: `{address}`")
        return address

    def _add_entry(self):
        if request.method.upper() != "POST":
            self._logger.error(f"Got request with method {request.method} instead of POST")
            return self._err_json_response(HTTPStatus.METHOD_NOT_ALLOWED, "FATAL: Only POST is allowed")
        request_body = request.get_json()
        raw_address = request_body.get("address")
        tenant_name = request_body.get("name")
        try:
            address = self._parse_address(raw_address)
        except ValueError as e:
            return self._err_json_response(HTTPStatus.BAD_REQUEST, f"Could not normalize address {raw_address}: `{e}`")
        self._logger.info(f"Normalized address `{raw_address}` to `{address}`")

        if not (result := self._db.new_tenant(address=address, tenant_name=tenant_name)):
            return self._err_json_response(HTTPStatus.INTERNAL_SERVER_ERROR, f"Could not insert tenant `{tenant_name}` into database")
        return jsonify(result), HTTPStatus.CREATED

    def index(self) -> Response:
        return Response(render_template("index.html"))

    def _route(self, path: str, view_function: Callable, methods: list[str] = None):
        self._app.add_url_rule(path, path.lstrip("/"), view_function, methods=methods or ["GET"])

    def _route_all(self):
        self._route("/", self.index)
        self._route("/_tenant", self._add_entry, methods=["POST"])

    def _err_json_response(self, status: int, message: str) -> Response:
        self._logger.debug(f"sending back error response ({status}): {message}")
        return Response(json.dumps({"error": message}), status=status, mimetype="application/json")
