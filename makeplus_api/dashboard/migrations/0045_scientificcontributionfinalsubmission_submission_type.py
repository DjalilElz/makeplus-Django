from django.db import migrations, models


def backfill_submission_type(apps, schema_editor):
    """
    Existing final submissions all had an original_submission (standalone
    ones didn't exist before this feature) -- copy its type across so
    filtering by submission_type works for rows created before this field
    existed. Uses raw SQL (single UPDATE ... FROM) rather than looping in
    Python since this can touch every row in the table.
    """
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE dashboard_eposterfinalsubmission AS final
            SET submission_type = orig.type_participation
            FROM dashboard_epostersubmission AS orig
            WHERE final.original_submission_id = orig.id
              AND final.submission_type IS NULL
            """
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    """
    Hand-written, idempotent (see [[makeplus-migration-bookkeeping-desync]]
    memory / project CLAUDE.md notes): ADD COLUMN IF NOT EXISTS for the
    schema change, and the backfill only touches rows still missing the
    value, so re-running this migration is always safe.

    No state_operations here at all: ScientificContributionFinalSubmission
    (db_table dashboard_eposterfinalsubmission) isn't represented in the
    migration graph's model state under ANY name -- confirmed by
    inspecting the state as of 0044, where it's simply absent even
    though the real table has existed and been used (views_eposter_final,
    views_final_communications, etc.) all along. This is a deeper
    instance of the same eposter model-state drift documented in memory:
    not just renamed, entirely untracked. Adding a normal AddField state
    operation for it (under either the current or the old class name)
    raises KeyError since Django has no state entry to add the field to.
    The real table is unaffected by this -- Django's ORM at runtime reads
    models.py directly, not migration state -- so a database-only
    operation is correct and sufficient here.
    """

    dependencies = [
        ('dashboard', '0044_eventformconfiguration_require_contribution_number'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE dashboard_eposterfinalsubmission "
                        "ADD COLUMN IF NOT EXISTS submission_type varchar(30) NULL;"
                    ),
                    reverse_sql=(
                        "ALTER TABLE dashboard_eposterfinalsubmission "
                        "DROP COLUMN IF EXISTS submission_type;"
                    ),
                ),
            ],
        ),
        migrations.RunPython(backfill_submission_type, noop_reverse),
    ]
