import json
import uuid

from config import Config
from src.db.conn import Database
from src.db.model import TenantModel
from src.geo.normalization import new_parser, AddressParser
from src.util.logging import Logger
from src.web.app import Application


def test(db: Database, logger: Logger, key: str):
    parser = new_parser(AddressParser.GOOGLE_MAPS, logger=logger, api_key=key)

    data = {
        "27 mitta crescent, narangba, qld": ("Alex Little", "Sarah Little"),
        "21 wedgetail cct, narangba, qld": ("Mariya McGee", "John McGee", "Liam McGee"),
        "12 windrest street, strathpine": ("Jason Martin",),
        "ul.Zhaltuga 8, 4027 Sheker, Plovdiv": ("Bai Ivan",),
        "15 Dr Louis Mallet Saint-Chély-d'Apcher": ("Christine Deveraux", "Cosette Fauchelevent"),
        "3 wall street nyc": ("Donald Trump",),
        "5 wall street nyc": ("Donald Trump",),
        "1 Guanghua Road, Beijing, China 100020": ("Xi Jinping",),
    }

    for addr, tenants in data.items():
        address = parser.normalize(addr)
        for tenant_name in tenants:

            inserted_tenant = db.new_tenant(address, tenant_name)
            print(f"Tenant inserted: {inserted_tenant}")

    for addr, tenants in data.items():
        address = parser.normalize(addr)
        residents = db.get_tenants_at_address(address)
        print(f"Tenants at {address}: {residents}")
        for tenant_name in tenants:
            addresses = db.get_addresses_for_tenant_name(tenant_name)
            print(f"Addresses where {tenant_name} lives {addresses}")



def main():
    cfg = Config.from_file()
    logger = Logger("MAIN", level=cfg.log_level)

    db = Database(cfg.database, logger=logger.new_from("DB"))

    test(db, logger, cfg.address_parser_api_key)

    # app = Application(port=cfg.port, logger=logger.new_from("APP"), db=db,
    #                   parser_engine=cfg.address_parser_backend, parser_api_key=cfg.address_parser_api_key)
    # app.run(debug=cfg.debug_mode)


if __name__ == '__main__':
    main()
