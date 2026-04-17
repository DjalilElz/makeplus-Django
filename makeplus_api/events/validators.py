"""
Custom Password Validators
"""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re


class MinimumLengthValidator:
    """
    Validate that the password is at least 8 characters long.
    """
    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _("Password must be at least %(min_length)d characters long."),
                code='password_too_short',
                params={'min_length': self.min_length},
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least %(min_length)d characters."
            % {'min_length': self.min_length}
        )


class ContainsNumberValidator:
    """
    Validate that the password contains at least one number.
    """
    def validate(self, password, user=None):
        if not re.search(r'\d', password):
            raise ValidationError(
                _("Password must contain at least one number."),
                code='password_no_number',
            )

    def get_help_text(self):
        return _("Your password must contain at least one number.")
