from __future__ import annotations

DEFAULT_CAPABILITY_WHITELIST: dict[str, list[str]] = {
    "filesystem": ["worker", "/workspace/**"],
    "filesystem_read": ["worker"],
    "filesystem_write": ["worker"],
    "network": ["*"],
    "exec": ["worker", "python", "node"],
    "email": ["*"],
    "payment": [],
}
