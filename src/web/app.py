import json
from http import HTTPStatus
from typing import Callable

from flask import Flask, render_template, request, Response, jsonify

from src.geo.normalization import AddressParser, new_parser
from src.util.logging import Logger
from src.util.meta import SingletonMeta


class Application(metaclass=SingletonMeta):

    def __init__(self, logger: Logger, port: int = 0,
                 parser_engine: str = AddressParser.GOOGLE_MAPS, parser_api_key: str = None
                 ):
        """

        :param port: Where to host the server. If 0, port 80 is chosen (or it can be specified in the run() command)
        :param parser_engine: which backend to use for normalizing GeoLocations (see AddressParser)
        """
        self._app: Flask = Flask(__name__)
        self._port: int = port
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

    def _add_address(self):
        if request.method.upper() != "POST":
            self._logger.error(f"Got request with method {request.method} instead of POST")
            return self._err_json_response(HTTPStatus.METHOD_NOT_ALLOWED, "FATAL: Only POST is allowed")
        raw_address = request.get_json().get("address")
        if not raw_address:
            return self._err_json_response(HTTPStatus.BAD_REQUEST, "No address specified")

        self._logger.debug(f"Got request to normalize address: `{raw_address}`")
        parse_ok = True
        if not (address := self._address_parser.normalize(raw_address)):
            self._logger.warning(f"Could not normalize address: `{address}` so using it as is")
            parse_ok = False
            address = raw_address
        else:
            self._logger.info(f"Normalized address `{raw_address}` to `{address}`")
        return jsonify({"address": address, "parsing_ok": parse_ok}), HTTPStatus.CREATED

    def index(self) -> Response:
        return Response(render_template("index.html"))

    def _route(self, path: str, view_function: Callable, methods: list[str] = None):
        self._app.add_url_rule(path, path.lstrip("/"), view_function, methods=methods or ["GET"])

    def _route_all(self):
        self._route("/", self.index)
        self._route("/_address", self._add_address, methods=["POST"])

    def _err_json_response(self, status: int, message: str) -> Response:
        self._logger.debug(f"sending back error response ({status}): {message}")
        return Response(json.dumps({"error": message}), status=status, mimetype="application/json")
