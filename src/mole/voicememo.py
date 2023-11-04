from pathlib import Path
import time
import plistlib
import subprocess
import tempfile
import os

import typer
import pendulum
import openai
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from pydub import AudioSegment

from .todoist import create_task
from .notebook import add_log


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
    - Create tasks in Todoist
    - Record the transcription in nb-cli and sync it.

    TODO:
    - Archive the audio.
    """
    # Example path: /Users/erichdblume/Library/Mobile Documents/iCloud~com~openplanetsoftware~just-press-record/Documents/2023-11-02/23-35-20.m4a
    when = pendulum.local(*map(int, path.parent.name.split("-")), *map(int, path.stem.split("-")))

    # Re-encode the audio to 16000Hz wav
    audio = AudioSegment.from_file(str(path))
    audio_16khz = audio.set_frame_rate(16000)
    wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    audio_16khz.export(wav.name, format="wav")

    # Transcribe with whisper.cpp
    # typer.echo(f"Transcribing {path}...")
    transcription = (
        subprocess.check_output(f"cd {WHISPER_CPP} && ./main -nt -f {wav.name} 2>/dev/null", shell=True)
        .decode("utf-8")
        .strip()
    )
    cleaned = "\n".join([line.strip() for line in transcription.split("\n") if line.strip()])
    os.unlink(wav.name)

    # Extract tasks from transcription with GPT-4
    prompt = "Please extract any tasks from the following voice memo, one task per line. If there are no tasks, just say 'none'. Be concise, don't respond with any chatter, and reword the tasks for brevity and clarity as needed. Thanks!"

    # typer.echo(f"Extracting tasks from transcription for {path}...")
    response = openai.ChatCompletion.create(
        model="gpt-4", messages=[{"role": "system", "content": prompt}, {"role": "user", "content": cleaned}]
    )
    top_choice = response.choices[0]["message"]["content"]
    # gpt-4 sometimes capitalizes None, plus we want to strip out both whitespace AND any leading dashs from markdown
    # (so we are stripping out leading whitspace and dashes and empty lines)
    tasks = [
        line.strip().lstrip("-").strip()
        for line in top_choice.split("\n")
        if line.strip() and line.strip().lower() != "none"
    ]
    for task in tasks:
        create_task(task)

    # Record the transcription in nb-cli
    add_log(cleaned, subtitle="Voice Memo", when=when)

    # TODO archive
    os.unlink(path)


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
    # Yes, this one got away from me. TODO - modularize it.

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

    # Ensure Just Press Record is configured to save to iCloud
    try:
        # No idea why they use '-for-iOS' in the domain name, but that's what it is
        subprocess.check_output("defaults read com.openplanetsoftware.Just-Press-Record-for-iOS", shell=True)
    except subprocess.CalledProcessError:
        # If this doesn't exist yet, we will need to warn the user we are opening JPR and ask them to take a second
        # to configure it. We could maybe try and do this with plistlib ourselves but I don't actually know how
        # iCloud sync triggers work and I think it's better to just let the user do it once.
        typer.secho(
            "⚠️  Just Press Record hasn't been configured yet, it will now launch. You can then configure it, or quit it, or leave it.",
            fg=typer.colors.YELLOW,
        )
        subprocess.check_output("open -a 'Just Press Record'", shell=True)

        typer.secho(
            "⚠️  If accessibility is not enabled, the script will now ask you to enable it. Please do so.",
            fg=typer.colors.YELLOW,
        )
        typer.echo(
            "(This allows mole to send keyboard shortcuts to Just Press Record - if you don't like this, just configure JPR to save to iCloud manually and this will be skipped."
        )
        # PS I originally tried to do an inline compilation of a swift program to check AXIsProcessTrustedWithOptions,
        # and while this worked, it _also_ showed the permissions prompt (even though the result of that prompt did not
        # impede the script from working). So, we will just use osascript directly and warn the user ahead of time.

        # Try to background it using osascript
        subprocess.check_output(
            'osascript -e \'tell application "Just Press Record" to activate\' -e \'tell application "System Events" to keystroke "h" using {command down}\'',
            shell=True,
        )

        # Let's sleep for 5 seconds, just to let things settle in the OS a bit
        typer.secho("⏳  Waiting 5 seconds for Just Press Record to self-configure...", fg=typer.colors.YELLOW)
        time.sleep(5)

    # Now we can check if the defaults exists again, and if not, bail with an error.
    try:
        subprocess.check_output("defaults read com.openplanetsoftware.Just-Press-Record-for-iOS", shell=True)
    except subprocess.CalledProcessError:
        typer.secho(
            "❌  Just Press Record hasn't been configured yet, despite trying. Please file a bug report. Maybe try configuring it yourself?",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    # Now, configure it to save to iCloud (because we can)
    # (Create a temporary file, export the defaults to it, read it with plistlib, check the value, and if it's not 1, set it to 1)
    with tempfile.NamedTemporaryFile(mode="wb+") as f:
        subprocess.check_output(
            f"defaults export com.openplanetsoftware.Just-Press-Record-for-iOS {f.name}", shell=True
        )
        data = plistlib.load(Path(f.name).open("rb"))

    if "JPRDataStoreIndex" not in data or data["JPRDataStoreIndex"] != 1:
        typer.echo("Configuring Just Press Record to save to iCloud...")
        subprocess.check_output(
            "defaults write com.openplanetsoftware.Just-Press-Record-for-iOS JPRDataStoreIndex -int 1", shell=True
        )

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

    # Download the model
    subprocess.check_output(f"cd {WHISPER_CPP} && ./models/download-ggml-model.sh base.en", shell=True)

    # Build it
    subprocess.check_output(f"cd {WHISPER_CPP} && make", shell=True)

    ## Task Extraction (currently from GPT-4)
    # For this sanity check we just import openai and make sure the key is set, and set it from op if not
    if not openai.api_key or "OPENAI_API_KEY" not in os.environ:
        typer.echo("Setting OpenAI API key...")
        cred = subprocess.check_output("op item --vault blumeops get 'OpenAI' --fields credential", shell=True)
        openai.api_key = cred.decode("utf-8").strip()