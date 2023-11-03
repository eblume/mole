import subprocess
import json

import typer
from watchdog.observers import Observer
from watchdog.events import FileCreatedEvent

from .voicememo import VoiceMemoHandler, ensure_voicememo


OBSERVER_JOIN_INTERVAL = 1  # seconds


def whack() -> None:
    """A long-lived watcher process that will react to certain events."""

    typer.echo("Whacking moles 🐹")
    user = json.loads(subprocess.check_output("op user get --me --format=json", shell=True))
    typer.echo(f"Running as {user['name']} <{user['email']}> (id: {user['id']})")

    # Setup
    ensure_voicememo()  # ensures a sane environment for voice memo transcription
    observer = WhackObserver()
    observer.start()

    try:
        # I need to harp about something for a second. The whole reason I decided to go down the rabbithole of using
        # an FSEvent/inotify/kqueue-aware watch library is because I wanted to avoid polling. But here I am, polling.
        # This is sloppy threading code. I should be able to call this like select(), all in one thread, and get
        # woken up as soon as an event is ready (or timeout). Delegating it to a separate thread is a cop-out. Well,
        # at least we are avoiding the massive FS scan that would happen if we didn't use a library like this.
        while observer.is_alive():
            observer.join(OBSERVER_JOIN_INTERVAL)  # wait for a bit.

    finally:
        observer.stop()
        observer.join()


class WhackObserver(Observer):
    """Specialized event observer for whack."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # We'll go ahead and schedule our handlers right here, since we know them.
        self._vm_handler = VoiceMemoHandler()
        self.schedule(self._vm_handler, path=VoiceMemoHandler.path, recursive=True)

    def start(self):
        super().start()

        # Immediately inject a synthetic event for all existing m4a files
        # (This should probably be part of a new Emitter class but I don't know how to hook that up to the OS-detected
        # Handler class, so this will do for now.)
        for path in VoiceMemoHandler._path.glob("**/*.m4a"):
            if path.is_file():
                event = FileCreatedEvent(str(path))
                event.is_synthetic = True
                self._vm_handler.on_created(event)
