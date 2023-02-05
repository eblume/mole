# -*- coding: utf-8 -*-
from dataclasses import dataclass
import datetime as dt


@dataclass
class Task:
    name: str
    completed: bool
    date: dt.date
