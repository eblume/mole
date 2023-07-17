import textwrap

from plumbum import local


def get_lyrics():
    """Get lyrics for the current song using the Music.app applescript interface"""
    osascript = local["osascript"]

    lyrics_script = """
    tell application "Music"
        if player state is playing then
            set current_track to current track
            return lyrics of current_track
        else
            return "No song playing"
        end if
    end tell
    """
    name_script = 'tell application "Music" to get name of current track'
    artist_script = 'tell application "Music" to get artist of current track'

    lyrics = osascript("-e", lyrics_script).strip()
    if not lyrics:
        return "No lyrics found or Music.app applescript bridge is broken"

    name = osascript("-e", name_script).strip()
    artist = osascript("-e", artist_script).strip()


    return textwrap.dedent(f"""
        Lyrics for {name} by {artist}:
        {lyrics}
    """)
