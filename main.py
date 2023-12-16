from config import Config
from src.util.logging import Logger
from src.web.app import Application


def main():
    cfg = Config.from_file()
    logger = Logger("MAIN", level=cfg.log_level)
    app = Application(port=cfg.port, logger=logger.new_from("APP"),
                      parser_engine=cfg.address_parser_backend, parser_api_key=cfg.address_parser_api_key)
    app.run(debug=cfg.debug_mode)


if __name__ == '__main__':
    main()
