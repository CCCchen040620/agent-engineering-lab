import logging

from backend.request_context import get_request_id


def configure_request_id_record_factory() -> None:
    current_factory = logging.getLogRecordFactory()

    if getattr(current_factory, "adds_request_id", False):
        return

    def record_factory(*args, **kwargs):
        record = current_factory(*args, **kwargs)
        record.request_id = get_request_id()
        return record

    record_factory.adds_request_id = True
    logging.setLogRecordFactory(record_factory)


def configure_logging() -> None:
    configure_request_id_record_factory()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | request_id=%(request_id)s | %(message)s",
    )
