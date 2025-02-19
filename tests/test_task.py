from mole.task import Task, ChoreDefinition
from mole.chores import update_chores


def test_create_and_complete_task(db_connection):
    # Create a new task with a name
    task = Task(name="Test Task")
    task.save(db_connection)

    # Retrieve the task and check its initial state
    retrieved_task = Task.get(db_connection, task.id)
    assert retrieved_task is not None
    assert retrieved_task.name == "Test Task"
    assert not retrieved_task.completed

    # Complete the task
    retrieved_task.complete(db_connection)

    # Retrieve the task again and check its state
    completed_task = Task.get(db_connection, task.id)
    assert completed_task is not None
    assert completed_task.name == "Test Task"
    assert completed_task.completed


def test_update_chores_creates_new_tasks(db_connection):
    # Example fixture data for chores
    chore_definitions = [
        ChoreDefinition(name="Weekly Chore", interval_days=7),
        ChoreDefinition(name="Biweekly Chore", interval_days=14),
    ]

    # Simulate chore completions
    db_connection.execute("""
        CREATE TABLE chore_completions (
            chore_name TEXT PRIMARY KEY,
            last_completed DATE
        )
    """)
    db_connection.execute("""
        INSERT INTO chore_completions (chore_name, last_completed) VALUES
        ('Weekly Chore', DATE('now', '-8 days')),
        ('Biweekly Chore', DATE('now', '-15 days'))
    """)

    # Call update_chores and check if new tasks are created
    update_chores(db_connection, chore_definitions)

    # Verify that new tasks are created for due chores
    tasks = db_connection.execute("SELECT name FROM tasks").fetchall()
    task_names = [task[0] for task in tasks]
    assert "Weekly Chore" in task_names
    assert "Biweekly Chore" in task_names


def test_update_chores_no_new_tasks(db_connection):
    # Example fixture data for chores
    chore_definitions = [
        ChoreDefinition(name="Weekly Chore", interval_days=7),
        ChoreDefinition(name="Biweekly Chore", interval_days=14),
    ]

    # Simulate chore completions
    db_connection.execute("""
        CREATE TABLE chore_completions (
            chore_name TEXT PRIMARY KEY,
            last_completed DATE
        )
    """)
    db_connection.execute("""
        INSERT INTO chore_completions (chore_name, last_completed) VALUES
        ('Weekly Chore', DATE('now', '-6 days')),
        ('Biweekly Chore', DATE('now', '-13 days'))
    """)

    # Call update_chores and check if no new tasks are created
    update_chores(db_connection, chore_definitions)

    # Verify that no new tasks are created for chores not due
    tasks = db_connection.execute("SELECT name FROM tasks").fetchall()
    assert len(tasks) == 0
