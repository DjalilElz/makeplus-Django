"""
Add per-event scientific-contribution submission form settings to
EventFormConfiguration: which of the 4 contribution types (E-Poster,
Communication Orale, Table Ronde, Atelier) are enabled, and whether the
"Thème" field is free text or an admin-defined dropdown.

Wrapped as idempotent add-if-missing (not plain AddField) for the same
reason as migration 0041: this production database has repeatedly lost
its django_migrations bookkeeping between deploys, so a redeploy that
re-runs this migration must be a safe no-op instead of crashing on
"column already exists".
"""
from django.db import migrations, models


NEW_FIELDS = [
    ('enable_e_poster', models.BooleanField(default=True, verbose_name='E-Poster activé')),
    ('enable_communication_orale', models.BooleanField(default=True, verbose_name='Communication Orale activée')),
    ('enable_table_ronde', models.BooleanField(default=True, verbose_name='Table Ronde activée')),
    ('enable_atelier', models.BooleanField(default=True, verbose_name='Atelier activé')),
    (
        'theme_field_mode',
        models.CharField(
            choices=[('free_text', 'Texte libre'), ('select', 'Liste déroulante')],
            default='free_text',
            max_length=20,
            verbose_name='Mode du champ Thème',
        ),
    ),
    (
        'theme_options',
        models.JSONField(
            blank=True,
            default=list,
            help_text="Liste des thèmes proposés quand le mode est 'Liste déroulante'",
            verbose_name='Options du thème (si liste déroulante)',
        ),
    ),
]


def _column_names(schema_editor, table_name):
    with schema_editor.connection.cursor() as cursor:
        return {
            col.name
            for col in schema_editor.connection.introspection.get_table_description(cursor, table_name)
        }


def add_missing_columns(apps, schema_editor):
    EventFormConfiguration = apps.get_model('dashboard', 'EventFormConfiguration')
    existing = _column_names(schema_editor, 'dashboard_eventformconfiguration')
    for name, field in NEW_FIELDS:
        if name not in existing:
            field.set_attributes_from_name(name)
            schema_editor.add_field(EventFormConfiguration, field)


def remove_added_columns(apps, schema_editor):
    EventFormConfiguration = apps.get_model('dashboard', 'EventFormConfiguration')
    existing = _column_names(schema_editor, 'dashboard_eventformconfiguration')
    for name, field in NEW_FIELDS:
        if name in existing:
            field.set_attributes_from_name(name)
            schema_editor.remove_field(EventFormConfiguration, field)


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0041_rename_service_to_secteur'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='eventformconfiguration',
                    name=name,
                    field=field,
                )
                for name, field in NEW_FIELDS
            ],
            database_operations=[
                migrations.RunPython(add_missing_columns, remove_added_columns),
            ],
        ),
    ]
