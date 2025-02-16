import subprocess
import tempfile
from pathlib import Path
from typing import Any

import typer
from watchdog.events import FileSystemEvent, FileSystemEventHandler

from .todoist import create_task

WHISPER_CPP = Path.home() / "code" / "3rd" / "whisper.cpp"


class VoiceMemoHandler(FileSystemEventHandler):
    """A handler for voice memo files."""

    _path = (
        Path.home()
        / "Library"
        / "Mobile Documents"
        / "iCloud~com~openplanetsoftware~just-press-record/Documents"
    )
    path = str(_path)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._seen = set()

    def dispatch(self, event: FileSystemEvent) -> None:
        """Dispatches events for VoiceMemo files.

        We only care about EVENT_TYPE_CREATED events.
        """
        match event.event_type:
            case "created":
                self.on_created(event)
            case _:
                pass  # We really only care about created events

    def on_created(self, event: Any):  # TODO: Tighten typing
        """Called when a file or directory is created."""

        if event.is_directory:
            return

        # Kludge: We receive multiple created events per file due to some sort of hacky thing JPR or iCloud is doing, I
        # guess. The files are slightly different each time, but not in a way I have figured out yet - something to do
        # with the stream size and bitrate, but nothing so much as a re-encoding. So instead we will just process each
        # file once, and ignore the rest. It might cause a problem when we go to unlink the file though, we'll see.
        if event.src_path in self._seen:
            return
        self._seen.add(event.src_path)

        if event.src_path.endswith(".m4a"):
            typer.echo(f"New voice memo: {event.src_path}")
            handle_vm(Path(event.src_path))


def handle_vm(path: Path) -> None:
    """Handles a voice memo file in m4a format.

    This function will:
    - Extract the datetime from the filename and path
    - Re-encode the audio to 16000Hz
    - Transcribe the audio using whisper.cpp
    - Extract tasks from the transcription using GPT-4
    - Create tasks in Todoist  # not currently implemented

    TODO:
    - Archive the audio.
    """
    # Re-encode the audio to 16000Hz wav using ffmpeg
    with tempfile.NamedTemporaryFile(suffix=".wav", mode="wb") as wav:
        # Convert and truncate audio using ffmpeg
        subprocess.run(
            [
                "ffmpeg",
                "-i",
                str(path),
                "-ar",
                "16000",
                "-t",
                "60",
                wav.name,
            ],
            check=True,
        )

        transcription = (
            subprocess.check_output(
                f"cd {WHISPER_CPP} && ./build/bin/whisper-cli -nt -f {wav.name} 2>/dev/null",
                shell=True,
            )
            .decode("utf-8")
            .strip()
        )
    cleaned = "\n".join(
        [line.strip() for line in transcription.split("\n") if line.strip()]
    )
    task_id = create_task(cleaned)
    typer.echo(f"todoist://showtask?id={str(task_id)}")

    # Finally, unlink audio
    path.unlink()
    return


def ensure_voicememo() -> None:
    """Ensures a sane environment for voice memo transcription.

    This function ensures that the following is true:
    - A 1Password service account is active
    - Just Press Record is installed from the mac apple store (uses mas tool)
    - Just Press Record is configured to save to iCloud
    - The iCloud JPR directory exists
    - Whisper.cpp is downloaded and built
    - OpenAI API key is set

    It will attempt to fix these issues if it can detect them broken, and it will also launch JPR and background it to make sure the app is syncing.
    """
    ## 1Password
    # Ensure 1Password CLI is installed by checking user info
    try:
        subprocess.check_output("op user get --me", shell=True)
    except subprocess.CalledProcessError:
        # In this case just bail, it isn't worth recovering
        typer.secho(
            "❌  1Password CLI is not installed or configured correctly. Please install it and configure it with a service account.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    # Note: We could here also confirm that the service account is active, but I don't think that's necessary.
    # If op can resolve the passwords without issue, it's fine.
    # If I run in to a lot of issues with `whack` hanging, it might be because of this.

    ## JPR (Just Press Record)

    # Ensure Just Press Record is installed
    try:
        subprocess.check_output("mas list | grep 'Just Press Record'", shell=True)
    except subprocess.CalledProcessError:
        typer.echo("Installing Just Press Record...")
        subprocess.check_output("mas install 1033342465", shell=True)

    # Ensure the iCloud JPR directory exists
    if not VoiceMemoHandler._path.exists():
        typer.echo(
            "Creating iCloud JPR directory... (this really shouldn't be necessary, JPR might not be configured correctly)"
        )
        VoiceMemoHandler._path.mkdir(parents=True, exist_ok=True)

    ## Whisper.cpp

    # Now, check that whisper.cpp is installed
    if not WHISPER_CPP.exists():
        typer.echo("Installing whisper.cpp...")
        subprocess.check_output(
            f"git clone git@github.com:ggerganov/whisper.cpp.git {WHISPER_CPP}",
            shell=True,
        )

    # Update it, because why not
    typer.echo("Updating whisper.cpp...")
    subprocess.check_output(f"cd {WHISPER_CPP} && git pull", shell=True)
    subprocess.check_output(
        f"cd {WHISPER_CPP} && ./models/download-ggml-model.sh base.en", shell=True
    )
    subprocess.check_output(f"cd {WHISPER_CPP} && make", shell=True)
