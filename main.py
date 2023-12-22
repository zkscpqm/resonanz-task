import argparse
from pathlib import Path

from config import Config
from src.db.conn import Database
from src.util.logging import Logger
from src.web.app import Application


def main(config_path: Path):
    cfg = Config.from_file(path=config_path)
    logger = Logger("MAIN", level=cfg.log_level)

    db = Database(cfg.database, logger=logger.new_from("DB"))

    app = Application(port=cfg.port, logger=logger.new_from("APP"), db=db,
                      parser_engine=cfg.address_parser_backend, parser_api_key=cfg.address_parser_api_key)
    app.run(debug=cfg.debug_mode)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", "-c", type=str, default="config.json", help="Path to config file")
    args = ap.parse_args()
    main(Path(args.config))
