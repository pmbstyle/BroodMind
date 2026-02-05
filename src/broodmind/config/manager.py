from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv, set_key, get_key


class ConfigManager:
    def __init__(self, env_path: str | Path = ".env") -> None:
        self.env_path = Path(env_path)
        if not self.env_path.exists():
            self.env_path.touch(mode=0o600)
        load_dotenv(self.env_path)

    def set(self, key: str, value: Any) -> None:
        """Set a value in the .env file."""
        if value is None:
            value = ""
        str_value = str(value)
        set_key(str(self.env_path), key, str_value)
        # Update current environment so subsequent calls in the same process see it
        os.environ[key] = str_value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the .env file or environment."""
        val = get_key(str(self.env_path), key)
        if val is None:
            return os.environ.get(key, default)
        return val

    def exists(self) -> bool:
        return self.env_path.exists()
