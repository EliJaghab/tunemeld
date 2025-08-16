import logging
import os

from dotenv import load_dotenv


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s() - line %(lineno)d - %(message)s",
            datefmt="%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


logger = get_logger(__name__)


def set_secrets() -> None:
    if not os.getenv("GITHUB_ACTIONS"):
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env.dev"))
        logger.info("env_path" + env_path)
        load_dotenv(dotenv_path=env_path)
