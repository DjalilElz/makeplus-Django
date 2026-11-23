from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Guarded (ADD COLUMN IF NOT EXISTS) instead of plain AddFields:
    production has repeatedly lost rows from django_migrations, so this
    migration can be replayed against a database that already has the
    columns.
    """

    dependencies = [
        ('dashboard', '0063_attestation_include_eposter_details'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE dashboard_emailcampaign ADD COLUMN IF NOT EXISTS sheet_filename varchar(255) NOT NULL DEFAULT '';
                    ALTER TABLE dashboard_emailcampaign ADD COLUMN IF NOT EXISTS sheet_columns jsonb NOT NULL DEFAULT '[]'::jsonb;
                    ALTER TABLE dashboard_emailcampaign ADD COLUMN IF NOT EXISTS sheet_rows jsonb NOT NULL DEFAULT '[]'::jsonb;
                    ALTER TABLE dashboard_emailcampaign ADD COLUMN IF NOT EXISTS sheet_email_column varchar(100) NOT NULL DEFAULT '';
                    ALTER TABLE dashboard_emailrecipient ADD COLUMN IF NOT EXISTS data jsonb NOT NULL DEFAULT '{}'::jsonb;
                    """,
                    reverse_sql="""
                    ALTER TABLE dashboard_emailcampaign DROP COLUMN IF EXISTS sheet_filename;
                    ALTER TABLE dashboard_emailcampaign DROP COLUMN IF EXISTS sheet_columns;
                    ALTER TABLE dashboard_emailcampaign DROP COLUMN IF EXISTS sheet_rows;
                    ALTER TABLE dashboard_emailcampaign DROP COLUMN IF EXISTS sheet_email_column;
                    ALTER TABLE dashboard_emailrecipient DROP COLUMN IF EXISTS data;
                    """,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='emailcampaign',
                    name='sheet_filename',
                    field=models.CharField(blank=True, max_length=255),
                ),
                migrations.AddField(
                    model_name='emailcampaign',
                    name='sheet_columns',
                    field=models.JSONField(blank=True, default=list),
                ),
                migrations.AddField(
                    model_name='emailcampaign',
                    name='sheet_rows',
                    field=models.JSONField(blank=True, default=list),
                ),
                migrations.AddField(
                    model_name='emailcampaign',
                    name='sheet_email_column',
                    field=models.CharField(blank=True, max_length=100),
                ),
                migrations.AddField(
                    model_name='emailrecipient',
                    name='data',
                    field=models.JSONField(blank=True, default=dict),
                ),
            ],
        ),
    ]
