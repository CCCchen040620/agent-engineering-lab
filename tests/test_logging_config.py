import logging

from backend.logging_config import configure_logging


def test_configure_logging_can_run_without_error():
    configure_logging()

    assert logging.getLogger() is not None