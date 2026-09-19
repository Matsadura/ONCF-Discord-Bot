class ONCFBotException(Exception):
    """Base exception for ONCF Bot."""
    pass

class ONCFAPIError(ONCFBotException):
    """Raised when the ONCF API returns an error or fails."""
    pass

class StationNotFoundError(ONCFBotException):
    """Raised when a station is not found in the dictionary."""
    pass

class AuthenticationFailedError(ONCFBotException):
    """Raised when login fails."""
    pass
