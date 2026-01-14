"""AWS credentials data model."""
from dataclasses import dataclass


@dataclass
class AWSCredentials:
    """AWS 凭证"""
    access_key_id: str
    secret_access_key: str
    region: str = "us-east-1"
    session_token: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        result = {
            "access_key_id": self.access_key_id,
            "secret_access_key": self.secret_access_key,
            "region": self.region,
        }
        if self.session_token:
            result["session_token"] = self.session_token
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "AWSCredentials":
        """Create from dictionary."""
        return cls(
            access_key_id=data["access_key_id"],
            secret_access_key=data["secret_access_key"],
            region=data.get("region", "us-east-1"),
            session_token=data.get("session_token"),
        )
