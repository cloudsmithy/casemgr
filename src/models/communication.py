"""Communication and attachment data models."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AttachmentInfo:
    """附件信息"""
    attachment_id: str
    file_name: str

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "attachment_id": self.attachment_id,
            "file_name": self.file_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AttachmentInfo":
        """Create from dictionary."""
        return cls(
            attachment_id=data["attachment_id"],
            file_name=data["file_name"],
        )


@dataclass
class Communication:
    """通信记录"""
    case_id: str
    body: str
    submitted_by: str
    time_created: datetime
    attachments: list[AttachmentInfo] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "case_id": self.case_id,
            "body": self.body,
            "submitted_by": self.submitted_by,
            "time_created": self.time_created.isoformat(),
            "attachments": [a.to_dict() for a in self.attachments],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Communication":
        """Create from dictionary."""
        return cls(
            case_id=data["case_id"],
            body=data["body"],
            submitted_by=data["submitted_by"],
            time_created=datetime.fromisoformat(data["time_created"]),
            attachments=[
                AttachmentInfo.from_dict(a) for a in data.get("attachments", [])
            ],
        )


@dataclass
class Attachment:
    """附件"""
    attachment_id: str
    file_name: str
    data: bytes

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization (without binary data)."""
        return {
            "attachment_id": self.attachment_id,
            "file_name": self.file_name,
        }
