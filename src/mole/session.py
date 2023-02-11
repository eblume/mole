# -*- coding: utf-8 -*-
import logging

from .actions import Actions
from .remote import Remote
from .task import Task


class Session:
    def __init__(self, remote: Remote):
        self.remote = remote

    @property
    def log(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)

    def determine_actions(self) -> Actions:
        # TODO replace all of this with a fun linear constraint declaritive syntax config
        actions = Actions()
        todays_tasks = self.remote.get_tasks()
        wams = [t for t in todays_tasks if t.name == "Whack-a-Mole" and t.completed == False]
        if len(wams) == 0:
            actions.create_task.append(Task(name="Whack-a-Mole", completed=False))
        self.log.debug("Detected %d actions", len(actions))
        return actions

    def resolve_actions(self, actions: Actions):
        for task in actions.create_task:
            self.log.debug("Doing action: %s", task.name)
            self.remote.create_task(task)
