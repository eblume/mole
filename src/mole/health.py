from dataclasses import dataclass
from enum import Enum


class Status(Enum):
    SUCCESS = "success"
    PENDING = "pending"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    @property
    def color(self) -> str:
        match self.value:
            case self.SUCCESS.value:
                return "green"
            case self.PENDING.value:
                return "yellow"
            case self.ERROR.value:
                return "red"
            case self.WARNING.value:
                return "orange"
            case self.INFO.value:
                return "blue"
            case _:
                return "white"

    @property
    def emoji(self) -> str:
        match self.value:
            case self.SUCCESS.value:
                return "✅"
            case self.PENDING.value:
                return "🕒"
            case self.ERROR.value:
                return "❌"
            case self.WARNING.value:
                return "⚠️"
            case self.INFO.value:
                return "ℹ️"
            case _:
                return "❓"


@dataclass
class HealthCheck:
    name: str
    status: Status
    message: str

    @property
    def finished(self) -> bool:
        return self.status not in (Status.PENDING, Status.INFO)


def health_checks() -> list[HealthCheck]:
    return [
        python_version_check(),
    ]


def python_version_check() -> HealthCheck:
    """Check that the python version is supported

    Not a terribly useful check, but it's a good example of how to write a health check."""
    import sys

    if sys.version_info < (3, 11):
        # There is no reason I chose 3.11 other than that I'm currently on it. We could push this down to 3.9 I think.
        return HealthCheck(
            name="Python Version",
            status=Status.ERROR,
            message=f"Python version {sys.version_info} is not supported. Please use Python 3.11 or higher.",
        )
    elif sys.version_info > (3, 12):
        # This is probably overthinking it but if mole is running on a version of python that is newer than I've coded
        # for, it's probably worth a warning. One solution to this warning might be to just bump these numbers.
        return HealthCheck(
            name="Python Version",
            status=Status.WARNING,
            message=f"Python version {sys.version_info} is not supported. Please use Python 3.11 or lower.",
        )
    return HealthCheck(
        name="Python Version",
        status=Status.SUCCESS,
        message=f"Python version {sys.version_info} is supported.",
    )
