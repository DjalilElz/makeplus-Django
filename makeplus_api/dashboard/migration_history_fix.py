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

We deliberately avoid executor.migrate(): it computes "migrate this app
to exactly migration X", and since some apps here already have *later*
migrations applied than the missing ones, that plan mixes forwards and
backwards migrations and Django refuses to run it (InvalidMigrationPlan).
Calling apply_migration() directly for just the missing migrations
sidesteps that entirely -- we're not resequencing anything, just filling
in gaps. migration_plan(..., clean_start=True) is still used below, but
only to get the full graph in dependency order for building state
ourselves -- it never computes a from-current-state plan, so it doesn't
hit the same InvalidMigrationPlan issue.

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

    # executor._create_project_state(with_applied_migrations=True) can't be
    # used here: it walks the full graph from a clean start and replays
    # mutate_state() only for migrations Django considers applied --
    # skipping the ones we're about to backfill entirely. That's exactly
    # the inconsistency we're fixing (an applied migration whose own
    # dependency is one of these "missing" ones), so replaying only the
    # "applied" set builds a state where the missing migration's effect
    # (e.g. the model it created) was never added -- the next applied
    # migration that depends on it then crashes with a KeyError
    # (confirmed in production: AddField on a model whose CreateModel
    # migration was skipped this way). Walking the full plan ourselves and
    # handling "applied" (state only) and "missing" (real apply) in the
    # same pass keeps every migration's state mutation in correct
    # dependency order exactly once, however the two sets interleave.
    from django.db.migrations.state import ProjectState

    full_plan = executor.migration_plan(executor.loader.graph.leaf_nodes(), clean_start=True)
    applied_migrations = {
        executor.loader.graph.nodes[key] for key in applied if key in executor.loader.graph.nodes
    }
    missing_migrations = {executor.loader.graph.nodes[key] for key in missing}

    state = ProjectState(real_apps=executor.loader.unmigrated_apps)
    for migration, _ in full_plan:
        if migration in applied_migrations:
            migration.mutate_state(state, preserve=False)
        elif migration in missing_migrations:
            state = executor.apply_migration(state, migration, fake=False, fake_initial=False)
            log(f'Applied {migration.app_label}.{migration.name}')

    log('Migration history is now consistent.')
    return True
