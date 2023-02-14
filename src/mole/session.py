# -*- coding: utf-8 -*-
import logging

from .actions import Actions
from .remote import Remote
from .slate import SlateTaskStatus, SolvedSlate
from .task import Task


class Session:
    def __init__(self, remote: Remote):
        self.remote = remote

    @property
    def log(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)

    def determine_actions(self, slate: SolvedSlate) -> Actions:
        actions = Actions()
        current_tasks = self.remote.get_tasks()

        for task, status in slate.compare(current_tasks):
            if status == SlateTaskStatus.unknown:
                logging.warn("Unknown task: %s", task.name)

            # TODO we need much more specificity beyond created/deleted/unknown
            # but this will need to come when I understand more about what is needed
            if status == SlateTaskStatus.created:
                actions.create_task.append(task)
            else:
                actions.delete_task.append(task)

        self.log.debug("Create tasks: %d", len(actions.create_task))
        self.log.debug("Delete tasks: %d", len(actions.delete_task))
        self.log.debug("All tasks: %d", len(actions))
        return actions

    def resolve_actions(self, actions: Actions):
        for task in actions.create_task:
            self.log.debug("Creating Task: %s", task.name)
            self.remote.create_task(task)
