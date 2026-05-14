# Generated manually - clean migration for eposter final submission

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0015_emailcampaign_external_campaign_id_and_more'),
        ('events', '0032_alter_exposantscan_notes'),
    ]

    operations = [
        # Create EPosterFinalSubmission model
        migrations.CreateModel(
            name='EPosterFinalSubmission',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('nom', models.CharField(max_length=100, verbose_name='Nom')),
                ('email', models.EmailField(max_length=254, verbose_name='Email')),
                ('telephone', models.CharField(max_length=20, verbose_name='Téléphone')),
                ('specialite', models.CharField(choices=[('allerologie', 'Allerologie'), ('anatomique', 'Anatomique'), ('anesthesiologie', 'Anesthésiologie'), ('biologie', 'Biologie'), ('chirurgie_cardiaque', 'Chirurgie cardiaque'), ('dermatologie', 'Dermatologie'), ('diabetologie_endocrinologie', 'Diabétologie endocrinologie'), ('gastro_enterologie_hepatologie', 'Gastro-entérologie et hépatologie'), ('obstetrique_gynecologie', 'Obstétrique et gynécologie'), ('hematologie', 'Hématologie'), ('immunologie', 'Immunologie'), ('maladies_infectieuses', 'Maladies infectieuses'), ('medecine_travail', 'Médecine du travail'), ('medecine_interne', 'Médecine interne'), ('medecine_generale', 'Médecine générale'), ('nephrologie', 'Néphrologie'), ('oncologie', 'Oncologie'), ('ophtalmologie', 'Ophtalmologie'), ('orl', 'ORL'), ('professions_sante_alliees', 'Professions de santé alliées'), ('pediatrie', 'Pédiatrie'), ('pneumologie', 'Pneumologie'), ('pharmacie_hospitaliere', 'Pharmacie hospitalière'), ('pharmacien_officine', "Pharmacien d'officine"), ('medecine_soins_intensifs', 'Médecine de soins intensifs'), ('psychiatrie', 'Psychiatrie'), ('radiologie', 'Radiologie'), ('rhumatologie', 'Rhumatologie'), ('urologie', 'Urologie'), ('chirurgie_dentaire', 'Chirurgie dentaire'), ('chirurgie_pediatrique', 'Chirurgie pédiatrique')], max_length=100, verbose_name='Spécialité')),
                ('domaine_communication', models.CharField(choices=[('rhinologie', 'Rhinologie'), ('pathologie_cervico_facial', 'Pathologie cervico-facial'), ('thyroide_parathyroide', 'Thyroïde et parathyroïde'), ('orl_pediatrique', 'ORL pédiatrique'), ('laryngologie_trachee', 'Laryngologie trachée'), ('otologie', 'Otologie'), ('cancerologie', 'Cancérologie'), ('divers', 'Divers')], max_length=100, verbose_name='Domaine de communication')),
                ('poster_number', models.CharField(max_length=50, verbose_name='Poster N° (Code)')),
                ('titre', models.CharField(max_length=500, verbose_name='Titre')),
                ('auteurs', models.TextField(verbose_name='Auteurs')),
                ('co_auteurs', models.TextField(blank=True, verbose_name='Co-auteurs')),
                ('abstract_file', models.FileField(upload_to='eposters/final_submissions/', verbose_name='Fichier Abstract (PDF)')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eposter_final_submissions', to='events.event')),
                ('original_submission', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='final_submission', to='dashboard.epostersubmission', verbose_name='Soumission originale')),
            ],
            options={
                'verbose_name': 'ePoster Final Submission',
                'verbose_name_plural': 'ePoster Final Submissions',
                'ordering': ['-submitted_at'],
            },
        ),
        
        # Add eposter_code field to EPosterSubmission
        migrations.AddField(
            model_name='epostersubmission',
            name='eposter_code',
            field=models.CharField(blank=True, max_length=50, unique=True, verbose_name='Code ePoster'),
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='eposterfinalsubmission',
            index=models.Index(fields=['event', '-submitted_at'], name='dashboard_e_event_i_418864_idx'),
        ),
        migrations.AddIndex(
            model_name='eposterfinalsubmission',
            index=models.Index(fields=['poster_number'], name='dashboard_e_poster__f44ff8_idx'),
        ),
    ]
