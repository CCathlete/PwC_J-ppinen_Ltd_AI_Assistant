from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass(frozen=True)
class KnowledgeBaseConfig:
    name: str
    description: str
    public: bool

    @staticmethod
    def load(path: Path) -> "KnowledgeBaseConfig":
        data = yaml.safe_load(path.read_text())
        return KnowledgeBaseConfig(
            name=data["name"],
            description=data.get("description", ""),
            public=data.get("public", False),
        )
