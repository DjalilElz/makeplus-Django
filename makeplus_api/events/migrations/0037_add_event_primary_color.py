"""
Add Event.primary_color: lets an organizer set a hex brand color for their
event, used to theme the mobile app after login.

Follows the idempotent SeparateDatabaseAndState pattern established in
events/migrations 0017/0018/0034/0036: this production database has
repeatedly lost its django_migrations bookkeeping between deploys, so a
plain AddField can crash with "column already exists" on a re-run even
though the column is already correctly in place.
"""
from django.db import migrations, models


def add_column(apps, schema_editor):
    from events.models import Event

    table = 'events_event'
    with schema_editor.connection.cursor() as cursor:
        columns = {
            col.name for col in
            schema_editor.connection.introspection.get_table_description(cursor, table)
        }
    if 'primary_color' not in columns:
        schema_editor.add_field(Event, Event._meta.get_field('primary_color'))


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0036_session_order'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='event',
                    name='primary_color',
                    field=models.CharField(
                        max_length=7,
                        default='#9C27B0',
                        help_text="Hex color (e.g. #9C27B0) used to theme the mobile app for this event",
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_column, reverse_noop),
            ],
        ),
    ]
