import os
from jira import JIRA, Issue


API_KEY = os.getenv('JIRA_APPLICATION_KEY')
URL = os.getenv('JIRA_SERVER_URL')


def get_my_issues() -> dict[str, str]:
    assert URL
    assert API_KEY

    jira = JIRA(server=URL, token_auth=API_KEY) 
    issues = jira.search_issues('assignee = currentUser()')

    # Why does mypy think issues can be strs? search_issues may need checking. TODO
    return {issue.key: issue.fields.summary for issue in issues if isinstance(issue, Issue)}
