from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_birth_date(value):
    if value > timezone.localdate():
        raise ValidationError('A data de nascimento não pode estar no futuro.')
