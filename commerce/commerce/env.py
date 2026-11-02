import os
from pathlib import Path


def load_dotenv(base_dir: Path) -> None:
    env_path = base_dir / ".env"
    if not env_path.is_file():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def env_bool(key: str, default: bool = False) -> bool:
    value = os.environ.get(key)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def env_list(key: str, default: list[str]) -> list[str]:
    value = os.environ.get(key, "").strip()
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]
