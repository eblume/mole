import os
import subprocess
import tempfile
from dataclasses import KW_ONLY, dataclass
from pathlib import Path
from typing import Iterable

import pendulum
import typer
from openai import OpenAI
from pydub import AudioSegment
from typerassistant import TyperAssistant
from typerassistant.spec import FunctionSpec
from watchdog.events import FileSystemEvent, FileSystemEventHandler

from mole.notebook import Logbook
from mole.secrets import get_secret

WHISPER_CPP = Path.home() / "code" / "3rd" / "whisper.cpp"


class VoiceMemoHandler(FileSystemEventHandler):
    """A handler for voice memo files."""

    _path = Path.home() / "Library" / "Mobile Documents" / "iCloud~com~openplanetsoftware~just-press-record/Documents"
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

    def on_created(self, event: FileSystemEvent):
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
    # - Create tasks in Todoist  # not currently implemented
    - Record the transcription in nb-cli and sync it.

    TODO:
    - Archive the audio.
    """
    # Example path: /Users/erichdblume/Library/Mobile Documents/iCloud~com~openplanetsoftware~just-press-record/Documents/2023-11-02/23-35-20.m4a
    when = pendulum.local(*map(int, path.parent.name.split("-")), *map(int, path.stem.split("-")))

    # Re-encode the audio to 16000Hz wav
    audio = AudioSegment.from_file(str(path))
    audio_16khz = audio.set_frame_rate(16000)

    # If the audio is over 60 seconds, truncate it to 60 seconds.
    # TODO this is a hack, we should really be using the streaming API for whisper.cpp (stream.cpp)
    if len(audio_16khz) > 60 * 1000:
        # This is necessary because occasionally my watch will start recording a voice memo that winds up being VERY
        # long (I had one over 30 hours long once), which causes all kinds of ruckus. A better fix is needed.
        typer.echo("Voice memo is over 60 seconds, truncating...")
        audio_16khz = audio_16khz[: 60 * 1000]

    with tempfile.NamedTemporaryFile(suffix=".wav", mode="wb") as wav:
        audio_16khz.export(wav.name, format="wav")
        transcription = (
            subprocess.check_output(f"cd {WHISPER_CPP} && ./main -nt -f {wav.name} 2>/dev/null", shell=True)
            .decode("utf-8")
            .strip()
        )
    cleaned = "\n".join([line.strip() for line in transcription.split("\n") if line.strip()])

    # Record the transcription in the daily journal
    logbook = Logbook(project=None)
    logbook.append_log(cleaned, preamble="JPR Memo", when=when)

    # Unlink the voice memo file now that it's logged -- this prevents costly infinite loops if the assistant fails,
    # although it also means if the assistant fails there's no easy retry.
    # TODO move all of this to some DAG like airflow or temporal.
    # TODO archive audio and transcription
    os.unlink(path)

    # Extract tasks from the transcription using GPT-4 and create them in Todoist
    # TODO this should become a new typerassistant API
    # TODO also look in to preserving threads across VMs, etc.
    from .cli import app

    client = OpenAI(api_key=get_secret("OpenAI", "credential", vault="blumeops"))
    assistant = VoiceMemoAssistant(app, client=client)
    print(assistant.ask(cleaned, use_commands=True, confirm_commands=False))


@dataclass
class VoiceMemoAssistant(TyperAssistant):
    """An assistant for voice memos."""

    _: KW_ONLY
    name: str = "Mole VoiceMemo Assistant"
    instructions: str = "Assistant scans voice memo transcriptions and, if applicable, creates todoist tasks from them."

    def functions(self) -> Iterable[FunctionSpec]:
        for function in super().functions():
            if function.name.split(".")[-1] == "todoist":
                yield function


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
        subprocess.check_output(f"git clone git@github.com:ggerganov/whisper.cpp.git {WHISPER_CPP}", shell=True)

    # Update it, because why not
    typer.echo("Updating whisper.cpp...")
    subprocess.check_output(f"cd {WHISPER_CPP} && git pull", shell=True)
    subprocess.check_output(f"cd {WHISPER_CPP} && ./models/download-ggml-model.sh base.en", shell=True)
    subprocess.check_output(f"cd {WHISPER_CPP} && make", shell=True)
