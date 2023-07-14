from functools import wraps
from typing import Any


import typer
import sys
import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError, ProfileNotFound


# TODO this should eventually literally import the blumoops package, but we're a ways off from that


_SESSION = None


def boto_resource(service_name: str) -> Any:
    global _SESSION
    if _SESSION is None:
        _SESSION = boto3.Session(profile_name="blumeops")
    return _SESSION.resource(service_name)


def has_blumeops_profile() -> bool:
    try:
        boto_resource('sts').get_caller_identity()
        return True
    except (BotoCoreError, NoCredentialsError, ProfileNotFound):
        return False

def require_blumeops(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        if not has_blumeops_profile():
            typer.secho('🚨 No blumeops profile found, cannot run command', fg=typer.colors.RED)
            typer.secho(f"Try `aws-vault exec blumeops -- mole {' '.join(sys.argv[1:])}`", fg=typer.colors.YELLOW)
            raise typer.Exit(1)
        return func(*args, **kwargs)
    return wrapped
