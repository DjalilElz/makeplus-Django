"""
Add PasswordResetVerification (self-service "mot de passe oublie" flow).

NOTE: This migration is hand-trimmed to contain ONLY the new
PasswordResetVerification model. `makemigrations` also wanted to bring in
a large pile of unrelated pre-existing drift (SignUpVerification,
FormRegistrationVerification, ControllerScan, ParticipantEventRegistration
and the ScientificContribution/EPoster rename in the dashboard app) that
was never captured in migration history for this app -- see the NOTE in
dashboard/migrations/0026_blocitem_eventblocconfig_reductionperiod_and_more.py
for the same pre-existing issue. That drift is intentionally excluded
here: it's unrelated to this change and risky to apply blind.

Also wrapped to be idempotent (check table existence before creating):
this production database has repeatedly lost its django_migrations
bookkeeping between deploys, which made a plain CreateModel crash with
"relation already exists" on a re-run even though the table was already
correctly in place.
"""
from django.db import migrations, models


def _table_names(schema_editor):
    with schema_editor.connection.cursor() as cursor:
        return set(schema_editor.connection.introspection.table_names(cursor))


def _index_names(schema_editor, table_name):
    """Database-agnostic index/constraint name lookup (works on Postgres and SQLite)."""
    with schema_editor.connection.cursor() as cursor:
        constraints = schema_editor.connection.introspection.get_constraints(cursor, table_name)
        return set(constraints.keys())


def create_password_reset_verification(apps, schema_editor):
    from events.models import PasswordResetVerification

    table = 'events_passwordresetverification'
    if table not in _table_names(schema_editor):
        schema_editor.create_model(PasswordResetVerification)
        return

    # Table already existed (bookkeeping desync re-run) -- create_model
    # would have added the Meta.indexes atomically with the table, but on
    # a re-run that never happens, so check them separately in case an
    # earlier attempt got the table but not the indexes.
    existing_indexes = _index_names(schema_editor, table)
    if 'events_pass_email_1a4f47_idx' not in existing_indexes:
        schema_editor.add_index(
            PasswordResetVerification,
            models.Index(fields=['email', 'is_used', '-created_at'], name='events_pass_email_1a4f47_idx'),
        )
    if 'events_pass_code_ha_d43854_idx' not in existing_indexes:
        schema_editor.add_index(
            PasswordResetVerification,
            models.Index(fields=['code_hash', 'is_used'], name='events_pass_code_ha_d43854_idx'),
        )
    if 'events_pass_expires_b656af_idx' not in existing_indexes:
        schema_editor.add_index(
            PasswordResetVerification,
            models.Index(fields=['expires_at', 'is_used'], name='events_pass_expires_b656af_idx'),
        )


def reverse_noop(apps, schema_editor):
    """No-op reverse: this is a resilience guard, not just a schema step."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0038_add_event_payment_link'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='PasswordResetVerification',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('email', models.EmailField(db_index=True, max_length=254)),
                        ('code_hash', models.CharField(db_index=True, max_length=64)),
                        ('new_password_hash', models.CharField(blank=True, max_length=255)),
                        ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                        ('expires_at', models.DateTimeField(db_index=True)),
                        ('is_used', models.BooleanField(default=False, db_index=True)),
                        ('used_at', models.DateTimeField(blank=True, null=True)),
                        ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                        ('user_agent', models.TextField(blank=True)),
                    ],
                    options={
                        'verbose_name': 'Password Reset Verification',
                        'verbose_name_plural': 'Password Reset Verifications',
                        'ordering': ['-created_at'],
                    },
                ),
                migrations.AddIndex(
                    model_name='passwordresetverification',
                    index=models.Index(fields=['email', 'is_used', '-created_at'], name='events_pass_email_1a4f47_idx'),
                ),
                migrations.AddIndex(
                    model_name='passwordresetverification',
                    index=models.Index(fields=['code_hash', 'is_used'], name='events_pass_code_ha_d43854_idx'),
                ),
                migrations.AddIndex(
                    model_name='passwordresetverification',
                    index=models.Index(fields=['expires_at', 'is_used'], name='events_pass_expires_b656af_idx'),
                ),
            ],
            database_operations=[
                migrations.RunPython(create_password_reset_verification, reverse_noop),
            ],
        ),
    ]
