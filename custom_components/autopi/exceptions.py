"""Exceptions for the AutoPi integration."""

from __future__ import annotations

from typing import Any


class AutoPiError(Exception):
    """Base exception for all AutoPi integration errors."""


class AutoPiAuthenticationError(AutoPiError):
    """Exception raised when authentication fails."""


class AutoPiConnectionError(AutoPiError):
    """Exception raised when connection to AutoPi API fails."""


class AutoPiAPIError(AutoPiError):
    """Exception raised when API returns an error."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code
            data: Additional error data
        """
        super().__init__(message)
        self.status_code = status_code
        self.data = data or {}


class AutoPiRateLimitError(AutoPiAPIError):
    """Exception raised when rate limit is exceeded."""


class AutoPiTimeoutError(AutoPiConnectionError):
    """Exception raised when request times out."""


class AutoPiInvalidConfigError(AutoPiError):
    """Exception raised when configuration is invalid."""


class AutoPiNoDataError(AutoPiError):
    """Exception raised when no data is available."""
