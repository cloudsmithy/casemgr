"""Filter data models."""
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .case import CaseStatus


@dataclass
class Filters:
    """过滤条件"""
    status: list["CaseStatus"] | None = None
    severity: list[str] | None = None
    search_text: str | None = None
    include_archived: bool = False
    archived_only: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        from .case import CaseStatus
        return {
            "status": [s.value for s in self.status] if self.status else None,
            "severity": self.severity,
            "search_text": self.search_text,
            "include_archived": self.include_archived,
            "archived_only": self.archived_only,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Filters":
        """Create from dictionary."""
        from .case import CaseStatus
        status = None
        if data.get("status"):
            status = [CaseStatus(s) for s in data["status"]]
        return cls(
            status=status,
            severity=data.get("severity"),
            search_text=data.get("search_text"),
            include_archived=data.get("include_archived", False),
            archived_only=data.get("archived_only", False),
        )
