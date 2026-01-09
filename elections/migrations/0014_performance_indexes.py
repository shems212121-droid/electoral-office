"""
Database Indexes Migration
Adding indexes for better query performance
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0013_userprofile'),
    ]

    operations = [
        # Voter indexes
        migrations.AddIndex(
            model_name='voter',
            index=models.Index(fields=['voter_number'], name='voter_number_idx'),
        ),
        migrations.AddIndex(
            model_name='voter',
            index=models.Index(fields=['full_name'], name='voter_name_idx'),
        ),
        migrations.AddIndex(
            model_name='voter',
            index=models.Index(fields=['classification'], name='voter_class_idx'),
        ),
        migrations.AddIndex(
            model_name='voter',
            index=models.Index(fields=['introducer'], name='voter_intro_idx'),
        ),
        
        # PartyCandidate indexes
        migrations.AddIndex(
            model_name='partycandidate',
            index=models.Index(fields=['party', 'serial_number'], name='candidate_party_idx'),
        ),
        migrations.AddIndex(
            model_name='partycandidate',
            index=models.Index(fields=['full_name'], name='candidate_name_idx'),
        ),
        
        # Anchor indexes
        migrations.AddIndex(
            model_name='anchor',
            index=models.Index(fields=['candidate'], name='anchor_cand_idx'),
        ),
        
        # Introducer indexes
        migrations.AddIndex(
            model_name='introducer',
            index=models.Index(fields=['anchor'], name='intro_anchor_idx'),
        ),
        
        # VoteCount indexes
        migrations.AddIndex(
            model_name='votecount',
            index=models.Index(fields=['station', 'candidate'], name='vote_station_cand_idx'),
        ),
        migrations.AddIndex(
            model_name='votecount',
            index=models.Index(fields=['entered_at'], name='vote_date_idx'),
        ),
        
        # UserProfile indexes
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['role'], name='profile_role_idx'),
        ),
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['is_active'], name='profile_active_idx'),
        ),
    ]
