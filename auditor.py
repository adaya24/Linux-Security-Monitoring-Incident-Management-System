
import subprocess
from pathlib import Path


def check_firewall():
    """Check whether UFW or nftables appears active."""
    results = []

    try:
        ufw = subprocess.run(
            ["ufw", "status"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if ufw.returncode == 0:
            output = ufw.stdout.strip()

            if "Status: active" in output:
                results.append({
                    "check": "Firewall",
                    "status": "PASS",
                    "severity": "LOW",
                    "details": "UFW reports that the firewall is active."
                })
                return results

            if "Status: inactive" in output:
                results.append({
                    "check": "Firewall",
                    "status": "WARNING",
                    "severity": "MEDIUM",
                    "details": "UFW is inactive."
                })

    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    try:
        nft = subprocess.run(
            ["nft", "list", "ruleset"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if nft.returncode == 0 and nft.stdout.strip():
            results.append({
                "check": "Firewall",
                "status": "PASS",
                "severity": "LOW",
                "details": "An nftables ruleset exists; review its rules."
            })
        elif not results:
            results.append({
                "check": "Firewall",
                "status": "WARNING",
                "severity": "MEDIUM",
                "details": (
                    "No active firewall configuration was confirmed. "
                    "Check firewall rules and permissions manually."
                )
            })

    except (FileNotFoundError, subprocess.TimeoutExpired):
        if not results:
            results.append({
                "check": "Firewall",
                "status": "ERROR",
                "severity": "LOW",
                "details": "Unable to inspect firewall tools."
            })

    return results


def check_ssh_configuration():
    """Inspect explicit SSH settings without modifying them."""
    config_path = Path("/etc/ssh/sshd_config")

    if not config_path.exists():
        return [{
            "check": "SSH",
            "status": "WARNING",
            "severity": "LOW",
            "details": "SSH server configuration file was not found."
        }]

    settings = {}

    try:
        for line in config_path.read_text(
            encoding="utf-8",
            errors="replace"
        ).splitlines():
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split(None, 1)
            if len(parts) == 2:
                settings[parts[0].lower()] = parts[1].lower()

    except PermissionError:
        return [{
            "check": "SSH",
            "status": "ERROR",
            "severity": "LOW",
            "details": "Permission denied reading SSH configuration."
        }]

    results = []

    root_login = settings.get("permitrootlogin")
    password_auth = settings.get("passwordauthentication")

    if root_login == "yes":
        results.append({
            "check": "SSH root login",
            "status": "WARNING",
            "severity": "HIGH",
            "details": "Explicit PermitRootLogin yes was found."
        })
    else:
        results.append({
            "check": "SSH root login",
            "status": "REVIEW",
            "severity": "LOW",
            "details": (
                "Explicit root-login setting is not 'yes'. "
                "Verify effective SSH settings separately."
            )
        })

    if password_auth == "yes":
        results.append({
            "check": "SSH password authentication",
            "status": "REVIEW",
            "severity": "MEDIUM",
            "details": (
                "Password authentication is explicitly enabled. "
                "Check whether this matches your security policy."
            )
        })
    else:
        results.append({
            "check": "SSH password authentication",
            "status": "REVIEW",
            "severity": "LOW",
            "details": (
                "Password authentication is not explicitly set to yes. "
                "Verify effective SSH settings separately."
            )
        })

    return results


def run_audit():
    """Run available read-only security checks."""
    results = []
    results.extend(check_firewall())
    results.extend(check_ssh_configuration())
    return results


if __name__ == "__main__":
    for result in run_audit():
        print(
            f"[{result['status']}] {result['check']} "
            f"({result['severity']})"
        )
        print(" ", result["details"])

