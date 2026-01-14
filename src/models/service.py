"""AWS service and severity data models."""
from dataclasses import dataclass, field


@dataclass
class Category:
    """服务类别"""
    code: str
    name: str

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "code": self.code,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Category":
        """Create from dictionary."""
        return cls(
            code=data["code"],
            name=data["name"],
        )


@dataclass
class Service:
    """AWS 服务"""
    code: str
    name: str
    categories: list[Category] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "code": self.code,
            "name": self.name,
            "categories": [c.to_dict() for c in self.categories],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Service":
        """Create from dictionary."""
        return cls(
            code=data["code"],
            name=data["name"],
            categories=[Category.from_dict(c) for c in data.get("categories", [])],
        )


@dataclass
class SeverityLevel:
    """严重级别"""
    code: str
    name: str

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "code": self.code,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SeverityLevel":
        """Create from dictionary."""
        return cls(
            code=data["code"],
            name=data["name"],
        )
