import json
from http import HTTPStatus
from typing import Callable

from flask import Flask, render_template, request, Response, jsonify

from src.geo.normalization import AddressParser
from src.util.meta import SingletonMeta


class Application(metaclass=SingletonMeta):

    def __init__(self, port: int = 0):
        self._app: Flask = Flask(__name__)
        self._port: int = port
        self._address_parser: AddressParser = AddressParser()
        self._route_all()

    def run(self, port: int = 0, debug: bool = False):
        if not port:
            if not self._port:
                raise RuntimeError("Port not specified")
            port = self._port
        if debug:
            return self._app.run(host="0.0.0.0", port=port, debug=False)
        import waitress
        waitress.serve(self._app, host="0.0.0.0", port=port)

    def _add_address(self):
        if request.method.upper() != "POST":
            print(f"Got request with method {request.method} instead of POST")
            return self._err_json_response(HTTPStatus.METHOD_NOT_ALLOWED, "Only POST is allowed")
        raw_address = request.values.get("address")
        if not raw_address:
            return self._err_json_response(HTTPStatus.BAD_REQUEST, "No address specified")

        parse_ok = True
        if not (address := self._address_parser.normalize(raw_address)):
            print(f"Could not normalize address: {address} so using it as is")
            parse_ok = False
            address = raw_address
        if parse_ok:
            print(f"Normalized address {raw_address} to `{address}`")
        return jsonify({"address": address, "parsing_ok": parse_ok}), HTTPStatus.CREATED

    def index(self) -> Response:
        return Response(render_template("index.html"))

    def _route(self, path: str, view_function: Callable, methods: list[str] = None):
        self._app.add_url_rule(path, path.lstrip("/"), view_function, methods=methods or ["GET"])

    def _route_all(self):
        self._route("/", self.index)
        self._route("/_address", self._add_address, methods=["POST"])

    @staticmethod
    def _err_json_response(status: int, message: str) -> Response:
        return Response(json.dumps({"error": message}), status=status, mimetype="application/json")
