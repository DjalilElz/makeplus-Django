from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Real production failure: Django's ImageField defaults to a 100-char
    column for the stored filename, and a real uploaded filename plus
    the upload_to prefix routinely exceeds that -- Postgres raised
    "value too long for type character varying(100)" on the very first
    real upload with a descriptive filename. Widening an already-varchar
    column is naturally idempotent (a no-op if already 255+), so no
    extra guarding needed here unlike this project's other migrations.
    """

    dependencies = [
        ('dashboard', '0046_attestationtemplate_attestationsendlog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attestationtemplate',
            name='template_image',
            field=models.ImageField(max_length=255, upload_to='events/attestation_templates/', verbose_name='Image du modèle'),
        ),
    ]
