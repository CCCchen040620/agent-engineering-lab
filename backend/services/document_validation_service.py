from backend.config import (
    MAX_DOCUMENT_CONTENT_CHARS,
    MAX_DOCUMENT_TITLE_CHARS,
    MAX_UPLOAD_FILE_BYTES,
)


class DocumentValidationError(Exception):
    def __init__(self, message: str, status_code: int = 422):
        super().__init__(message)
        self.status_code = status_code


def validate_document_title(
    title: str,
    max_chars: int = MAX_DOCUMENT_TITLE_CHARS,
) -> None:
    if len(title) > max_chars:
        raise DocumentValidationError(
            f"文档标题过长，最多支持 {max_chars} 个字符。",
            status_code=422,
        )


def validate_document_content(
    content: str,
    max_chars: int = MAX_DOCUMENT_CONTENT_CHARS,
) -> None:
    if len(content) > max_chars:
        raise DocumentValidationError(
            f"文档正文过长，最多支持 {max_chars} 个字符。",
            status_code=413,
        )


def validate_upload_file_size(
    content_bytes: bytes,
    max_bytes: int = MAX_UPLOAD_FILE_BYTES,
) -> None:
    if len(content_bytes) > max_bytes:
        raise DocumentValidationError(
            f"上传文件过大，最大支持 {max_bytes} 字节。",
            status_code=413,
        )
