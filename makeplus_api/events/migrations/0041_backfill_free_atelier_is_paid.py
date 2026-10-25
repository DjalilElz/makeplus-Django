from django.db import migrations


def backfill_free_atelier_is_paid(apps, schema_editor):
    """
    Session.is_paid is what actually puts a workshop into the Workshops
    bloc on the public registration form (see
    dashboard.views_blocs.get_public_bloc_context and
    dashboard.blocs_service.resolve_catalog_prices, both of which filter
    Session.objects.filter(is_paid=True) unconditionally) -- despite its
    name, it does NOT mean "costs money"; a legitimately free-but-
    reservable workshop is is_paid=True with price=0.

    Before this was fixed (SessionForm.clean() used to reject exactly
    that combination, and the admin checkbox was labeled "Session/
    atelier payant" -- "Paid session/workshop"), an event owner creating
    a free workshop had no way to produce it: checking the box forced a
    price, leaving it unchecked (the only option left, and the natural
    reading of the label for something free) saved is_paid=False, which
    made the workshop permanently invisible on the registration form.

    This backfills exactly the ateliers caught by that now-fixed bug:
    session_type='atelier', price=0, is_paid=False. Scoped tightly to
    avoid touching anything that wasn't a victim of it:
    - session_type='atelier' only, not every session type, so a
      deliberately non-reservable conference/communication/etc. session
      is never affected.
    - price=0 only: a session with a real price and is_paid=False was a
      deliberate choice (e.g. an informational atelier not meant to be
      reservable), not something this bug could have produced, so it's
      left alone.
    Flipping is_paid to True here can't start charging anyone -- price
    stays 0 -- it only makes the workshop appear, which is exactly what
    the owner was trying to do when they created it.
    """
    db_alias = schema_editor.connection.alias
    Session = apps.get_model('events', 'Session')
    Session.objects.using(db_alias).filter(
        session_type='atelier', price=0, is_paid=False,
    ).update(is_paid=True)


def reverse_noop(apps, schema_editor):
    # Deliberately irreversible: we can no longer tell which of these
    # rows were already is_paid=True=>False=>True vs genuinely fixed by
    # this migration, and reversing would just reintroduce the bug this
    # exists to clean up.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0040_fix_location_url_nullable'),
    ]

    operations = [
        migrations.RunPython(backfill_free_atelier_is_paid, reverse_noop),
    ]
