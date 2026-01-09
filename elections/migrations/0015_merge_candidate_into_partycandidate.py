# Generated migration for merging Candidate and PartyCandidate models

from django.db import migrations, models
import django.db.models.deletion


def migrate_candidates_to_party_candidates(apps, schema_editor):
    """نقل بيانات Candidate إلى PartyCandidate"""
    Candidate = apps.get_model('elections', 'Candidate')
    PartyCandidate = apps.get_model('elections', 'PartyCandidate')
    Anchor = apps.get_model('elections', 'Anchor')
    CandidateMonitor = apps.get_model('elections', 'CandidateMonitor')
    
    # إنشاء mapping من ID القديم إلى ID الجديد
    id_mapping = {}
    
    for candidate in Candidate.objects.all():
        # إنشاء سجل PartyCandidate جديد
        party_candidate = PartyCandidate.objects.create(
            candidate_code=candidate.candidate_code,
            full_name=candidate.full_name,
            voter_number=candidate.voter_number,
            phone=candidate.phone,
            mother_name_triple=candidate.mother_name_triple,
            date_of_birth=candidate.date_of_birth,
            address=candidate.address,
            voting_center_number=candidate.voting_center_number,
            voting_center_name=candidate.voting_center_name,
            registration_center_number=candidate.registration_center_number,
            registration_center_name=candidate.registration_center_name,
            family_number=candidate.family_number,
            governorate=candidate.governorate,
            station_number=candidate.station_number,
            status=candidate.status,
            created_at=candidate.created_at,
            updated_at=candidate.updated_at,
            # الحقول الجديدة الخاصة بالأحزاب تبقى فارغة
            party=None,
            serial_number=None,
            council_type='parliament',
        )
        
        # حفظ التطابق
        id_mapping[candidate.id] = party_candidate.id
    
    # تحديث Anchor records لتشير إلى PartyCandidate
    for anchor in Anchor.objects.all():
        if anchor.candidate_id in id_mapping:
            anchor.candidate_id = id_mapping[anchor.candidate_id]
            anchor.save()
    
    # تحديث CandidateMonitor records لتشير إلى PartyCandidate
    for monitor in CandidateMonitor.objects.all():
        if monitor.candidate_id and monitor.candidate_id in id_mapping:
            monitor.candidate_id = id_mapping[monitor.candidate_id]
            monitor.save()


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0014_performance_indexes'),
    ]

    operations = [
        # Step 1: Add new fields to PartyCandidate
        migrations.AddField(
            model_name='partycandidate',
            name='mother_name_triple',
            field=models.CharField(blank=True, max_length=100, verbose_name='اسم الأم ثلاثي'),
        ),
        migrations.AddField(
            model_name='partycandidate',
            name='date_of_birth',
            field=models.DateField(blank=True, null=True, verbose_name='تاريخ الميلاد'),
        ),
        migrations.AddField(
            model_name='partycandidate',
            name='address',
            field=models.CharField(blank=True, max_length=200, verbose_name='عنوان السكن'),
        ),
        migrations.AddField(
            model_name='partycandidate',
            name='voting_center_number',
            field=models.CharField(blank=True, max_length=50, verbose_name='رقم مركز الاقتراع'),
        ),
        migrations.AddField(
            model_name='partycandidate',
            name='voting_center_name',
            field=models.CharField(blank=True, max_length=150, verbose_name='اسم مركز الاقتراع'),
        ),
        migrations.AddField(
            model_name='partycandidate',
            name='registration_center_number',
            field=models.CharField(blank=True, max_length=50, verbose_name='رقم مركز التسجيل'),
        ),
        migrations.AddField(
            model_name='partycandidate',
            name='registration_center_name',
            field=models.CharField(blank=True, max_length=150, verbose_name='اسم مركز التسجيل'),
        ),
        migrations.AddField(
            model_name='partycandidate',
            name='family_number',
            field=models.CharField(blank=True, max_length=50, verbose_name='رقم العائلة'),
        ),
        migrations.AddField(
            model_name='partycandidate',
            name='governorate',
            field=models.CharField(default='البصرة', max_length=50, verbose_name='المحافظة'),
        ),
        migrations.AddField(
            model_name='partycandidate',
            name='station_number',
            field=models.CharField(blank=True, max_length=50, verbose_name='رقم المحطة'),
        ),
        migrations.AddField(
            model_name='partycandidate',
            name='status',
            field=models.CharField(blank=True, max_length=50, verbose_name='الحالة'),
        ),
        
        # Step 2: Make party and serial_number nullable
        migrations.AlterField(
            model_name='partycandidate',
            name='party',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='candidates', to='elections.politicalparty', verbose_name='الحزب'),
        ),
        migrations.AlterField(
            model_name='partycandidate',
            name='serial_number',
            field=models.IntegerField(blank=True, null=True, verbose_name='الرقم التسلسلي في القائمة'),
        ),
        
        # Step 3: Migrate data from Candidate to PartyCandidate
        migrations.RunPython(migrate_candidates_to_party_candidates, migrations.RunPython.noop),
        
        # Step 4: Update foreign keys to point to PartyCandidate
        migrations.AlterField(
            model_name='anchor',
            name='candidate',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='anchors', to='elections.partycandidate', verbose_name='المرشح'),
        ),
        migrations.AlterField(
            model_name='candidatemonitor',
            name='candidate',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='monitors', to='elections.partycandidate', verbose_name='المرشح'),
        ),
        
        # Step 5: Update Meta options
        migrations.AlterModelOptions(
            name='partycandidate',
            options={'ordering': ['-created_at'], 'verbose_name': 'مرشح', 'verbose_name_plural': 'المرشحون'},
        ),
        migrations.AlterUniqueTogether(
            name='partycandidate',
            unique_together=set(),
        ),
    ]
