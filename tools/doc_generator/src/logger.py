import logging


class Logger:
    def __init__(self):
        self._setup_logging()
        self.logger = logging.getLogger(__name__)

    def _setup_logging(self):
        formatter = logging.Formatter(
            "%(asctime)s │ %(levelname)-5s │ %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        logger = logging.getLogger()
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def info(self, message: str):
        self.logger.info(message)

    def error(self, message: str):
        self.logger.error(message)

    def warning(self, message: str):
        self.logger.warning(message)


logger = Logger()
