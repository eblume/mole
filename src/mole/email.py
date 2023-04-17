from __future__ import annotations

import subprocess
import tempfile

import typer

GET_EMAIL_COUNT_APPLESCRIPT = """
tell application "Mail"
    set checkAccount to account "{account}"
    set checkInbox to mailbox "{inbox}" of checkAccount
    set unread to (messages of checkInbox whose read status is false)
    set countUnread to count of unread
    return countUnread
end tell

"""

def run_applescript(script: str) -> str:
    with tempfile.NamedTemporaryFile(suffix='.scpt', mode='w') as temp_file:
        temp_file.write(script)
        temp_file.flush()
        return subprocess.check_output(['osascript', temp_file.name]).decode('utf-8')


def get_email_count(account: str, inbox: str) -> int:
    """Return the number of unread emails in the inbox, using Mail.app via AppleScript"""
    script = GET_EMAIL_COUNT_APPLESCRIPT.format(account=account, inbox=inbox)
    output = run_applescript(script).strip()
    count = int(output)
    typer.secho(f"📬 [{account}/{inbox}] {count}", fg=typer.colors.GREEN if count == 0 else typer.colors.BLUE)
    return count

