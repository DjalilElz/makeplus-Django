from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0052_participantimportbatch_creation_total'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE dashboard_participantimportrow
                    ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMP WITH TIME ZONE NULL;
                    """,
                    reverse_sql="""
                    ALTER TABLE dashboard_participantimportrow
                    DROP COLUMN IF EXISTS claimed_at;
                    """,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='participantimportrow',
                    name='claimed_at',
                    field=models.DateTimeField(null=True, blank=True),
                ),
            ],
        ),
    ]
