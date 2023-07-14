import openai
from plumbum import local


def get_item(secret: str, *fields: str) -> str:
    return local["op"]["item"]["get"][secret]["--fields"][",".join(fields)]().strip()


def ensure_openai():
    """Ensures that openai has the proper credentials, or aborts"""
    if not openai.api_key:
        openai.api_key = get_item("OpenAI", "API Key")


def todoist_key() -> str:
    """Return the Todoist API key"""
    api_key = get_item("Todoist", "API Key")
    if api_key is None or len(api_key) != 40:
        raise ValueError("Invalid Todoist API Key found in OnePassword.")
    return api_key
