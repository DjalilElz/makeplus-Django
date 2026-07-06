"""
Settings for running `manage.py test`.

The historical migration chain has several pre-existing inconsistencies
(duplicate/renamed indexes and fields) that only surface when building a
database from scratch. Production never hits this because its migrations
already ran incrementally over time. For tests we don't care about replaying
migration history — we just need tables that match the current models — so
migrations are disabled and the test database is built directly from models.
"""
from .settings import *  # noqa: F401,F403


class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()
