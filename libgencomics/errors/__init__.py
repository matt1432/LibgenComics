class LibgenException(Exception):
    name = "LibgenException"

    def __init__(self, url: str | None) -> None:
        super().__init__(f"{self.name}: {url}")


class LibgenBadGatewayException(LibgenException):
    name = "LibgenBadGatewayException"


class LibgenMaxUserConnectionsException(LibgenException):
    name = "LibgenMaxUserConnectionsException"


class LibgenNginxException(LibgenException):
    name = "LibgenNginxException"


class LibgenNginxRateLimitedException(LibgenException):
    name = "LibgenNginxRateLimitedException"


class LibgenRateLimitedException(LibgenException):
    name = "LibgenRateLimitedException"


class LibgenRequestURITooLargeException(LibgenException):
    name = "LibgenRequestURITooLargeException"


class LibgenSSLHandshakeFailedException(LibgenException):
    name = "LibgenSSLHandshakeFailedException"


class LibgenTimeoutException(LibgenException):
    name = "LibgenTimeoutException"
