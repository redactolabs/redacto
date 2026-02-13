"""
Security schema for input sanitization and validation.

This module provides a framework-agnostic security layer for validating and sanitizing
user inputs to protect against XSS, HTML injection, and other security vulnerabilities.

Features:
- String sanitization with email preservation
- HTML sanitization with configurable allowed tags
- Quill editor content sanitization with CSS support
- SVG file upload sanitization
"""

import html
import re
from functools import wraps
from typing import Annotated, Any, BinaryIO, Protocol, runtime_checkable
import bleach
from bleach.css_sanitizer import CSSSanitizer

from py_svg_hush import filter_svg
from pydantic import BaseModel as Schema
from pydantic import AfterValidator, field_validator, ValidationInfo

from redacto.security.constants import BASIC_HTML_ALLOWED_ATTRIBUTES, BASIC_HTML_ALLOWED_TAGS, QUILL_STRING_INPUT_ALLOWED_ATTRIBUTES, QUILL_STRING_INPUT_ALLOWED_CSS_PROPERTIES, QUILL_STRING_INPUT_ALLOWED_TAGS

# Optional HttpError import with fallback
try:
    from ninja.errors import HttpError

except ImportError:
    # Fallback for when Django Ninja is not installed
    class HttpError(Exception):  # type: ignore
        """Fallback HttpError class for non-Django-Ninja environments."""

        def __init__(self, status_code: int, message: str):
            self.status_code = status_code
            super().__init__(message)



@runtime_checkable
class FileUpload(Protocol):
    """
    Protocol for file upload objects from any framework (Django, FastAPI, etc.).

    This protocol defines the minimal interface required for file upload sanitization,
    making the code framework-agnostic and compatible with:
    - Django: UploadedFile, InMemoryUploadedFile
    - FastAPI: fastapi.UploadFile
    - Django Ninja: ninja.files.UploadedFile
    - Any custom implementation matching this interface
    """

    name: str
    file: BinaryIO  # File-like object with seek() and read()
    content_type: str | None  # Optional MIME type


class SecureSchema(Schema):
    """
    Base Pydantic schema with built-in security sanitization.

   """

    @staticmethod
    def string_input_sanitizer(v: str, field_name: str) -> str:
        """
    
        This sanitizer protects against HTML and XSS injection attacks while
        preserving legitimate content like email addresses in angle brackets
        (e.g., <noreply@redacto.io>).

        """
        original = html.unescape(v)

        # Extract and temporarily replace email patterns
        email_pattern = r"<[^<>@\s]+@[^<>@\s]+\.[^<>@\s]+>"
        matches = re.findall(email_pattern, v)
        placeholders = {}
        for i, email in enumerate(matches):
            key = f"__EMAIL_PLACEHOLDER_{i}__"
            placeholders[key] = email
            v = v.replace(email, key)

        # Sanitize the input
        sanitized_input = bleach.clean(v, tags=[], attributes={}, strip=True)

        # Restore email placeholders
        for key, email in placeholders.items():
            sanitized_input = sanitized_input.replace(key, email)

        cleaned = html.unescape(sanitized_input)

        # Compare cleaned version with original
        if cleaned != original:
            raise ValueError(
                f"string field name: {field_name} - Input contains unsafe HTML or XSS content. "
                "Please provide a safe input."
            )

        return original

    @staticmethod
    def html_input_sanitizer(v: str, info: ValidationInfo) -> str:
        """
        This sanitizer allows a wide range of HTML tags and attributes for
        rich content, while still protecting against XSS attacks.

        """
        field_name = getattr(info, "field_name", None)

        sanitized_input = bleach.clean(
            v,
            tags=BASIC_HTML_ALLOWED_TAGS,
            attributes=BASIC_HTML_ALLOWED_ATTRIBUTES,
            strip=True,
        )

        if sanitized_input != v:
            raise ValueError(
                f"HTML field name: {field_name} - Input contains unsafe HTML or XSS content. "
                "Please provide a safe input to HTML input field."
            )

        return v

    @staticmethod
    def quill_string_input_sanitizer(v: str, info: ValidationInfo) -> str:
        """
        This sanitizer allows Quill editor formatting tags and a limited subset
        of CSS properties (color and background-color only).

        """
        field_name = getattr(info, "field_name", "html_field")

        css_sanitizer = CSSSanitizer(
            allowed_css_properties=QUILL_STRING_INPUT_ALLOWED_CSS_PROPERTIES,
        )

        cleaner = bleach.Cleaner(
            tags=QUILL_STRING_INPUT_ALLOWED_TAGS,
            attributes=QUILL_STRING_INPUT_ALLOWED_ATTRIBUTES,
            protocols=["http", "https", "mailto", "tel"],
            strip=True,  # drop disallowed tags entirely
            css_sanitizer=css_sanitizer,
        )

        sanitized_input = cleaner.clean(v)

        if sanitized_input != v:
            raise ValueError(
                f"HTML field '{field_name}' contains unsafe or disallowed HTML/CSS. "
                "Please provide safe HTML input."
            )

        return v

    @staticmethod
    def svg_file_sanitizer(file: FileUpload, field_name: str = "") -> FileUpload:
        """

        Currently supports SVG sanitization. This method is framework-agnostic
        and works with file upload objects from Django, FastAPI, or any other
        framework that matches the FileUpload protocol.

        """
        if not file or not hasattr(file, "name"):
            return file

        # Check if the file is an SVG
        is_svg = file.name.lower().endswith(".svg") or (
            hasattr(file, "content_type") and file.content_type == "image/svg+xml"
        )

        if is_svg:
            keep_data_url_mime_types = {
                "image": ["jpeg", "png", "gif"],
            }
            try:
                # Read file content from the uploaded file object
                file.file.seek(0)
                content = file.file.read()
                file.file.seek(0)  # Reset position after reading

                if not isinstance(content, bytes):
                    content = str(content).encode("utf-8")
                original_content_str = content.decode("utf-8")

                # Sanitize the SVG content
                sanitized_content = filter_svg(content, keep_data_url_mime_types)

                if isinstance(sanitized_content, bytes):
                    sanitized_content_str = sanitized_content.decode("utf-8")
                else:
                    sanitized_content_str = sanitized_content

                # Check if significant content was removed (indicating unsafe content)
                original_size = len(original_content_str.strip())
                sanitized_size = len(sanitized_content_str.strip())
                size_difference = abs(original_size - sanitized_size)

                size_threshold = max(50, original_size * 0.1)

                if size_difference > size_threshold:
                    raise ValueError(
                        f"SVG field name: {field_name} - Input SVG contains unsafe content. "
                        "Please provide a safe SVG file."
                    )

            except Exception as e:
                raise ValueError(
                    f"SVG field name: {field_name} - Error processing SVG file: {str(e)}"
                )

        return file

    @field_validator("*", mode="after")
    @classmethod
    def string_input_validator(cls, v: Any, info: ValidationInfo) -> Any:
        field_name = getattr(info, "field_name", None)
        if isinstance(v, str):
            return cls.string_input_sanitizer(v, field_name)
        return v

    @staticmethod
    def sanitize_file_uploads(func):
        """
        Decorator that automatically sanitizes all file uploads in an endpoint.
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                sanitized_kwargs = {}
                for key, value in kwargs.items():
                    # Check if value matches FileUpload protocol
                    if isinstance(value, FileUpload):
                        sanitized_kwargs[key] = SecureSchema.svg_file_sanitizer(
                            value, key
                        )

                    elif isinstance(value, list) and value and len(value) > 0:
                        # Check if it's a list of file uploads
                        if isinstance(value[0], FileUpload):
                            sanitized_kwargs[key] = [
                                SecureSchema.svg_file_sanitizer(f, f"{key}[{i}]")
                                for i, f in enumerate(value)
                            ]
                        else:
                            sanitized_kwargs[key] = value
                    else:
                        sanitized_kwargs[key] = value

                return func(*args, **sanitized_kwargs)

            except ValueError as e:
                error_message = str(e)
                raise HttpError(400, error_message)

        return wrapper



# Plain string with no HTML allowed (safest, default behavior)
NoHtmlString = Annotated[str, AfterValidator(SecureSchema.string_input_sanitizer)]

# Rich HTML string with allowed tags and attributes
BasicHtmlString = Annotated[str, AfterValidator(SecureSchema.html_input_sanitizer)]

# Quill editor string with limited HTML and CSS support
QuillEditorString = Annotated[
    str, AfterValidator(SecureSchema.quill_string_input_sanitizer)
]
