# No-op migration - cleanup already completed

from django.db import migrations


def noop(apps, schema_editor):
    """No operation - this migration has already been applied"""
    print("Migration 0027: No operation needed (already applied)")
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0025_restructure_participant_model'),
    ]

    operations = [
        migrations.RunPython(noop, migrations.RunPython.noop),
    ]
