This document is being used to brainstorm use cases for mole to guide development.

It assumes a Motion-based scheduling system as well as an associated calendar, and its outputs are new scheduled tasks
in Motion.

# Case 1: Whack-a-mole

Ensure that a task exists and is scheduled that just says "Complete me!". That's it. If it is completed, then the task
will not exist, so Mole must make a new one. Mole must never make two, however if the user makes two or more, Mole
should log the situation but take no action. (Mole does not delete tasks... yet.)

## Components

1. long-running executable
2. "live"/refreshing/async-sync/etc reaction to motion task state change
3. Simple declarative task language that does not require remote IDs for state comparison
4. Task creation based on declarative state delta.
5. Configuration system suitable for securely connecting to motion API


# Case 2: What's Next

Mole should print the next 3 scheduled tasks as debug output periodically. This is a placeholder for future entrypoints
that will query for this data.

## Components

As per case 1, plus...

1. Internal query API mechanism - interrogate state of declarative data
2. Potentially useful terminal output. Maybe create basic entrypoint script? `mole next`?
3. Anti-goal: IPC, shmem, RPC, etc. Internal API should be "internal", intended for use within a mole process.

A lema of 2 and 3: `mole next`, if created now, must run the mole remote query mechanism from within its own process and
terminate successfully on completion without looping continuously. This will be needed eventually, and should enforce
good code hygiene, but isn't strictly the point of this use case, so maybe best to leave it for later.

A quicker implementation would be to simply have the sync loop periodically debug-dump the next 3 motion tasks.

# Case 3: Email

Mole should connect to an email account and query if there are any emails in the inbox. If there are, Mole must create a
task to check email.


## Components

As per case 2, plus...

1. Email API: basic IMAP/POP/whatever queries needed for use case.
2. Extended configuration syntax suitable for connecting securely to email and calendar providers. (google first.)
3. Rate Limiting

# Case 4: Smart Email

As per case 3, except that Mole should not schedule this task more than N times a day (for configurable N, perhaps
expressed in minutes-assigned instead of count-of-tasks?). The exception to that exception is when an email exists
UNREAD in the inbox with HIGH PRIORITY, in which case the task should be scheduled regardless of N and with high
priority.


## Components

As per case 3, plus...


1. Linear constraint solver
2. Declarative task configuration syntax extended to include linear constraints (ordering, exclusion, etc.)
3. Motion API extended to support expression of solved linear constraints. (Possible need for labels, projects,
   dependencies, subtasks, etc.)
