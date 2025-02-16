import pytest
import os


@pytest.mark.skipif(
    os.getenv("INTEGRATION_MODE") != "true", reason="Integration mode not enabled"
)
def test_todoist_api():
    # Placeholder for integration test with Todoist API
    # Use the `op` CLI to fetch the API key and perform API calls
    pass
