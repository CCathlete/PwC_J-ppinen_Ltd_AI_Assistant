from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv
from returns.result import safe
import os


@dataclass(frozen=True)
class Env:
    vars: dict[str, str | bool | int | float] = field(default_factory=dict)

    @safe
    def load(self, path_to_dotenv: str | Path = ".env") -> "Env":
        load_dotenv(dotenv_path=path_to_dotenv)
        loaded_vars = {
            k: self._parse_value(v)
            for k, v in os.environ.items()
            if v
        }
        return Env(vars=loaded_vars)

    @safe
    def export(self) -> None:
        for key, value in self.vars.items():
            os.environ[key] = str(value)

    @staticmethod
    def _parse_value(value: str) -> str | bool | int | float:
        if value.lower() in {"true", "false"}:
            return value.lower() == "true"
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            return value
