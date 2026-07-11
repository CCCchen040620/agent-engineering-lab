import pytest

from backend.services.document_validation_service import (
    DocumentValidationError,
    validate_document_content,
    validate_document_title,
    validate_upload_file_size,
)


def test_validate_document_title_allows_valid_title():
    validate_document_title("员工手册", max_chars=10)


def test_validate_document_title_rejects_too_long_title():
    with pytest.raises(DocumentValidationError) as error:
        validate_document_title("a" * 11, max_chars=10)

    assert error.value.status_code == 422
    assert "文档标题过长" in str(error.value)


def test_validate_document_content_rejects_too_long_content():
    with pytest.raises(DocumentValidationError) as error:
        validate_document_content("a" * 21, max_chars=20)

    assert error.value.status_code == 413
    assert "文档正文过长" in str(error.value)


def test_validate_upload_file_size_rejects_too_large_file():
    with pytest.raises(DocumentValidationError) as error:
        validate_upload_file_size(b"a" * 6, max_bytes=5)

    assert error.value.status_code == 413
    assert "上传文件过大" in str(error.value)
