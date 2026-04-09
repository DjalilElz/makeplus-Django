# Generated migration for EmailLoginCode model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


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
            index=models.Index(fields=['user', 'event', 'is_used'], name='events_emai_user_id_idx'),
        ),
        migrations.AddIndex(
            model_name='emaillogincode',
            index=models.Index(fields=['code_hash'], name='events_emai_code_ha_idx'),
        ),
    ]
