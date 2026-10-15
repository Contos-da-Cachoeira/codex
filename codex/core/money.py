from decimal import Decimal, InvalidOperation

from django import forms
from django.core.exceptions import ValidationError


def validate_gold(value):
    try:
        amount = Decimal(str(value).replace(',', '.'))
    except InvalidOperation:
        raise ValidationError('Informe um valor em DO, por exemplo 2 ou 2,5.')
    if not amount.is_finite() or amount < 0 or amount > 2147483647:
        raise ValidationError('O saldo em DO precisa estar entre 0 e 2147483647.')
    if amount % Decimal('0.5'):
        raise ValidationError('Use múltiplos de 0,5 DO (1 Dindim de Prata).')


class GoldField(forms.DecimalField):
    def __init__(self, **kwargs):
        super().__init__(max_digits=11, decimal_places=1, min_value=0,
                         max_value=2147483647, validators=[validate_gold], **kwargs)
        self.widget.attrs['step'] = '0.5'

    def to_python(self, value):
        amount = super().to_python(value.replace(',', '.') if isinstance(value, str) else value)
        return amount.normalize() if amount is not None and amount.is_finite() else amount
