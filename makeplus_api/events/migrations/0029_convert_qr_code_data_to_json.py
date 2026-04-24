# Generated migration to convert qr_code_data from string to JSON

from django.db import migrations
import json


def convert_qr_code_data_to_json(apps, schema_editor):
    """Convert existing qr_code_data from string/dict to valid JSON"""
    Participant = apps.get_model('events', 'Participant')
    
    for participant in Participant.objects.all():
        if participant.qr_code_data:
            try:
                # If it's already a dict (shouldn't happen but just in case)
                if isinstance(participant.qr_code_data, dict):
                    # Convert dict to JSON string
                    participant.qr_code_data = json.dumps(participant.qr_code_data)
                    participant.save(update_fields=['qr_code_data'])
                # If it's a string that looks like a dict (with single quotes)
                elif isinstance(participant.qr_code_data, str):
                    # Try to parse it as Python literal
                    import ast
                    try:
                        data_dict = ast.literal_eval(participant.qr_code_data)
                        # Convert to valid JSON string
                        participant.qr_code_data = json.dumps(data_dict)
                        participant.save(update_fields=['qr_code_data'])
                    except (ValueError, SyntaxError):
                        # If it's already valid JSON, leave it
                        try:
                            json.loads(participant.qr_code_data)
                            # Already valid JSON, no change needed
                        except json.JSONDecodeError:
                            # Invalid format, set to empty dict
                            print(f"Warning: Invalid qr_code_data for participant {participant.id}, resetting to empty dict")
                            participant.qr_code_data = json.dumps({})
                            participant.save(update_fields=['qr_code_data'])
            except Exception as e:
                print(f"Error converting qr_code_data for participant {participant.id}: {e}")
                # Set to empty dict as fallback
                participant.qr_code_data = json.dumps({})
                participant.save(update_fields=['qr_code_data'])


def reverse_conversion(apps, schema_editor):
    """Reverse migration - convert JSON back to string"""
    # No need to reverse, data is already in string format
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0025_restructure_participant_model'),
    ]

    operations = [
        migrations.RunPython(convert_qr_code_data_to_json, reverse_conversion),
    ]
