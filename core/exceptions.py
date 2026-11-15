"""Custom exception classes for CSSA."""


class CSSAError(Exception):
    """Base exception for all CSSA errors."""
    pass


class PlatformNotSupportedError(CSSAError):
    """Raised when the current platform is not supported."""
    pass


class AdapterError(CSSAError):
    """Raised when a platform adapter encounters an error."""
    pass


class ScannerError(CSSAError):
    """Raised when a scanner module encounters an error."""
    pass


class RuleEngineError(CSSAError):
    """Raised when the rule engine encounters an error."""
    pass


class DatabaseError(CSSAError):
    """Raised when a database operation fails."""
    pass


class ReportGenerationError(CSSAError):
    """Raised when report generation fails."""
    pass


class CommandExecutionError(CSSAError):
    """Raised when a subprocess command fails."""

    def __init__(self, command: str, return_code: int | None = None,
                 stdout: str = "", stderr: str = "", message: str = ""):
        self.command = command
        self.return_code = return_code
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(message or f"Command failed: {command} (rc={return_code})")


class InsufficientPrivilegesError(CSSAError):
    """Raised when elevated privileges are required but not available."""
    pass


class ModuleUnavailableError(CSSAError):
    """Raised when a required system module or utility is unavailable."""

    def __init__(self, module_name: str, reason: str = ""):
        self.module_name = module_name
        self.reason = reason
        super().__init__(f"Module unavailable: {module_name}" +
                         (f" ({reason})" if reason else ""))


class ConfigurationError(CSSAError):
    """Raised when configuration is invalid or missing."""
    pass


class BaselineError(CSSAError):
    """Raised when baseline operations fail."""
    pass
