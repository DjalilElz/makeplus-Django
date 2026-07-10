"""
Add Session.is_active: lets an admin temporarily hide a paid session
(workshop) from the public registration form without deleting it.

Follows the idempotent SeparateDatabaseAndState pattern established in
dashboard/migrations 0026+ and events/migrations 0017/0018: this
production database has repeatedly lost its django_migrations
bookkeeping between deploys, so a plain AddField can crash with
"column already exists" on a re-run even though the column is already
correctly in place.
"""
from django.db import migrations, models


def add_column(apps, schema_editor):
    from events.models import Session

    table = 'events_session'
    with schema_editor.connection.cursor() as cursor:
        columns = {
            col.name for col in
            schema_editor.connection.introspection.get_table_description(cursor, table)
        }
    if 'is_active' not in columns:
        schema_editor.add_field(Session, Session._meta.get_field('is_active'))


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0033_unique_user_email'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='session',
                    name='is_active',
                    field=models.BooleanField(
                        default=True,
                        help_text="Uncheck to temporarily hide this session from the public registration form "
                                  "(e.g. speaker not confirmed yet) without deleting it. Admin views are unaffected.",
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_column, reverse_noop),
            ],
        ),
    ]
