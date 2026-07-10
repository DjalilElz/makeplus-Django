"""
Self-heal for prod migration-history gaps: some migrations were recorded
as applied without their dependencies also being recorded (historical
DB/migration-file drift), which trips Django's check_consistent_history()
and blocks every `migrate` call before it gets a chance to run anything --
including fixing itself.

This walks the full migration graph, finds every migration that's a
(transitive) dependency of an applied migration but isn't itself recorded
as applied, and actually runs those migrations for real via
MigrationExecutor -- bypassing only the history-consistency guard, not
the migrations themselves. That's safe here because this codebase's
migrations of this kind are written defensively (check-before-ALTER), so
replaying one that already matches the live schema is a no-op.

Postgres-only. Safe to call repeatedly: no-ops once history is consistent.
"""


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

    targets = list(missing)
    plan = executor.migration_plan(targets)

    log(f'Found {len(plan)} unrecorded migration(s) that applied migrations depend on:')
    for migration, _backwards in plan:
        log(f'  - {migration.app_label}.{migration.name}')

    if dry_run:
        log('[DRY RUN] No changes made.')
        return True

    executor.migrate(targets, plan=plan)
    log('Applied the missing migrations. Migration history is now consistent.')
    return True
