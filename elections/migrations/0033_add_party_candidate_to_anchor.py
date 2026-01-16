# Generated migration for adding party_candidate field to Anchor model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0032_registrationcenter_voter_polling_center_and_more'),
    ]

    operations = [
        # Make candidate field nullable
        migrations.AlterField(
            model_name='anchor',
            name='candidate',
            field=models.ForeignKey(
                blank=True, 
                null=True, 
                on_delete=django.db.models.deletion.CASCADE, 
                related_name='anchors', 
                to='elections.candidate', 
                verbose_name='المرشح'
            ),
        ),
        # Add new party_candidate field
        migrations.AddField(
            model_name='anchor',
            name='party_candidate',
            field=models.ForeignKey(
                blank=True, 
                null=True, 
                on_delete=django.db.models.deletion.CASCADE, 
                related_name='anchors', 
                to='elections.partycandidate', 
                verbose_name='المرشح (جديد)'
            ),
        ),
    ]
