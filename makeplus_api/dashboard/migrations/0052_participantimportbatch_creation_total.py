from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0051_participantimportrow_confirmation_email_sent'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE dashboard_participantimportbatch
                    ADD COLUMN IF NOT EXISTS creation_total INTEGER NULL;
                    """,
                    reverse_sql="""
                    ALTER TABLE dashboard_participantimportbatch
                    DROP COLUMN IF EXISTS creation_total;
                    """,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='participantimportbatch',
                    name='creation_total',
                    field=models.IntegerField(null=True, blank=True),
                ),
            ],
        ),
    ]
