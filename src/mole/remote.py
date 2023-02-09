# -*- coding: utf-8 -*-
from __future__ import annotations

import abc
import logging
from typing import Generic, Optional, Type, TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from .task import Task


# These TypeVars exist because I couldn't figure out a cleaner type-safe way to allow subtypes of Remote to specify
# their own configuration parameters (username, password, api key, IdP/SAML url, etc...). It is a bit messy if you're
# not familiar with typed python. Check out `Remote.from_config` to see it all glue together.
RemoteConfigT = TypeVar("RemoteConfigT", bound="RemoteConfig")
RemoteT = TypeVar("RemoteT", bound="Remote")


class RemoteConfig(abc.ABC):
    pass


class Remote(abc.ABC, Generic[RemoteConfigT]):
    """The abstract methods of this class define the common API for all remotes.

    Subclasses must provide a corresponding RemoteConfig subclass to provide things like remote credentials, secrets,
    and other configuration.
    """

    @classmethod
    @abc.abstractmethod
    def from_config(cls: Type[RemoteT], config: RemoteConfigT) -> RemoteT:
        raise NotImplemented

    @abc.abstractmethod
    def get_tasks(self, name: Optional[str] = None) -> list[Task]:
        raise NotImplemented

    @abc.abstractmethod
    def create_task(self, task: Task):
        raise NotImplemented

    @property
    def log(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)
