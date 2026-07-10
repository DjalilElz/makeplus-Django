"""
Self-heal for prod migration-history gaps: some migrations were recorded
as applied without their dependencies also being recorded (historical
DB/migration-file drift), which trips Django's check_consistent_history()
and blocks every `migrate` call before it gets a chance to run anything --
including fixing itself.

This walks the full migration graph, finds every migration that's a
(transitive) dependency of an applied migration but isn't itself recorded
as applied, and applies exactly those migrations for real, one at a time
in dependency order, via MigrationExecutor.apply_migration() -- bypassing
only the history-consistency guard, not the migrations themselves. That's
safe here because this codebase's migrations of this kind are written
defensively (check-before-ALTER), so replaying one that already matches
the live schema is a no-op.

We deliberately avoid executor.migrate()/migration_plan(): those compute
"migrate this app to exactly migration X", and since some apps here
already have *later* migrations applied than the missing ones, that plan
mixes forwards and backwards migrations and Django refuses to run it
(InvalidMigrationPlan). Calling apply_migration() directly sidesteps that
entirely -- we're not resequencing anything, just filling in gaps.

Postgres-only. Safe to call repeatedly: no-ops once history is consistent.
"""


def _topological_order(graph, keys):
    keys = set(keys)
    ordered = []
    visited = set()

    def visit(key):
        if key in visited:
            return
        visited.add(key)
        node = graph.node_map.get(key)
        if node:
            for parent in node.parents:
                if parent in keys:
                    visit(parent)
        ordered.append(key)

    for key in keys:
        visit(key)
    return ordered


def fix_migration_history(dry_run=False, log=lambda msg: None):
    """Returns True if a fix was (or would be, in dry-run mode) applied."""
    from django.db import connection

    if connection.vendor != 'postgresql':
        return False

    from django.db.migrations.executor import MigrationExecutor

    executor = MigrationExecutor(connection)
    applied = set(executor.loader.applied_migrations.keys())

    missing = set()
    stack = list(applied)
    while stack:
        key = stack.pop()
        node = executor.loader.graph.node_map.get(key)
        if not node:
            continue
        for parent in node.parents:
            if parent not in applied and parent not in missing:
                missing.add(parent)
                stack.append(parent)

    if not missing:
        log('Migration history is consistent -- nothing to do.')
        return False

    ordered_keys = _topological_order(executor.loader.graph, missing)

    log(f'Found {len(ordered_keys)} unrecorded migration(s) that applied migrations depend on:')
    for key in ordered_keys:
        log(f'  - {key[0]}.{key[1]}')

    if dry_run:
        log('[DRY RUN] No changes made.')
        return True

    state = executor._create_project_state(with_applied_migrations=True)
    for key in ordered_keys:
        migration = executor.loader.graph.nodes[key]
        state = executor.apply_migration(state, migration, fake=False, fake_initial=False)
        log(f'Applied {key[0]}.{key[1]}')

    log('Migration history is now consistent.')
    return True
