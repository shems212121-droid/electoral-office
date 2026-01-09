from django.core.exceptions import ValidationError
import re


def validate_phone_number(value):
    """
    التحقق من أن رقم الهاتف يتكون من 11 رقماً بالضبط
    """
    if value:
        # إزالة أي مسافات أو رموز خاصة
        cleaned_value = re.sub(r'[^\d]', '', str(value))
        
        if len(cleaned_value) != 11:
            raise ValidationError(
                'رقم الهاتف يجب أن يتكون من 11 رقماً بالضبط.',
                code='invalid_phone_length'
            )
        
        # التحقق من أن جميع الأحرف أرقام
        if not cleaned_value.isdigit():
            raise ValidationError(
                'رقم الهاتف يجب أن يحتوي على أرقام فقط.',
                code='invalid_phone_format'
            )


def validate_voter_number_required(value):
    """
    التحقق من أن رقم الناخب غير فارغ
    """
    if not value or str(value).strip() == '':
        raise ValidationError(
            'رقم الناخب حقل إجباري.',
            code='voter_number_required'
        )
