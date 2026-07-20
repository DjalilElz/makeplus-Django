"""
Add Event.payment_link: an optional URL an organizer can set so the
submissions page can email participants a standard "here's your payment
link" message.

Follows the idempotent SeparateDatabaseAndState pattern established in
events/migrations 0017/0018/0034/0036/0037: this production database has
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
    if 'payment_link' not in columns:
        schema_editor.add_field(Event, Event._meta.get_field('payment_link'))


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0037_add_event_primary_color'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='event',
                    name='payment_link',
                    field=models.URLField(
                        blank=True,
                        null=True,
                        help_text="Optional payment/invoice link sent to participants from the submissions page",
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_column, reverse_noop),
            ],
        ),
    ]
