"""Case data models."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .communication import Communication


class CaseStatus(Enum):
    """案例状态"""
    OPENED = "opened"
    PENDING_CUSTOMER_ACTION = "pending-customer-action"
    RESOLVED = "resolved"
    UNASSIGNED = "unassigned"
    WORK_IN_PROGRESS = "work-in-progress"


@dataclass
class Case:
    """案例"""
    case_id: str
    display_id: str
    subject: str
    status: CaseStatus
    service_code: str
    category_code: str
    severity_code: str
    submitted_by: str
    time_created: datetime
    language: str = "zh"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "case_id": self.case_id,
            "display_id": self.display_id,
            "subject": self.subject,
            "status": self.status.value,
            "service_code": self.service_code,
            "category_code": self.category_code,
            "severity_code": self.severity_code,
            "submitted_by": self.submitted_by,
            "time_created": self.time_created.isoformat(),
            "language": self.language,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Case":
        """Create from dictionary."""
        return cls(
            case_id=data["case_id"],
            display_id=data["display_id"],
            subject=data["subject"],
            status=CaseStatus(data["status"]),
            service_code=data["service_code"],
            category_code=data["category_code"],
            severity_code=data["severity_code"],
            submitted_by=data["submitted_by"],
            time_created=datetime.fromisoformat(data["time_created"]),
            language=data.get("language", "zh"),
        )


@dataclass
class CaseDetail(Case):
    """案例详情"""
    cc_email_addresses: list[str] = field(default_factory=list)
    communications: list["Communication"] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        from .communication import Communication
        base = super().to_dict()
        base["cc_email_addresses"] = self.cc_email_addresses
        base["communications"] = [c.to_dict() for c in self.communications]
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "CaseDetail":
        """Create from dictionary."""
        from .communication import Communication
        return cls(
            case_id=data["case_id"],
            display_id=data["display_id"],
            subject=data["subject"],
            status=CaseStatus(data["status"]),
            service_code=data["service_code"],
            category_code=data["category_code"],
            severity_code=data["severity_code"],
            submitted_by=data["submitted_by"],
            time_created=datetime.fromisoformat(data["time_created"]),
            language=data.get("language", "zh"),
            cc_email_addresses=data.get("cc_email_addresses", []),
            communications=[
                Communication.from_dict(c) for c in data.get("communications", [])
            ],
        )
