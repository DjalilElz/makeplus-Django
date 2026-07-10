#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
    try:
        import django
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    if len(sys.argv) > 1 and sys.argv[1] == 'migrate':
        # Self-heal a prod migration-history inconsistency before Django's
        # own consistency check can block this (and every future) migrate.
        # See dashboard/migration_history_fix.py.
        django.setup()
        from dashboard.migration_history_fix import fix_migration_history
        fix_migration_history(log=print)

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
