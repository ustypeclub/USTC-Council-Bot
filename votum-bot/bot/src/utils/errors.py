"""Custom exception types for Votum.

Using distinct exception types makes it easier to handle different error
conditions in command handlers and display appropriate user feedback.
"""

class VotumError(Exception):
    """Base class for all custom errors in Votum."""


class ConfigError(VotumError):
    """Raised when a configuration value is invalid or missing."""


class PermissionError(VotumError):
    """Raised when a user lacks permission to perform an action."""