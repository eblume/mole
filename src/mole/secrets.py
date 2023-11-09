import subprocess


def get_secret(key: str, field: str, vault: str = None, extra: list[str] = None) -> str:
    """Get a secret from 1password."""
    command = ["op", "item"]
    if vault:
        command.extend(["--vault", vault])
    command.extend(["get", key, "--fields", field])
    if extra:
        command.extend(extra)

    return subprocess.check_output(command).decode("utf-8").strip()
