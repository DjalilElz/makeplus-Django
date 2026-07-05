"""
Management command to fix old URLs in email templates
Usage: python manage.py fix_email_template_urls
"""
from django.core.management.base import BaseCommand
from dashboard.models_eposter import ScientificContributionEmailTemplate


class Command(BaseCommand):
    help = 'Replace old final submission URLs with new URL structure in email templates'

    def handle(self, *args, **options):
        old_patterns = [
            'https://makeplus-django-5.onrender.com/dashboard/contributions/final-submission/',
            'makeplus-django-5.onrender.com/dashboard/contributions/final-submission/',
            '/dashboard/contributions/final-submission/',
        ]
        
        new_pattern = '/dashboard/events/{{event_id}}/contributions/final-submission/'
        
        templates = ScientificContributionEmailTemplate.objects.all()
        updated_count = 0
        
        for template in templates:
            original_html = template.body_html
            updated_html = original_html
            
            # Replace all old patterns with the correct one
            for old_pattern in old_patterns:
                if old_pattern in updated_html:
                    # Replace with variable-based URL
                    updated_html = updated_html.replace(
                        old_pattern,
                        'https://makeplus-platform.onrender.com/dashboard/events/{{event.id}}/contributions/final-submission/'
                    )
                    self.stdout.write(
                        self.style.WARNING(f'Found old URL pattern in template: {template.event.name} - {template.get_template_type_display()}')
                    )
            
            # If HTML was changed, save it
            if updated_html != original_html:
                template.body_html = updated_html
                template.save(update_fields=['body_html'])
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Updated template: {template.event.name} - {template.get_template_type_display()}')
                )
        
        if updated_count == 0:
            self.stdout.write(self.style.SUCCESS('No templates needed updating.'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Successfully updated {updated_count} template(s)!')
            )
            self.stdout.write(
                self.style.WARNING('\nNote: Templates now use Django template variables.')
            )
            self.stdout.write(
                self.style.WARNING('The {{event.id}} will be rendered when emails are sent.')
            )
