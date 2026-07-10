"""
Add Session.order: lets an admin control the display order of
workshops in the Workshops bloc on the public registration form
(the schedule/agenda still sorts by start time).

Follows the idempotent SeparateDatabaseAndState pattern established in
dashboard/migrations 0026+ and events/migrations 0017/0018/0034: this
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
    if 'order' not in columns:
        schema_editor.add_field(Session, Session._meta.get_field('order'))


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0035_userassignment_event_owner_role'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='session',
                    name='order',
                    field=models.IntegerField(
                        default=0,
                        help_text="Controls display order in the Workshops bloc on the public registration "
                                  "form only (the schedule/agenda still sorts by start time). Lower shows first.",
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_column, reverse_noop),
            ],
        ),
    ]
