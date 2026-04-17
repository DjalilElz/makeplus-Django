# Generated migration for verification models - Safe version

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0020_fix_emaillogincode_id_type'),
        ('dashboard', '0014_add_missing_formconfiguration_fields'),
    ]

    operations = [
        # Create SignUpVerification table if not exists
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS events_signupverification (
                id BIGSERIAL PRIMARY KEY,
                email VARCHAR(254) NOT NULL,
                code_hash VARCHAR(64) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                is_used BOOLEAN NOT NULL DEFAULT FALSE,
                used_at TIMESTAMP WITH TIME ZONE NULL,
                ip_address INET NULL,
                user_agent TEXT NOT NULL DEFAULT ''
            );
            
            CREATE INDEX IF NOT EXISTS events_sign_email_is_used_idx 
                ON events_signupverification (email, is_used, created_at DESC);
            CREATE INDEX IF NOT EXISTS events_sign_code_hash_idx 
                ON events_signupverification (code_hash, is_used);
            CREATE INDEX IF NOT EXISTS events_sign_expires_idx 
                ON events_signupverification (expires_at, is_used);
            CREATE INDEX IF NOT EXISTS events_signupverification_email_idx 
                ON events_signupverification (email);
            CREATE INDEX IF NOT EXISTS events_signupverification_code_hash_idx 
                ON events_signupverification (code_hash);
            CREATE INDEX IF NOT EXISTS events_signupverification_created_at_idx 
                ON events_signupverification (created_at);
            CREATE INDEX IF NOT EXISTS events_signupverification_expires_at_idx 
                ON events_signupverification (expires_at);
            CREATE INDEX IF NOT EXISTS events_signupverification_is_used_idx 
                ON events_signupverification (is_used);
            """,
            reverse_sql="DROP TABLE IF EXISTS events_signupverification CASCADE;"
        ),
        
        # Create FormRegistrationVerification table if not exists
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS events_formregistrationverification (
                id BIGSERIAL PRIMARY KEY,
                email VARCHAR(254) NOT NULL,
                code_hash VARCHAR(64) NOT NULL,
                form_data JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                is_used BOOLEAN NOT NULL DEFAULT FALSE,
                used_at TIMESTAMP WITH TIME ZONE NULL,
                ip_address INET NULL,
                user_agent TEXT NOT NULL DEFAULT '',
                form_id BIGINT NOT NULL REFERENCES dashboard_formconfiguration(id) ON DELETE CASCADE
            );
            
            CREATE INDEX IF NOT EXISTS events_form_email_form_idx 
                ON events_formregistrationverification (email, form_id, is_used, created_at DESC);
            CREATE INDEX IF NOT EXISTS events_form_code_hash_idx 
                ON events_formregistrationverification (code_hash, is_used);
            CREATE INDEX IF NOT EXISTS events_form_expires_idx 
                ON events_formregistrationverification (expires_at, is_used);
            CREATE INDEX IF NOT EXISTS events_formregistrationverification_email_idx 
                ON events_formregistrationverification (email);
            CREATE INDEX IF NOT EXISTS events_formregistrationverification_code_hash_idx 
                ON events_formregistrationverification (code_hash);
            CREATE INDEX IF NOT EXISTS events_formregistrationverification_created_at_idx 
                ON events_formregistrationverification (created_at);
            CREATE INDEX IF NOT EXISTS events_formregistrationverification_expires_at_idx 
                ON events_formregistrationverification (expires_at);
            CREATE INDEX IF NOT EXISTS events_formregistrationverification_is_used_idx 
                ON events_formregistrationverification (is_used);
            CREATE INDEX IF NOT EXISTS events_formregistrationverification_form_id_idx 
                ON events_formregistrationverification (form_id);
            """,
            reverse_sql="DROP TABLE IF EXISTS events_formregistrationverification CASCADE;"
        ),
    ]
