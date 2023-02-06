# -*- coding: utf-8 -*-
import datetime as dt

from .actions import Actions
from .remote import Remote
from .task import Task


class Session:
    def __init__(self, remote: Remote):
        self.remote = remote

    def determine_actions(self) -> Actions:
        # TODO replace all of this with a fun linear constraint declaritive syntax config
        today = dt.date.today()
        actions = Actions()
        todays_tasks = self.remote.get_tasks(date=today, name="Whack-a-Mole", completed=False)
        if len(todays_tasks) == 0:
            actions.create_task.append(Task(name="Whack-a-Mole", date=today, completed=False))
        return actions

    def resolve_actions(self, actions: Actions):
        for task in actions.create_task:
            self.remote.create_task(task)
