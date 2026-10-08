from django.db import migrations


class Migration(migrations.Migration):
    """
    Production's events_event.location_url column has a NOT NULL
    constraint with no default, even though the model has always
    declared null=True -- creating a new event (which never sets this
    optional field) fails with "null value in column location_url
    violates not-null constraint". Likely the column was created NOT
    NULL by whatever process first added it, before migration
    0017_event_location_url's own guarded ADD COLUMN ran and saw it
    already existed (only checking presence, not nullability), so it
    never got a chance to add it nullable as intended.

    DROP NOT NULL is safe to run unconditionally -- a no-op if the
    column is already nullable, and reversible (ALTER ... SET NOT NULL
    would only make sense going forward if every existing row already
    has a non-null value, which isn't guaranteed, so reverse is a
    deliberate no-op instead of risking a failed rollback).
    """

    dependencies = [
        ('events', '0039_add_password_reset_verification'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE events_event ALTER COLUMN location_url DROP NOT NULL;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
