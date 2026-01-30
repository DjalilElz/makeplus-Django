"""
ePoster Serializers for API endpoints
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models_eposter import (
    EPosterSubmission, 
    EPosterValidation, 
    EPosterCommitteeMember,
    EPosterEmailTemplate
)


class EPosterAuthorSerializer(serializers.Serializer):
    """Serializer for individual authors in submission"""
    nom = serializers.CharField(max_length=100)
    prenom = serializers.CharField(max_length=100)
    affiliation = serializers.CharField(max_length=200, required=False, allow_blank=True)


class EPosterSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for ePoster submissions"""
    full_name = serializers.SerializerMethodField()
    validations_count = serializers.SerializerMethodField()
    rejections_count = serializers.SerializerMethodField()
    pending_validations = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_participation_display = serializers.CharField(source='get_type_participation_display', read_only=True)
    grade_display = serializers.CharField(source='get_grade_display', read_only=True)
    genre_display = serializers.CharField(source='get_genre_display', read_only=True)
    
    class Meta:
        model = EPosterSubmission
        fields = [
            'id', 'event',
            # Personal info
            'nom', 'prenom', 'full_name', 'email', 'telephone', 'genre', 'genre_display',
            # Professional info
            'grade', 'grade_display', 'grade_autre', 'service', 'etablissement', 'wilaya',
            # Submission details
            'type_participation', 'type_participation_display', 'theme', 'titre_travail',
            # Authors
            'auteurs',
            # Abstract
            'introduction', 'materiels_methodes', 'resultats', 'conclusion',
            # Files
            'fichier_resume', 'fichier_poster',
            # Status
            'status', 'status_display', 'validations_required',
            'validations_count', 'rejections_count', 'pending_validations',
            'rejection_reason',
            # Timestamps
            'submitted_at', 'updated_at', 'final_decision_date',
        ]
        read_only_fields = [
            'id', 'status', 'validations_count', 'rejections_count', 
            'pending_validations', 'submitted_at', 'updated_at',
            'final_decision_date', 'acceptance_email_sent', 'rejection_email_sent'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_validations_count(self, obj):
        return obj.get_validations_count()
    
    def get_rejections_count(self, obj):
        return obj.get_rejections_count()
    
    def get_pending_validations(self, obj):
        return obj.get_pending_validations_count()
    
    def validate_auteurs(self, value):
        """Validate authors list structure"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Authors must be a list")
        
        for i, author in enumerate(value):
            if not isinstance(author, dict):
                raise serializers.ValidationError(f"Author {i+1} must be an object")
            if 'nom' not in author or 'prenom' not in author:
                raise serializers.ValidationError(f"Author {i+1} must have 'nom' and 'prenom' fields")
        
        return value


class EPosterSubmissionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating ePoster submissions (public form)"""
    auteurs = EPosterAuthorSerializer(many=True, required=False)
    
    class Meta:
        model = EPosterSubmission
        fields = [
            'event',
            # Personal info
            'nom', 'prenom', 'email', 'telephone', 'genre',
            # Professional info
            'grade', 'grade_autre', 'service', 'etablissement', 'wilaya',
            # Submission details
            'type_participation', 'theme', 'titre_travail',
            # Authors
            'auteurs',
            # Abstract
            'introduction', 'materiels_methodes', 'resultats', 'conclusion',
            # Files
            'fichier_resume', 'fichier_poster',
        ]
    
    def create(self, validated_data):
        # Set default validations_required based on event settings if available
        event = validated_data.get('event')
        if event and hasattr(event, 'settings'):
            validations_required = event.settings.get('eposter_validations_required', 1)
            validated_data['validations_required'] = validations_required
        
        return super().create(validated_data)


class EPosterSubmissionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for submission lists"""
    full_name = serializers.SerializerMethodField()
    validations_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_participation_display = serializers.CharField(source='get_type_participation_display', read_only=True)
    
    class Meta:
        model = EPosterSubmission
        fields = [
            'id', 'nom', 'prenom', 'full_name', 'email',
            'type_participation', 'type_participation_display',
            'titre_travail', 'theme', 'etablissement',
            'status', 'status_display', 'validations_count',
            'validations_required', 'submitted_at'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_validations_count(self, obj):
        return obj.get_validations_count()


class EPosterValidationSerializer(serializers.ModelSerializer):
    """Serializer for committee validations"""
    committee_member_name = serializers.SerializerMethodField()
    submission_title = serializers.CharField(source='submission.titre_travail', read_only=True)
    
    class Meta:
        model = EPosterValidation
        fields = [
            'id', 'submission', 'submission_title',
            'committee_member', 'committee_member_name',
            'is_approved', 'comments', 'rating',
            'validated_at', 'updated_at'
        ]
        read_only_fields = ['id', 'committee_member', 'validated_at', 'updated_at']
    
    def get_committee_member_name(self, obj):
        user = obj.committee_member
        return user.get_full_name() or user.username


class EPosterValidationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating validations"""
    
    class Meta:
        model = EPosterValidation
        fields = ['submission', 'is_approved', 'comments', 'rating']
    
    def validate(self, attrs):
        request = self.context.get('request')
        submission = attrs.get('submission')
        
        # Check if user is a committee member for this event
        if request and request.user:
            is_committee_member = EPosterCommitteeMember.objects.filter(
                event=submission.event,
                user=request.user,
                is_active=True
            ).exists()
            
            if not is_committee_member:
                raise serializers.ValidationError(
                    "You must be a committee member to validate submissions"
                )
        
        return attrs
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['committee_member'] = request.user
        return super().create(validated_data)


class CommitteeMemberSerializer(serializers.ModelSerializer):
    """Serializer for committee members"""
    user_name = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source='user.email', read_only=True)
    validations_count = serializers.SerializerMethodField()
    pending_count = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = EPosterCommitteeMember
        fields = [
            'id', 'event', 'user', 'user_name', 'user_email',
            'role', 'role_display', 'specialty', 'is_active',
            'validations_count', 'pending_count',
            'assigned_at'
        ]
        read_only_fields = ['id', 'assigned_at']
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    
    def get_validations_count(self, obj):
        return obj.get_validations_count()
    
    def get_pending_count(self, obj):
        return obj.get_pending_submissions().count()


class EPosterEmailTemplateSerializer(serializers.ModelSerializer):
    """Serializer for ePoster email templates"""
    type_display = serializers.CharField(source='get_template_type_display', read_only=True)
    
    class Meta:
        model = EPosterEmailTemplate
        fields = [
            'id', 'event', 'template_type', 'type_display',
            'subject', 'body_html', 'body_text', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EPosterStatisticsSerializer(serializers.Serializer):
    """Serializer for ePoster statistics"""
    total_submissions = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    accepted_count = serializers.IntegerField()
    rejected_count = serializers.IntegerField()
    revision_requested_count = serializers.IntegerField()
    
    # By type
    by_type = serializers.DictField(child=serializers.IntegerField())
    
    # By theme
    by_theme = serializers.DictField(child=serializers.IntegerField())
    
    # Committee stats
    committee_members_count = serializers.IntegerField()
    total_validations = serializers.IntegerField()
