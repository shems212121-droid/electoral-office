# Generated migration for fixing phone field length

from django.db import migrations, models
import elections.validators


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0032_registrationcenter_voter_polling_center_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='voter',
            name='phone',
            field=models.CharField(blank=True, max_length=30, null=True, validators=[elections.validators.validate_phone_number], verbose_name='رقم الهاتف'),
        ),
    ]
