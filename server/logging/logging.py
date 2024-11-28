import logging


def log_config():
    logging.basiConfig(
        level=logging.DEBUG,
        format="%(name)s - %(levelname)s - %(message)s",
        # logging.debug
        # logging.info
        # logging.warning
        # logging.error
        # logging.critical
    )
