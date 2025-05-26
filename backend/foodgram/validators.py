from django.core.exceptions import ValidationError

from .constants import MAX_USER


def validate_name(value):
    if len(value) > MAX_USER:
        raise ValidationError(
            f'Длина поля не должна превышать {MAX_USER} символов.'
        )
    return value
