from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Guarded (ADD COLUMN IF NOT EXISTS) instead of a plain AddField:
    production has repeatedly lost rows from django_migrations, so this
    migration can be replayed against a database that already has the
    column -- a plain AddField would then fail and block the deploy.
    """

    dependencies = [
        ('dashboard', '0054_registrationorder_created_at_idx'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE dashboard_blocitem
                    ADD COLUMN IF NOT EXISTS show_on_public_form boolean NOT NULL DEFAULT true;
                    """,
                    reverse_sql="""
                    ALTER TABLE dashboard_blocitem DROP COLUMN IF EXISTS show_on_public_form;
                    """,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='blocitem',
                    name='show_on_public_form',
                    field=models.BooleanField(default=True),
                ),
            ],
        ),
    ]
