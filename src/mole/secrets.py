import re
import subprocess
from typing import Optional


def get_secret(key: str, field: str, vault: Optional[str] = None, extra: Optional[list[str]] = None) -> str:
    """Get a secret from 1password."""
    command = ["op", "item"]
    ## I've recently discovered that it incurs on the order of THOUSANDS of additional requests to 1password whenever I use a string-name for vault and key, which quickly exceeds the rate limit.
    # So, we'll do some checks to make sure we're not doing that, and use UUIDs instead.
    # If the key or vault is an id, we'll just use it as-is. If it's not, we check the VAULTS dict for common lookups,
    # and use the id from there. If it's not in there, we COULD do something like warn the user and proceed, but it's
    # seriously killing my rate limit, so I'm just going to fail.
    if vault is None:
        vault = VAULTS["Personal"]  # This is also the default behavior for op, but this makes the code nicer.
    else:
        if not re.match(r"^[0-9a-z]{26}$", vault):
            vault = VAULTS[vault]
        command.extend(["--vault", vault])

    if not re.match(r"^[0-9a-z]{26}$", key):
        if key in COMMON_KEYS[vault]:
            key = COMMON_KEYS[vault][key]
        else:
            # See the note above; this is a recoverable failure I am choosing not to recover from.
            # Just use op item get to find the id and add it to COMMON_KEYS.
            raise ValueError(f"Unable to look up key {key} in vault {vault} - use a UUID or add it to COMMON_KEYS")

    command.extend(["get", key, "--fields", field])
    if extra:
        command.extend(extra)

    try:
        output = subprocess.check_output(command, timeout=10).decode("utf-8").strip()
    except subprocess.TimeoutExpired:
        # Try one more time - sometimes the first request times out, but the second one works, I don't know why.
        # This creates a problem though for the user, they only get 10s to enter their password the first time. But
        # they'll get more time the second time, meanwhile users who got it right the first time won't have to see a
        # failure message they didn't cause.
        #
        # I think this might have something to do with `nb sync` and the github ssh key agent, somehow? I don't know.
        output = subprocess.check_output(command).decode("utf-8").strip()

    return output


## No, these aren't actually secrets. They are just 1password key names and vault names converted to ids so that we can avoid doing name-id lookups. See the note in get_secret for more info.


VAULTS = {
    "Personal": "wpwhqn557rkb4ybpyvdxi5wsmu",
    "blumeops": "vg6xf6vvfmoh5hqjjhlhbeoaie",
}


COMMON_KEYS = {
    "wpwhqn557rkb4ybpyvdxi5wsmu": {},
    "vg6xf6vvfmoh5hqjjhlhbeoaie": {
        "OpenAI": "5dam3u2wbiqjs4lfci5iln54n4",
        "Todoist": "c53h3xnmswhvexa5mntoyvhgpm",
    },
}
