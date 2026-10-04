from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Hand-written and guarded (IF NOT EXISTS raw SQL + SeparateDatabaseAndState),
    same reasoning as 0048/0049 -- this app's migration history has
    repeatedly lost its recorded-applied rows in production.

    Two changes:
    1. assigned_to M2M on ScientificContributionSubmission (plain
       'member' committee accounts only review submissions explicitly
       assigned to them).
    2. contribution_code's uniqueness moves from a single GLOBAL unique
       constraint to per-event -- needed so the new "P-<n>" auto-numbering
       (see eposter_set_status) can start at P-1 in every event without
       colliding with another event's P-1. Dynamically finds and drops
       whatever the existing global constraint is actually named (it
       predates this migration and its exact name isn't known here)
       before adding the new scoped one.
    """

    dependencies = [
        ('dashboard', '0049_participant_import_batch_and_row'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE TABLE IF NOT EXISTS dashboard_epostersubmission_assigned_to (
                        id BIGSERIAL PRIMARY KEY,
                        scientificcontributionsubmission_id UUID NOT NULL REFERENCES dashboard_epostersubmission(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
                        user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
                        CONSTRAINT dashboard_e_assigned_to_uniq UNIQUE (scientificcontributionsubmission_id, user_id)
                    );
                    CREATE INDEX IF NOT EXISTS dashboard_e_assigned_to_submission_idx ON dashboard_epostersubmission_assigned_to (scientificcontributionsubmission_id);
                    CREATE INDEX IF NOT EXISTS dashboard_e_assigned_to_user_idx ON dashboard_epostersubmission_assigned_to (user_id);
                    """,
                    reverse_sql="DROP TABLE IF EXISTS dashboard_epostersubmission_assigned_to CASCADE;",
                ),
                migrations.RunSQL(
                    sql="""
                    DO $$
                    DECLARE
                        old_constraint_name text;
                    BEGIN
                        SELECT tc.constraint_name INTO old_constraint_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu
                            ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                        WHERE tc.table_name = 'dashboard_epostersubmission'
                            AND tc.constraint_type = 'UNIQUE'
                            AND kcu.column_name = 'eposter_code'
                        LIMIT 1;

                        IF old_constraint_name IS NOT NULL THEN
                            EXECUTE format('ALTER TABLE dashboard_epostersubmission DROP CONSTRAINT %I', old_constraint_name);
                        END IF;
                    END $$;

                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint WHERE conname = 'dashboard_e_event_contribution_code_uniq'
                        ) THEN
                            ALTER TABLE dashboard_epostersubmission
                                ADD CONSTRAINT dashboard_e_event_contribution_code_uniq UNIQUE (event_id, eposter_code);
                        END IF;
                    END $$;
                    """,
                    reverse_sql="""
                    ALTER TABLE dashboard_epostersubmission DROP CONSTRAINT IF EXISTS dashboard_e_event_contribution_code_uniq;
                    """,
                ),
            ],
            state_operations=[
                # model_name is 'epostersubmission', not
                # 'scientificcontributionsubmission' -- the class was
                # renamed in Python source without a RenameModel
                # migration, so the migration graph's state still only
                # knows it by its original name (confirmed via
                # MigrationLoader; EPosterSubmission = alias in
                # models_eposter.py is the same underlying model).
                migrations.AddField(
                    model_name='epostersubmission',
                    name='assigned_to',
                    field=models.ManyToManyField(blank=True, help_text='Committee members this submission has been assigned to for review', related_name='assigned_contribution_submissions', to=settings.AUTH_USER_MODEL),
                ),
                migrations.AlterField(
                    model_name='epostersubmission',
                    name='contribution_code',
                    field=models.CharField(blank=True, db_column='eposter_code', max_length=50, null=True, verbose_name='Code de Contribution'),
                ),
                migrations.AddConstraint(
                    model_name='epostersubmission',
                    constraint=models.UniqueConstraint(fields=('event', 'contribution_code'), name='dashboard_e_event_contribution_code_uniq'),
                ),
            ],
        ),
    ]
