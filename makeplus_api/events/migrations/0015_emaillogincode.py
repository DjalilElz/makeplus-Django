# Generated migration for EmailLoginCode model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


def create_emaillogincode_if_not_exists(apps, schema_editor):
    """Create EmailLoginCode table only if it doesn't exist"""
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'events_emaillogincode'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            # Table doesn't exist, create it
            schema_editor.create_model(apps.get_model('events', 'EmailLoginCode'))


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('events', '0014_alter_usereventassignment_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailLoginCode',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code_hash', models.CharField(db_index=True, max_length=64)),
                ('is_used', models.BooleanField(default=False, help_text='True if code has been used or invalidated')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='login_codes', to='events.event')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='login_codes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Email Login Code',
                'verbose_name_plural': 'Email Login Codes',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='emaillogincode',
            index=models.Index(fields=['user', 'event', 'is_used'], name='events_emai_user_id_b75a1f_idx'),
        ),
        migrations.AddIndex(
            model_name='emaillogincode',
            index=models.Index(fields=['code_hash'], name='events_emai_code_ha_idx'),
        ),
    ]
    
    # Override to handle existing table
    def apply(self, project_state, schema_editor, collect_sql=False):
        try:
            return super().apply(project_state, schema_editor, collect_sql)
        except Exception as e:
            if 'already exists' in str(e):
                # Table already exists, skip this migration
                return project_state
            raise
