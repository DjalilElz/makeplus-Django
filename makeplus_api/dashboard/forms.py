"""
Forms for MakePlus Dashboard
Multi-step event creation and user management
"""

from django import forms
from django.contrib.auth.models import User
from events.models import Event, Room, Session, UserEventAssignment, Participant
from django.core.exceptions import ValidationError
from decimal import Decimal
import json
from dashboard.models_email import EmailCampaign, EmailTemplate


class EventDetailsForm(forms.ModelForm):
    """Step 1: Event Basic Details (for creation)"""
    
    number_of_rooms = forms.IntegerField(
        min_value=1,
        max_value=50,
        initial=1,
        required=True,
        help_text="How many rooms/salles will this event have?",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 3'
        })
    )
    
    class Meta:
        model = Event
        fields = [
            'name', 'description', 'start_date', 'end_date', 
            'location', 'location_details', 'status',
            'logo', 'banner', 'organizer_contact',
            'programme_file', 'guide_file'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., TechSummit Algeria 2025'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Brief description of the event...'
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Centre des Congrès, Alger'
            }),
            'location_details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional location details...'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'banner': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'organizer_contact': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@event.com'
            }),
            'programme_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf'
            }),
            'guide_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date <= start_date:
            raise ValidationError('End date must be after start date')
        
        return cleaned_data


class EventEditForm(forms.ModelForm):
    """Form for editing existing events (without number_of_rooms field)"""
    
    class Meta:
        model = Event
        fields = [
            'name', 'description', 'start_date', 'end_date', 
            'location', 'location_details', 'status',
            'logo', 'banner', 'organizer_contact',
            'programme_file', 'guide_file'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., TechSummit Algeria 2025'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Brief description of the event...'
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Centre des Congrès, Alger'
            }),
            'location_details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional location details...'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'banner': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'organizer_contact': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'organizer@example.com'
            }),
            'programme_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf'
            }),
            'guide_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf'
            }),
        }
    
    def clean(self):
        """Validate form data"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date <= start_date:
            raise ValidationError('End date must be after start date')
        
        return cleaned_data


class RoomForm(forms.ModelForm):
    """Step 2: Room/Salle Details (used multiple times based on number_of_rooms)"""
    
    class Meta:
        model = Room
        fields = ['name', 'capacity', 'description', 'location']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Salle Principale, Auditorium A'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Maximum capacity',
                'min': '1'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Room description and features...'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Location within venue (e.g., Ground Floor, Section A)'
            }),
        }


class SessionForm(forms.ModelForm):
    """Step 3: Session Details (Conferences/Ateliers for each room)"""
    
    room = forms.ModelChoiceField(
        queryset=Room.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label="Room"
    )
    
    class Meta:
        model = Session
        fields = [
            'title', 'description', 'session_type', 'room', 'start_time', 'end_time',
            'speaker_name', 'speaker_title', 'speaker_bio', 'speaker_photo_url',
            'theme', 'is_paid', 'price', 'youtube_live_url', 'status', 'cover_image_url'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Introduction to AI & Machine Learning'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Session description...'
            }),
            'session_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'speaker_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Dr. Ahmed Benali'
            }),
            'speaker_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., AI Research Scientist'
            }),
            'speaker_bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Speaker biography...'
            }),
            'speaker_photo_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/photo.jpg'
            }),
            'theme': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Artificial Intelligence, Blockchain'
            }),
            'is_paid': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'youtube_live_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://youtube.com/watch?v=...'
            }),
            'cover_image_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/cover.jpg'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        if event:
            self.fields['room'].queryset = Room.objects.filter(event=event)
    
    def clean(self):
        cleaned_data = super().clean()
        is_paid = cleaned_data.get('is_paid')
        price = cleaned_data.get('price')
        
        if is_paid and (not price or price <= 0):
            raise ValidationError('Paid sessions must have a price greater than 0')
        
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and end_time <= start_time:
            raise ValidationError('End time must be after start time')
        
        return cleaned_data


class UserCreationForm(forms.ModelForm):
    """Step 4: Create users and assign roles"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        }),
        help_text="User's password"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        }),
        label="Confirm Password"
    )
    
    role = forms.ChoiceField(
        choices=UserEventAssignment.ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'toggleRoomField()'
        }),
        help_text="User's role for this event"
    )
    
    # Conditional field for organisateur, gestionnaire_des_salles and controlleur_des_badges
    assigned_room = forms.ModelChoiceField(
        queryset=Room.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        help_text="Select room to assign (for organisateur, gestionnaire des salles or controlleur des badges)"
    )
    
    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        if event:
            self.fields['assigned_room'].queryset = Room.objects.filter(event=event)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
        }
    
    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise ValidationError('Passwords do not match')
        
        return password_confirm
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class QuickUserForm(forms.Form):
    """Quick user creation form for dashboard"""
    
    # Step 1: Role selection first (only admin-creatable roles, not participant)
    role = forms.ChoiceField(
        choices=UserEventAssignment.ADMIN_CREATABLE_ROLES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'toggleConditionalFields()'
        })
    )
    
    # Step 2: Event selection
    event = forms.ModelChoiceField(
        queryset=Event.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'updateRoomOptions(this.value)'
        })
    )
    
    # Conditional field for gestionnaire_salle and controlleur
    assigned_room = forms.ModelChoiceField(
        queryset=Room.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        help_text="Select room to assign (for Gestionnaire de Salle or Contrôleur)"
    )
    
    # Step 3: User information
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'user@example.com'
        })
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial room queryset - show all rooms, will be filtered by JavaScript
        # Or filter by event if provided in POST data
        if 'event' in self.data:
            try:
                event_id = self.data.get('event')
                self.fields['assigned_room'].queryset = Room.objects.filter(event_id=event_id)
            except (ValueError, TypeError):
                pass
        elif self.initial.get('event'):
            self.fields['assigned_room'].queryset = Room.objects.filter(event=self.initial['event'])
        else:
            # Show all rooms initially
            self.fields['assigned_room'].queryset = Room.objects.all().select_related('event')


class RoomAssignmentForm(forms.Form):
    """Assign gestionnaires to rooms"""
    
    room = forms.ModelChoiceField(
        queryset=Room.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    gestionnaire = forms.ModelChoiceField(
        queryset=User.objects.none(),  # Will be populated in __init__
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        
        if event:
            # Filter rooms by event
            self.fields['room'].queryset = Room.objects.filter(event=event)
            
            # Filter users who are gestionnaires for this event
            gestionnaire_ids = UserEventAssignment.objects.filter(
                event=event,
                role='gestionnaire_des_salles',
                is_active=True
            ).values_list('user_id', flat=True)
            
            self.fields['gestionnaire'].queryset = User.objects.filter(
                id__in=gestionnaire_ids
            )


# Caisse Management Forms

class CaisseForm(forms.ModelForm):
    """Form for creating/editing caisses"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Leave blank to keep existing password (for edits)"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        label="Confirm Password"
    )

    class Meta:
        from caisse.models import Caisse
        model = Caisse
        fields = ['name', 'email', 'event', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'event': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        # Only validate if password is provided
        if password:
            if password != password_confirm:
                raise forms.ValidationError("Passwords do not match")
            if len(password) < 6:
                raise forms.ValidationError("Password must be at least 6 characters long")

        # For new instances, password is required
        if not self.instance.pk and not password:
            raise forms.ValidationError("Password is required for new caisses")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        password = self.cleaned_data.get('password')
        
        # Only set password if provided
        if password:
            instance.set_password(password)
        
        if commit:
            instance.save()
        return instance


class PayableItemForm(forms.ModelForm):
    """Form for creating/editing payable items"""
    
    class Meta:
        from caisse.models import PayableItem
        model = PayableItem
        fields = ['event', 'name', 'description', 'price', 'item_type', 'session', 'is_active']
        widgets = {
            'event': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'item_type': forms.Select(attrs={'class': 'form-select'}),
            'session': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        
        # Make session optional
        self.fields['session'].required = False
        self.fields['session'].empty_label = "None (not linked to a session)"
        
        # Filter sessions by event
        if event:
            # When creating new item with event passed
            self.fields['session'].queryset = Session.objects.filter(event=event)
            # Hide and set event field
            self.fields['event'].widget = forms.HiddenInput()
            self.fields['event'].initial = event.id
        elif 'event' in self.data:
            # When form is submitted
            try:
                event_id = int(self.data.get('event'))
                self.fields['session'].queryset = Session.objects.filter(event_id=event_id)
            except (ValueError, TypeError):
                self.fields['session'].queryset = Session.objects.none()
        elif self.instance.pk and self.instance.event:
            # When editing existing item
            self.fields['session'].queryset = Session.objects.filter(event=self.instance.event)
        else:
            # Default: no sessions
            self.fields['session'].queryset = Session.objects.none()


class CaisseLoginForm(forms.Form):
    """Form for caisse operator login"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )


class EmailCampaignForm(forms.ModelForm):
    """Form for creating and editing email campaigns"""
    
    class Meta:
        model = EmailCampaign
        fields = [
            'name', 'event', 'subject', 'from_email', 'from_name', 
            'reply_to', 'track_opens', 'track_clicks'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., January Newsletter 2026'
            }),
            'event': forms.Select(attrs={
                'class': 'form-select'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 🎉 Exciting Updates from MakePlus!'
            }),
            'from_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'noreply@makeplus.com'
            }),
            'from_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., MakePlus Team'
            }),
            'reply_to': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'support@makeplus.com (optional)'
            }),
            'track_opens': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'track_clicks': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make event optional
        self.fields['event'].required = False
        self.fields['reply_to'].required = False
        
        # Set default from_email from settings if available
        if not self.initial.get('from_email'):
            from django.conf import settings
            self.initial['from_email'] = getattr(settings, 'DEFAULT_FROM_EMAIL', '')

