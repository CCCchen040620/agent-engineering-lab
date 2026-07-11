import logging

from backend.logging_config import configure_logging
from backend.request_context import reset_request_id, set_request_id


def test_configure_logging_can_run_without_error():
    configure_logging()

    assert logging.getLogger() is not None


def test_log_record_has_request_id(caplog):
    configure_logging()
    caplog.set_level(logging.INFO)
    token = set_request_id("test-request-id")

    logging.getLogger("test_logger").info("测试日志")

    reset_request_id(token)

    assert caplog.records[-1].request_id == "test-request-id"
