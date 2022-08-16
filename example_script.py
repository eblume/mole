# -*- coding: utf-8 -*-
from pathlib import Path
import re

from mole import Config

key_file = Path("todoist.key")
if not key_file.exists():
    raise ValueError("You must first create a file that contains your todoist API key")

key = key_file.read_text().strip()
if not re.match("[0-9a-f]{40}", key):
    raise ValueError(f"Invalid key found in {str(key_file)}")

config = Config(debug=True, verbose=True, api_key=key, remote="todoist")
