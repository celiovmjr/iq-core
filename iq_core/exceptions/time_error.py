from .iqoption_error import IQOptionError

class InvalidTargetTime(IQOptionError, ValueError):
    """Raised when the target time is invalid or in the past."""
