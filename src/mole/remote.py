# -*- coding: utf-8 -*-
import abc
import logging


class SyncClient(abc.ABC):
    @abc.abstractmethod
    async def run(self) -> None:
        raise NotImplementedError

    @property
    def log(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)
