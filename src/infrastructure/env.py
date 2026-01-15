# src/infrastructure/env.py
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv
import os

@dataclass(frozen=True)
class Env:
    vars: dict[str, str | bool | int | float] = field(default_factory=dict)

    def load(self, path_to_dotenv: str | Path = '.') -> "Env":
        """Load .env file and return a new Env with vars populated."""
        load_dotenv(dotenv_path=path_to_dotenv)
        loaded_vars = {k: self._parse_value(v) for k, v in os.environ.items()}
        # return a new instance since frozen=True
        return Env(vars=loaded_vars)

    @staticmethod
    def _parse_value(value: str) -> str | bool | int | float:
        """Convert string env value to appropriate type."""
        if value.lower() in {"true", "false"}:
            return value.lower() == "true"
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            return value

