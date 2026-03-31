class APIError(Exception):
    """Base API error."""


class APIConnectionError(APIError):
    """Raised when the remote service cannot be reached."""


class APIUnavailableError(APIError):
    """Raised when the remote service is unavailable."""


class APINotFoundError(APIError):
    """Raised when the requested endpoint does not exist."""


class APIResponseError(APIError):
    """Raised when the response payload is invalid or unexpected."""


class APIRateLimitError(APIError):
    """Raised when the remote service rejects requests due to rate limits."""


class APITimeoutError(APIError):
    """Raised when a request times out."""


class APIUnauthorizedError(APIError):
    """Raised when the request is unauthorized."""


class APIRetryExhaustedError(APIError):
    """Raised when retry attempts are exhausted."""
