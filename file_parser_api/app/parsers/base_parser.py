from abc import ABC, abstractmethod


class BaseParser(ABC):
    """Interface for all parsers."""

    @abstractmethod
    def parse(self, file_path: str) -> str:
        """Return file content as Markdown string."""
        raise NotImplementedError


