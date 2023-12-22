import csv
import json
from datetime import timedelta
from http import HTTPStatus
from io import TextIOWrapper
from typing import Callable

from flask import Flask, render_template, request, Response, jsonify

from src.db.conn import Database
from src.db.model import AddressModel
from src.geo.normalization import AddressParser, new_parser
from src.util.logging import Logger
from src.util.meta import SingletonMeta
from src.web.model import Address


class Application(metaclass=SingletonMeta):

    _batch_size: int = 1024

    def __init__(self, logger: Logger, db: Database, port: int = 0,
                 parser_engine: str = AddressParser.GOOGLE_MAPS, parser_api_key: str = None
                 ):
        self._app: Flask = Flask(__name__)
        self._port: int = port
        self._db: Database = db
        self._address_parser: AddressParser = new_parser(
            parser_engine, logger=logger.new_from("ADDRESS_PARSER"), api_key=parser_api_key
        )
        self._logger: Logger = logger
        self._configure()
        self._route_all()

    def _configure(self):
        # avoid reading the file from disk each time
        self._app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=60 * 60 * 24 * 365)

    def _route_all(self):
        self._route("/", self.search)
        self._route("/search", self.search, endpoint="search")
        self._route("/insert", self.insert, endpoint="insert")

        # these are named a bit weird because basically you search addresses to find tenants and vice-versa
        self._route("/search/_addresses", self._search_addresses_by_tenant)
        self._route("/search/_tenants", self._search_tenants_by_address)

        self._route("/insert/_tenant", self._add_entry, methods=["POST"])
        self._route("/insert/_batch", self._batch_insert, methods=["POST"])

    def run(self, port: int = 0, debug: bool = False):
        """
        Run the application. If no port is specified, the port from the constructor is used. If no port is specified
        in the constructor, port 80 is used.
        If debug is True, the application is run in debug mode (raw flask). Otherwise, the application is run in
        production mode (waitress WSGI server)
        """
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

    def _parse_address(self, raw_address: str) -> Address:
        if not raw_address:
            raise ValueError("No address specified")

        self._logger.debug(f"Got request to normalize address: `{raw_address}`")
        if not (address := self._address_parser.normalize(raw_address)):
            raise ValueError(f"Could not normalize address: `{address}`")
        self._logger.debug(f"Normalized address `{raw_address}` to `{address}`")
        return address

    def _add_entry(self):
        request_body = request.get_json()
        raw_address = request_body.get("address")
        tenant_name = request_body.get("name")
        try:
            address = self._parse_address(raw_address)
        except ValueError as e:
            return self._err_json_response(HTTPStatus.BAD_REQUEST, f"Could not normalize address {raw_address}: `{e}`")
        if not (result := self._db.new_tenant(address=address, tenant_name=tenant_name)):
            return self._err_json_response(HTTPStatus.INTERNAL_SERVER_ERROR, f"Could not insert tenant `{tenant_name}` into database")
        return jsonify(result), HTTPStatus.CREATED

    def _batch_insert(self):
        if 'file' not in request.files:
            return self._err_json_response(HTTPStatus.BAD_REQUEST, "No file part")

        file = request.files['file']
        if file.filename == '':
            return self._err_json_response(HTTPStatus.BAD_REQUEST, "No selected file")

        batch = []
        success_count = 0
        failure_count = 0

        # Process the file line by line
        text_stream = TextIOWrapper(file.stream, encoding='utf-8')
        csv_reader = csv.reader(text_stream)
        for i, row in enumerate(csv_reader):
            if i == 0:
                continue
            if len(row) != 2:
                failure_count += 1
                self._logger.warning(f"Skipping row {i} because it does not have exactly 2 columns")
                continue

            tenant_name, raw_address = row
            try:
                address = self._parse_address(raw_address)
                batch.append((tenant_name, address))
            except ValueError:
                self._logger.warning(f"Skipping row {i} because could not normalize address `{raw_address}`")
                failure_count += 1

            if len(batch) >= self._batch_size:
                pending = len(batch)
                successful = self._db.batch_insert_tenants(batch)
                success_count += successful
                failure_count += pending - successful
                batch.clear()

        if batch:
            pending = len(batch)
            successful = self._db.batch_insert_tenants(batch)
            success_count += successful
            failure_count += pending - successful
        text_stream.close()
        status = HTTPStatus.CREATED if failure_count == 0 else HTTPStatus.PARTIAL_CONTENT
        return jsonify({"success": success_count, "failed": failure_count}), status

    def _search_tenants_by_address(self) -> Response:
        if not (raw_address := request.args.get("address")):
            result = self._db.get_all_tenants()
        else:
            try:
                address = self._parse_address(raw_address)
            except ValueError as e:
                return self._err_json_response(HTTPStatus.BAD_REQUEST, f"Could not normalize address {raw_address}: `{e}`")

            result = self._db.get_tenants_at_address(address=address)

        return jsonify([tenant.to_dict() for tenant in result])

    def _search_addresses_by_tenant(self) -> Response:
        if not (tenant_name := request.args.get("name")):
            result = self._db.get_all_tenants()
        else:
            result = self._db.get_addresses_for_tenant_name(tenant_name=tenant_name)

        self._logger.debug(f"Got addresses for tenant `{tenant_name}`: {result}")
        return jsonify([tenant.to_dict() for tenant in result])

    def search(self) -> Response:
        return Response(render_template("search.html"))

    def insert(self) -> Response:
        return Response(render_template("insert.html"))

    def _route(self, path: str, view_function: Callable, methods: list[str] = None, endpoint: str = None):
        self._app.add_url_rule(
            path,
            view_func=view_function, methods=methods or ["GET"], endpoint=endpoint
        )

    def _err_json_response(self, status: int, message: str) -> Response:
        self._logger.debug(f"sending back error response ({status}): {message}")
        return Response(json.dumps({"error": message}), status=status, mimetype="application/json")
