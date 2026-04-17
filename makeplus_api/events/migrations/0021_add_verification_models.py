# Generated migration for verification models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0020_fix_emaillogincode_id_type'),
        ('dashboard', '0014_add_missing_formconfiguration_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='SignUpVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(db_index=True, max_length=254)),
                ('code_hash', models.CharField(db_index=True, max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('expires_at', models.DateTimeField(db_index=True)),
                ('is_used', models.BooleanField(db_index=True, default=False)),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Sign Up Verification',
                'verbose_name_plural': 'Sign Up Verifications',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='FormRegistrationVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(db_index=True, max_length=254)),
                ('code_hash', models.CharField(db_index=True, max_length=64)),
                ('form_data', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('expires_at', models.DateTimeField(db_index=True)),
                ('is_used', models.BooleanField(db_index=True, default=False)),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('form', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='verifications', to='dashboard.formconfiguration')),
            ],
            options={
                'verbose_name': 'Form Registration Verification',
                'verbose_name_plural': 'Form Registration Verifications',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='signupverification',
            index=models.Index(fields=['email', 'is_used', '-created_at'], name='events_sign_email_is_used_idx'),
        ),
        migrations.AddIndex(
            model_name='signupverification',
            index=models.Index(fields=['code_hash', 'is_used'], name='events_sign_code_hash_idx'),
        ),
        migrations.AddIndex(
            model_name='signupverification',
            index=models.Index(fields=['expires_at', 'is_used'], name='events_sign_expires_idx'),
        ),
        migrations.AddIndex(
            model_name='formregistrationverification',
            index=models.Index(fields=['email', 'form', 'is_used', '-created_at'], name='events_form_email_form_idx'),
        ),
        migrations.AddIndex(
            model_name='formregistrationverification',
            index=models.Index(fields=['code_hash', 'is_used'], name='events_form_code_hash_idx'),
        ),
        migrations.AddIndex(
            model_name='formregistrationverification',
            index=models.Index(fields=['expires_at', 'is_used'], name='events_form_expires_idx'),
        ),
    ]
