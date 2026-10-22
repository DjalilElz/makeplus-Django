# Generated migration to change Participant.qr_code_data from TextField to JSONField
#
# Rewritten guarded: production's django_migrations bookkeeping has
# repeatedly lost its recorded-applied rows (see this app's other
# hand-written migrations for the same fix), which turned this
# originally plain AlterField into a genuine re-run on a column that
# was already converted long ago. ALTER COLUMN TYPE jsonb USING ...
# forces Postgres to scan/rewrite every row even when the type already
# matches -- on this table that's slow enough to exceed Supabase's
# statement_timeout and fail the whole deploy. Skipping entirely when
# the column is already jsonb makes the re-run an actual no-op.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0029_convert_qr_code_data_to_json'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    DO $$
                    BEGIN
                        IF (
                            SELECT data_type FROM information_schema.columns
                            WHERE table_name = 'events_participant' AND column_name = 'qr_code_data'
                        ) != 'jsonb' THEN
                            -- 0029 normalized every non-empty value to valid JSON
                            -- text, but rows it skipped (NULL/empty) or a row whose
                            -- fallback UPDATE also failed could still hold something
                            -- the ::jsonb cast below would choke on -- clear those
                            -- first so the cast can't fail partway through.
                            UPDATE events_participant
                            SET qr_code_data = '{}'
                            WHERE qr_code_data IS NULL OR qr_code_data = '';

                            ALTER TABLE events_participant
                            ALTER COLUMN qr_code_data TYPE jsonb USING qr_code_data::jsonb;

                            ALTER TABLE events_participant
                            ALTER COLUMN qr_code_data SET DEFAULT '{}'::jsonb;
                        END IF;
                    END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name='participant',
                    name='qr_code_data',
                    field=models.JSONField(default=dict, blank=True, help_text='QR code content as JSON'),
                ),
            ],
        ),
    ]
