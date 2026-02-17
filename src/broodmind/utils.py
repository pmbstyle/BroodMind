from __future__ import annotations

from datetime import UTC, datetime


import subprocess

import json

def get_tailscale_ips() -> list[str]:
    """Retrieve all available Tailscale IPs in the tailnet using JSON output."""
    try:
        # tailscale status --json provides a detailed list of all nodes and their IPs.
        out = subprocess.check_output(["tailscale", "status", "--json"], text=True, stderr=subprocess.DEVNULL)
        data = json.loads(out)
        ips = []
        
        # Add self IPs
        if "Self" in data and "TailscaleIPs" in data["Self"]:
            ips.extend(data["Self"]["TailscaleIPs"])
            
        # Add peer IPs
        if "Peer" in data:
            for peer in data["Peer"].values():
                if "TailscaleIPs" in peer:
                    ips.extend(peer["TailscaleIPs"])
                    
        return list(set(ips))  # Unique IPs
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
        return []


def utc_now() -> datetime:
    return datetime.now(UTC)


def is_heartbeat_ok(text: str) -> bool:
    """Check if the text contains HEARTBEAT_OK (case-insensitive) and is exactly one line."""
    value = (text or "").strip()
    if not value:
        return False
    # Must contain HEARTBEAT_OK and have no internal newlines
    return "HEARTBEAT_OK" in value.upper() and "\n" not in value


def is_control_response(text: str) -> bool:
    """Check if the text is a system control message like HEARTBEAT_OK or NO_USER_RESPONSE."""
    value = (text or "").strip()
    if not value:
        return True
        
    if is_heartbeat_ok(value):
        return True
        
    # Check for NO_USER_RESPONSE variations
    normalized = value.upper().replace("_", "").replace(" ", "")
    if normalized == "NOUSERRESPONSE":
        return True
        
    return False
