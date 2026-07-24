"""
Rename service -> secteur on ScientificContributionSubmission (db_table
dashboard_epostersubmission).

Wrapped as idempotent RunPython (not a plain RenameField) because this
production database has repeatedly lost its django_migrations bookkeeping
between deploys (same recurring issue as migrations 0019 and 0026) --
a plain RenameField crashed with "column 'service' does not exist" on a
redeploy after this migration had already applied once. Checking column
existence first means a re-run is a safe no-op instead of a crash.
"""
from django.db import migrations, models


def _column_names(schema_editor, table_name):
    with schema_editor.connection.cursor() as cursor:
        return {
            col.name
            for col in schema_editor.connection.introspection.get_table_description(cursor, table_name)
        }


def rename_service_to_secteur(apps, schema_editor):
    columns = _column_names(schema_editor, 'dashboard_epostersubmission')
    if 'service' in columns and 'secteur' not in columns:
        with schema_editor.connection.cursor() as cursor:
            cursor.execute('ALTER TABLE dashboard_epostersubmission RENAME COLUMN service TO secteur')


def rename_secteur_to_service(apps, schema_editor):
    columns = _column_names(schema_editor, 'dashboard_epostersubmission')
    if 'secteur' in columns and 'service' not in columns:
        with schema_editor.connection.cursor() as cursor:
            cursor.execute('ALTER TABLE dashboard_epostersubmission RENAME COLUMN secteur TO service')


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0040_eventemailtemplate_payment_link_relabel'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RenameField(
                    model_name='epostersubmission',
                    old_name='service',
                    new_name='secteur',
                ),
                migrations.AlterField(
                    model_name='epostersubmission',
                    name='secteur',
                    field=models.CharField(
                        choices=[('public', 'Public'), ('prive', 'Privé')],
                        max_length=200,
                        verbose_name='Secteur',
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(rename_service_to_secteur, rename_secteur_to_service),
            ],
        ),
    ]
