# Manual migration to increase template_type field length
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0020_make_genre_optional'),
    ]

    operations = [
        migrations.RunSQL(
            # PostgreSQL - increase varchar length for template_type field
            sql="ALTER TABLE dashboard_eposteremailtemplate ALTER COLUMN template_type TYPE VARCHAR(35);",
            reverse_sql="ALTER TABLE dashboard_eposteremailtemplate ALTER COLUMN template_type TYPE VARCHAR(30);",
        ),
    ]
