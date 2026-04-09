from django.db import models

# Import email models
from .models_email import EmailTemplate, EventEmailTemplate, EmailLog

# Import ePoster models
from .models_eposter import (
    EPosterSubmission, 
    EPosterValidation, 
    EPosterCommitteeMember,
    EPosterEmailTemplate
)
