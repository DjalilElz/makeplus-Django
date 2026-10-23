# Generated migration to convert qr_code_data from string to JSON

from django.db import migrations, transaction
import json
import ast


def _to_json_string(qr_code_data, participant_id):
    try:
        # Try to parse as Python literal (dict with single quotes)
        data_dict = ast.literal_eval(qr_code_data)
        return json.dumps(data_dict)
    except (ValueError, SyntaxError):
        # If it's already valid JSON, leave it
        try:
            json.loads(qr_code_data)
            return qr_code_data  # Already valid JSON
        except json.JSONDecodeError:
            print(f"Warning: Invalid qr_code_data for participant {participant_id}, resetting to empty dict")
            return json.dumps({})


def convert_qr_code_data_to_json(apps, schema_editor):
    """
    Convert existing qr_code_data from string/dict to valid JSON.

    Each row's UPDATE runs inside its own savepoint (transaction.atomic()).
    Postgres aborts the ENTIRE surrounding transaction the instant any one
    statement fails, and refuses every statement after that -- including a
    "fallback" UPDATE -- until a ROLLBACK happens. The original version of
    this migration had no savepoint, so one bad row's failure took its own
    fallback UPDATE down with it and crashed the whole migration (and
    therefore the whole deploy). Wrapping each row -- primary attempt AND
    fallback -- in its own savepoint means a single bad row can never
    take down anything beyond itself.
    """
    db_alias = schema_editor.connection.alias

    with schema_editor.connection.cursor() as cursor:
        # 0030 (which depends on this migration) converts the column to a
        # real jsonb type -- guarded by checking it isn't jsonb already.
        # If that already succeeded, every row's value is GUARANTEED
        # valid JSON by Postgres's own jsonb type enforcement (0030's
        # own ALTER COLUMN ... USING qr_code_data::jsonb would have
        # failed outright on any row that wasn't). This migration's
        # entire job is then provably already done, so there's nothing
        # left to scan or fix -- skip immediately rather than walking
        # every row with an individual UPDATE (which is what made
        # replaying this migration, when production's django_migrations
        # bookkeeping lost its applied-record for it, repeatedly time out
        # and get blocked by lock contention once the table had grown to
        # thousands of rows under live traffic).
        cursor.execute(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_name = 'events_participant' AND column_name = 'qr_code_data'"
        )
        row = cursor.fetchone()
        if row and row[0] == 'jsonb':
            return

        # Get all participants with their qr_code_data
        # Cast to text explicitly to avoid JSON parsing in WHERE clause
        cursor.execute(
            "SELECT id, qr_code_data::text FROM events_participant WHERE qr_code_data::text IS NOT NULL AND qr_code_data::text != ''"
        )
        rows = cursor.fetchall()

    for participant_id, qr_code_data in rows:
        if not qr_code_data:
            continue
        try:
            with transaction.atomic(using=db_alias):
                json_string = _to_json_string(qr_code_data, participant_id)
                with schema_editor.connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE events_participant SET qr_code_data = %s WHERE id = %s",
                        [json_string, participant_id]
                    )
        except Exception as e:
            print(f"Error converting qr_code_data for participant {participant_id}: {e} -- resetting to empty dict")
            try:
                with transaction.atomic(using=db_alias):
                    with schema_editor.connection.cursor() as cursor:
                        cursor.execute(
                            "UPDATE events_participant SET qr_code_data = %s WHERE id = %s",
                            [json.dumps({}), participant_id]
                        )
            except Exception as e2:
                print(f"Also failed to reset qr_code_data for participant {participant_id}: {e2} -- leaving value as-is")


def reverse_conversion(apps, schema_editor):
    """Reverse migration - no action needed"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0025_restructure_participant_model'),
    ]

    operations = [
        migrations.RunPython(convert_qr_code_data_to_json, reverse_conversion),
    ]
