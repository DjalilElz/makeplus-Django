"""
Add registration blocs / paid-registration models.

NOTE 1: This migration is hand-trimmed to contain ONLY the four new bloc
models (BlocItem, EventBlocConfig, ReductionPeriod, RegistrationOrder). The
autodetector also wanted to delete/recreate the ScientificContribution/EPoster
model family and touch EmailCampaign/EmailRecipient, because the dashboard
migration history never captured the ePoster -> ScientificContribution rename
(those models map to existing tables via db_table). Those operations are
intentionally excluded: they would be destructive on the production database
and are unrelated to this change.

NOTE 2: The actual schema operations are wrapped to be idempotent (check
existence before creating). This production database has repeatedly lost
its django_migrations bookkeeping for this app between deploys (root cause
not yet identified - not caused by anything in this codebase), which made a
plain CreateModel crash with "relation already exists" on every subsequent
deploy even though the tables/data were already correctly in place. Making
this migration idempotent means a re-run is a safe no-op instead of a
crash, regardless of why the bookkeeping went missing.
"""
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


def _table_names(schema_editor):
    with schema_editor.connection.cursor() as cursor:
        return set(schema_editor.connection.introspection.table_names(cursor))


def _index_names(schema_editor, table_name):
    """Database-agnostic index/constraint name lookup (works on Postgres and SQLite)."""
    with schema_editor.connection.cursor() as cursor:
        constraints = schema_editor.connection.introspection.get_constraints(cursor, table_name)
        return set(constraints.keys())


def create_blocs_schema(apps, schema_editor):
    """
    Idempotent forwards: only create tables/indexes that don't already exist.

    Uses the real, current model classes (not apps.get_model()) because
    RunPython inside SeparateDatabaseAndState only has access to the
    pre-migration historical state, which doesn't know about these models
    yet - that's exactly the state this migration is meant to create.
    Safe here since these models' fields haven't changed since this
    migration was authored.
    """
    from dashboard.models_blocs import BlocItem, EventBlocConfig, ReductionPeriod, RegistrationOrder

    existing_tables = _table_names(schema_editor)

    if 'dashboard_blocitem' not in existing_tables:
        schema_editor.create_model(BlocItem)
    if 'dashboard_eventblocconfig' not in existing_tables:
        schema_editor.create_model(EventBlocConfig)
    if 'dashboard_reductionperiod' not in existing_tables:
        schema_editor.create_model(ReductionPeriod)
    if 'dashboard_registrationorder' not in existing_tables:
        schema_editor.create_model(RegistrationOrder)

    blocitem_indexes = _index_names(schema_editor, 'dashboard_blocitem')
    if 'dashboard_b_event_i_c776f2_idx' not in blocitem_indexes:
        schema_editor.add_index(
            BlocItem,
            models.Index(fields=['event', 'bloc', 'is_active'], name='dashboard_b_event_i_c776f2_idx'),
        )

    order_indexes = _index_names(schema_editor, 'dashboard_registrationorder')
    if 'dashboard_r_event_i_57842e_idx' not in order_indexes:
        schema_editor.add_index(
            RegistrationOrder,
            models.Index(fields=['event', 'status', '-created_at'], name='dashboard_r_event_i_57842e_idx'),
        )
    if 'dashboard_r_email_7153db_idx' not in order_indexes:
        schema_editor.add_index(
            RegistrationOrder,
            models.Index(fields=['email'], name='dashboard_r_email_7153db_idx'),
        )


def reverse_noop(apps, schema_editor):
    """
    No-op reverse: this migration is a resilience guard as much as a
    schema-creation step, so reversing it should not drop tables that may
    hold real production data.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0025_drop_duplicate_contribution_number_column'),
        ('events', '0032_alter_exposantscan_notes'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='BlocItem',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('bloc', models.CharField(choices=[('status', 'Status'), ('restauration', 'Restauration'), ('social_event', 'Social Event')], max_length=20)),
                        ('name', models.CharField(max_length=200)),
                        ('price', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                        ('is_active', models.BooleanField(default=True)),
                        ('order', models.IntegerField(default=0)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bloc_items', to='events.event')),
                    ],
                    options={
                        'verbose_name': 'Bloc Item',
                        'verbose_name_plural': 'Bloc Items',
                        'ordering': ['bloc', 'order', 'name'],
                    },
                ),
                migrations.CreateModel(
                    name='EventBlocConfig',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('show_status', models.BooleanField(default=False)),
                        ('show_restauration', models.BooleanField(default=False)),
                        ('show_workshops', models.BooleanField(default=False)),
                        ('show_social_event', models.BooleanField(default=False)),
                        ('status_select_mode', models.CharField(choices=[('single', 'Single choice (radio)'), ('multiple', 'Multiple choice (checkbox)')], default='single', max_length=10)),
                        ('restauration_select_mode', models.CharField(choices=[('single', 'Single choice (radio)'), ('multiple', 'Multiple choice (checkbox)')], default='multiple', max_length=10)),
                        ('social_event_select_mode', models.CharField(choices=[('single', 'Single choice (radio)'), ('multiple', 'Multiple choice (checkbox)')], default='multiple', max_length=10)),
                        ('reduction_by_period_enabled', models.BooleanField(default=False)),
                        ('reduction_by_blocs_enabled', models.BooleanField(default=False)),
                        ('reduction_2_blocs', models.DecimalField(decimal_places=2, default=0, help_text='% off when items from 2 distinct blocs are selected', max_digits=5)),
                        ('reduction_3_blocs', models.DecimalField(decimal_places=2, default=0, help_text='% off when items from 3 distinct blocs are selected', max_digits=5)),
                        ('reduction_4_blocs', models.DecimalField(decimal_places=2, default=0, help_text='% off when items from 4 distinct blocs are selected', max_digits=5)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('event', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='bloc_config', to='events.event')),
                    ],
                    options={
                        'verbose_name': 'Event Bloc Configuration',
                        'verbose_name_plural': 'Event Bloc Configurations',
                    },
                ),
                migrations.CreateModel(
                    name='ReductionPeriod',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('name', models.CharField(blank=True, help_text="Optional label, e.g. 'Early bird'", max_length=100)),
                        ('start_date', models.DateField()),
                        ('end_date', models.DateField()),
                        ('discount_percent', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reduction_periods', to='events.event')),
                    ],
                    options={
                        'verbose_name': 'Reduction Period',
                        'verbose_name_plural': 'Reduction Periods',
                        'ordering': ['start_date'],
                    },
                ),
                migrations.CreateModel(
                    name='RegistrationOrder',
                    fields=[
                        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ('full_name', models.CharField(blank=True, max_length=255)),
                        ('email', models.EmailField(blank=True, max_length=254)),
                        ('items_snapshot', models.JSONField(blank=True, default=list)),
                        ('subtotals', models.JSONField(blank=True, default=dict)),
                        ('distinct_blocs_count', models.IntegerField(default=0)),
                        ('total_before_reduction', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                        ('period_discount_percent', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                        ('blocs_discount_percent', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                        ('total_discount_percent', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                        ('total_after_reduction', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                        ('receipt_file', models.FileField(upload_to='registrations/receipts/')),
                        ('status', models.CharField(choices=[('pending', 'Pending Review'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                        ('admin_notes', models.TextField(blank=True)),
                        ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                        ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                        ('user_agent', models.TextField(blank=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registration_orders', to='events.event')),
                        ('form_submission', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='registration_orders', to='dashboard.formsubmission')),
                        ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_registration_orders', to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'verbose_name': 'Registration Order',
                        'verbose_name_plural': 'Registration Orders',
                        'ordering': ['-created_at'],
                    },
                ),
                migrations.AddIndex(
                    model_name='blocitem',
                    index=models.Index(fields=['event', 'bloc', 'is_active'], name='dashboard_b_event_i_c776f2_idx'),
                ),
                migrations.AddIndex(
                    model_name='registrationorder',
                    index=models.Index(fields=['event', 'status', '-created_at'], name='dashboard_r_event_i_57842e_idx'),
                ),
                migrations.AddIndex(
                    model_name='registrationorder',
                    index=models.Index(fields=['email'], name='dashboard_r_email_7153db_idx'),
                ),
            ],
            database_operations=[
                migrations.RunPython(create_blocs_schema, reverse_noop),
            ],
        ),
    ]
