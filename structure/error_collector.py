from typing import Self, TypeAlias

from structure.types import OsmElementT


class ErrorCollector:
    """Class to hold error, warning and notice messages."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notices: list[str] = []

    @staticmethod
    def format_message(text: str, el: OsmElementT) -> str:
        if el:
            typ = el["type"]
            id_ = el.get("id", el.get("ref"))
            tags = el.get("tags", {})
            name = tags.get("name", tags.get("ref", ""))
            text = f'{text} ({typ} {id_}, "{name}")'
        return text

    def notice(self, message: str, el: OsmElementT | None = None) -> None:
        """This type of message may point to a potential problem."""
        msg = self.format_message(message, el)
        self.notices.append(msg)

    def warn(self, message: str, el: OsmElementT | None = None) -> None:
        """A warning is definitely a problem but is doesn't prevent
        from building a routing file and doesn't invalidate the city.
        """
        msg = self.format_message(message, el)
        self.warnings.append(msg)

    def error(self, message: str, el: OsmElementT | None = None) -> None:
        """Error is a critical problem that invalidates the city."""
        msg = self.format_message(message, el)
        self.errors.append(msg)


class ErrorCollectorHolder:
    """Mixin for classes that contain an ErrorCollector instance.
    It's supposed the City class inherits this mixin.
    """

    def __init__(self) -> None:
        self.error_collector = ErrorCollector()


ErrorCollectorHolderMixin: TypeAlias = Self | ErrorCollectorHolder


class ErrorCollectorGate:
    """The class contains notice()/warn()/error() and some other
    methods that forward their calls to the nested error_collector attribute
    of the ErrorCollector type. Intended for StopArea, Route and other
    classes that generate errors/warnings for a city validation report.
    """

    def __init__(self, error_collector: ErrorCollector) -> None:
        self.error_collector = error_collector

    def notice(
        self: Self | ErrorCollectorHolderMixin,
        message: str,
        el: OsmElementT | None = None,
    ) -> None:
        self.error_collector.notice(message, el)

    def warn(
        self: Self | ErrorCollectorHolderMixin,
        message: str,
        el: OsmElementT | None = None,
    ) -> None:
        self.error_collector.warn(message, el)

    def error(
        self: Self | ErrorCollectorHolderMixin,
        message: str,
        el: OsmElementT | None = None,
    ) -> None:
        self.error_collector.error(message, el)

    @property
    def has_errors(self: Self | ErrorCollectorHolderMixin) -> bool:
        return bool(self.error_collector.errors)

    @property
    def notices(self: Self | ErrorCollectorHolderMixin) -> list[str]:
        return self.error_collector.notices

    @property
    def warnings(self: Self | ErrorCollectorHolderMixin) -> list[str]:
        return self.error_collector.warnings

    @property
    def errors(self: Self | ErrorCollectorHolderMixin) -> list[str]:
        return self.error_collector.errors
