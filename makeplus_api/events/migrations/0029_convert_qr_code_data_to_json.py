# Generated migration to convert qr_code_data from string to JSON

from django.db import migrations
import json


def convert_qr_code_data_to_json(apps, schema_editor):
    """Convert existing qr_code_data from string/dict to valid JSON"""
    # Use raw SQL to avoid model field issues
    db_alias = schema_editor.connection.alias
    
    with schema_editor.connection.cursor() as cursor:
        # Get all participants with their qr_code_data
        cursor.execute(
            "SELECT id, qr_code_data FROM events_participant WHERE qr_code_data IS NOT NULL AND qr_code_data != ''"
        )
        
        rows = cursor.fetchall()
        
        for participant_id, qr_code_data in rows:
            if qr_code_data:
                try:
                    # Try to parse as Python literal (dict with single quotes)
                    import ast
                    try:
                        data_dict = ast.literal_eval(qr_code_data)
                        # Convert to valid JSON string
                        json_string = json.dumps(data_dict)
                    except (ValueError, SyntaxError):
                        # If it's already valid JSON, leave it
                        try:
                            json.loads(qr_code_data)
                            json_string = qr_code_data  # Already valid JSON
                        except json.JSONDecodeError:
                            # Invalid format, set to empty dict
                            print(f"Warning: Invalid qr_code_data for participant {participant_id}, resetting to empty dict")
                            json_string = json.dumps({})
                    
                    # Update the record with valid JSON
                    cursor.execute(
                        "UPDATE events_participant SET qr_code_data = %s WHERE id = %s",
                        [json_string, participant_id]
                    )
                    
                except Exception as e:
                    print(f"Error converting qr_code_data for participant {participant_id}: {e}")
                    # Set to empty dict as fallback
                    cursor.execute(
                        "UPDATE events_participant SET qr_code_data = %s WHERE id = %s",
                        [json.dumps({}), participant_id]
                    )


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
