"""Case creation parameters data model."""
from dataclasses import dataclass


@dataclass
class CreateCaseParams:
    """创建案例参数"""
    subject: str
    service_code: str
    category_code: str
    severity_code: str
    communication_body: str
    cc_email_addresses: list[str] | None = None
    language: str = "zh"
    attachment_set_id: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "subject": self.subject,
            "service_code": self.service_code,
            "category_code": self.category_code,
            "severity_code": self.severity_code,
            "communication_body": self.communication_body,
            "cc_email_addresses": self.cc_email_addresses,
            "language": self.language,
            "attachment_set_id": self.attachment_set_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CreateCaseParams":
        """Create from dictionary."""
        return cls(
            subject=data["subject"],
            service_code=data["service_code"],
            category_code=data["category_code"],
            severity_code=data["severity_code"],
            communication_body=data["communication_body"],
            cc_email_addresses=data.get("cc_email_addresses"),
            language=data.get("language", "zh"),
            attachment_set_id=data.get("attachment_set_id"),
        )
