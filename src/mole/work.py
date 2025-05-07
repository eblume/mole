from mole.task import ChoreDefinition


def work(chores: list[ChoreDefinition] | None = None) -> None:
    for chore in chores or []:
        print(chore.name)
    print("All Done!")
