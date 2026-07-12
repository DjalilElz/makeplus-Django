"""
Add FormConfiguration.use_banner_image: a per-event toggle so the public
registration page can show the uploaded banner_image as the page header
instead of the default designed (gradient) header.

Follows the idempotent SeparateDatabaseAndState pattern established in
0026+: this production database has repeatedly lost its
django_migrations bookkeeping between deploys, so a plain AddField can
crash with "column already exists" on a re-run even though the column
is already correctly in place.
"""
from django.db import migrations, models


def add_column(apps, schema_editor):
    from dashboard.models_form import FormConfiguration

    table = 'dashboard_formconfiguration'
    with schema_editor.connection.cursor() as cursor:
        columns = {
            col.name for col in
            schema_editor.connection.introspection.get_table_description(cursor, table)
        }
    if 'use_banner_image' not in columns:
        schema_editor.add_field(FormConfiguration, FormConfiguration._meta.get_field('use_banner_image'))


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0036_registrationorder_caisse_transaction'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='formconfiguration',
                    name='use_banner_image',
                    field=models.BooleanField(default=False, help_text='Show the banner image at the top of the form instead of the default designed header.'),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_column, reverse_noop),
            ],
        ),
    ]
