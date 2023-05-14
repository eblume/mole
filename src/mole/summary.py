from __future__ import annotations

from .todoist import TodoistRemote

import textwrap

import openai
import json


MAX_TOKENS = 8096  # gpt-4 limit


def get_summary(temperature: float, extra_prompt: str) -> str:
    """Summarize the day using an LLM"""
    remote = TodoistRemote()
    on_deck_tasks = remote.get_tasks(filter="today | overdue")
    state = {
        "on_deck_task_keys": ['content', 'due', 'priority', 'project'],  # defined here to hint for AI
        "on_deck_tasks": [
            (
                textwrap.shorten(task.name, width=50, placeholder="..."),
                task.due.date if task.due is not None else None,  # note, dropping time info, TODO
                task.priority,
                remote.project_id_map[task.project_id] if task.project_id is not None else None
            )

            for task in on_deck_tasks if task.priority != 3
        ],
    }
    json_state = json.dumps(state, separators=(',', ':'))
    messages = [
        { 'role': 'system', 'content': "Assistant, summarize Erich's day using Todoist data. Provide a brief list of details and a couple of suggestions in a relaxed, informal tone." },
        { 'role': 'user', 'content': textwrap.shorten(json_state, width=MAX_TOKENS - 1000, placeholder="...") },
    ]

    if extra_prompt:
        messages.append({ 'role': 'user', 'content': extra_prompt })

    response = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=temperature,
        max_tokens=MAX_TOKENS - 3000,
        messages=messages,
    )

    return response['choices'][0]['message']['content'].strip()  # type: ignore
