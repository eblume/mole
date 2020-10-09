# -*- coding: utf-8 -*-
"""This file contains tests that also serve as a small tutorial of funicular."""
import abc
from dataclasses import dataclass, field
from typing import List, Set, Type
from uuid import uuid4

import pytest

import funicular

###################
# Example program #
###################
# A small simulation, the details of which don't much matter


@dataclass
class Person:
    name: str
    age: int
    alive: bool = True
    interaction_history: List["InteractionRecord"] = field(default_factory=list)

    @classmethod
    def interact(cls, interaction: "Interaction") -> None:
        record = interaction.run()
        for person in interaction.group:
            person.interaction_history.append(record)


@dataclass
class Interaction(abc.ABC):
    group: Set[Person]

    def run(self, *args, **kwargs) -> "InteractionRecord":
        raise NotImplementedError("Base classes must define this method")


@dataclass(frozen=True)
class InteractionRecord:
    memo: str
    year: int
    interaction_type: Type[Interaction]
    people_names: Set[str]


class Talk(Interaction):
    def run(self, *args, **kwargs) -> InteractionRecord:
        return InteractionRecord(
            memo="These people spoke",
            year=kwargs.get("year", 0),
            interaction_type=self.__class__,
            people_names={p.name for p in self.group},
        )


class Play(Interaction):
    def run(self, *args, **kwargs) -> InteractionRecord:
        return InteractionRecord(
            memo="These people played",
            year=kwargs.get("year", 0),
            interaction_type=self.__class__,
            people_names={p.name for p in self.group},
        )


def run_simulation(initial_population: int, years: int):
    import random

    people = {Person(name=str(uuid4()), age=random.randint(0, 100)) for _ in range(initial_population)}

    for _ in range(years):
        interactions: List[Interaction] = []
        for person in people:
            if not person.alive:
                continue

            person.age += 1

            # TODO model death process more accurately? Stochastic variables?
            if person.age >= 100:
                person.alive = False
                continue

            # Pick a random interaction
            interaction: Type[Interaction] = random.choice(Interaction.__subclasses__())

            # Pick a random group of people
            group_size = random.randint(1, len(people) - 1)
            group = set(random.choices(list(people - {person}), k=group_size))

            # Record the interaction
            interactions.append(interaction(group))

        for this_interaction in interactions:
            Person.interact(this_interaction)


#########################################
# End example program (examples follow) #
#########################################


@pytest.fixture
def tree():
    return funicular.parse_object(run_simulation)


def example_get_called_classes(tree):
    # You can filter on instances of keywords, like 'class'
    classes = tree.keywords("class")

    # You can search for classes based on their name, as a string.
    # Keep in mind that funicular does not evaluate the AST, by default.
    # It is searching your code _as written_, not _as interpreted_.
    expected_classes = ["Person", "Interaction", "InteractionRecord", "Talk", "Play"]
    assert sorted(c.name for c in classes) == sorted(expected_classes)

    # But, you can ask funicular to evaluate that tree.
    record_types = [c.name == "InteractionRecord" for c in classes]
    assert len(record_types) == 1  # Just to prove there's only one found.
    compiled_class = record_types[0].compile()

    # The compiled class has the same behavior as a direct import
    example_args = ("foo", 2, Play, {})  # These are some example args for InteractionRecord
    assert compiled_class(*example_args) == InteractionRecord(*example_args)

    # In fact...
    assert compiled_class == InteractionRecord


def example_get_called_functions(tree):
    # You can filter by function names
    run_fns = tree.functions(name="run")

    # (This is the same as using the keyword 'def')
    assert run_fns == tree.keywords("def", label="run")

    # You can also query specifically for 'run' functions that are class methods
    run_methods = run_fns.filter(is_method=True)
    assert run_methods == run_fns  # (which in this case is the same group)

    # You can build a query object to do more complex queries.
    query = funicular.Query()

    # Beware that the `query` object is a Domain Specific Language that inspects
    # attribute access to build an internal representation of the query - these
    # aren't true assignments.
    query.type = funicular.Function  # Search for functions...
    query.statements.count = 1  # ... with only one statement
    query.statements[0] = funicular.Keyword("raise")  # ... which is a `raise`
    query.statements[0].arguments[0].name = "NotImplementedError"  # ... which is a NotImplementedError

    # With this query, we can find the one `run` method from Interaction.
    query_result = tree.filter(query)
    assert len(query_result) == 1  # Just to prove only one was found
    base_run = query_result[0]
    assert base_run == Interaction.run

    # You can also run this query based on an existing query result (such as a
    # filter). In this case, the two produce the same result, since the query is
    # already specific enough to capture the one method.
    assert tree.filter(query) == run_methods.filter(query)
