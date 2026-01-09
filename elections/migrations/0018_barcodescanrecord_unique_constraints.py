# Generated migration for adding unique constraints to BarcodeScanRecord
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0017_barcodescansession_barcodescanrecord'),
    ]

    operations = [
        # Add unique constraint to prevent duplicate scans of same station
        # Only for successfully processed records
        migrations.AddConstraint(
            model_name='barcodescanrecord',
            constraint=models.UniqueConstraint(
                fields=['center_number', 'station_number'],
                condition=models.Q(status__in=['validated', 'processed']),
                name='unique_validated_station_scan',
                violation_error_message='هذه المحطة تم مسحها ومعالجتها مسبقاً'
            ),
        ),
        
        # Add index for faster duplicate checking
        migrations.AddIndex(
            model_name='barcodescanrecord',
            index=models.Index(
                fields=['center_number', 'station_number', 'status'],
                name='idx_scan_center_station'
            ),
        ),
    ]
