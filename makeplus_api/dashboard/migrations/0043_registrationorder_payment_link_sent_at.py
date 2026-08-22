"""
Add RegistrationOrder.payment_link_sent_at (nullable DateTimeField): lets
the submissions page durably show "preinscription email already sent"
across reloads/future visits, instead of an in-memory confirmation that
vanishes the moment the modal closes -- set by
dashboard.views_event_owner.send_payment_link_email whenever it succeeds.

Follows the idempotent SeparateDatabaseAndState pattern established in
this app (0026+, 0033, 0034, 0036): this production database has
repeatedly lost its django_migrations bookkeeping between deploys, so a
plain AddField can crash with "column already exists" on a re-run even
though the column is already correctly in place.
"""
from django.db import migrations, models


def add_column(apps, schema_editor):
    from dashboard.models_blocs import RegistrationOrder

    table = 'dashboard_registrationorder'
    with schema_editor.connection.cursor() as cursor:
        columns = {
            col.name for col in
            schema_editor.connection.introspection.get_table_description(cursor, table)
        }
    if 'payment_link_sent_at' not in columns:
        schema_editor.add_field(RegistrationOrder, RegistrationOrder._meta.get_field('payment_link_sent_at'))


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0042_scientific_contribution_form_config'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='registrationorder',
                    name='payment_link_sent_at',
                    field=models.DateTimeField(blank=True, null=True),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_column, reverse_noop),
            ],
        ),
    ]
