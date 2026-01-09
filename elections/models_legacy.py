from django.db import models

class PersonHD(models.Model):
    per_id = models.BigIntegerField(primary_key=True, db_column='PER_ID')
    per_famno = models.BigIntegerField(db_column='PER_FAMNO', null=True)
    per_first = models.CharField(max_length=15, db_column='PER_FIRST', null=True)
    per_father = models.CharField(max_length=15, db_column='PER_FATHER', null=True)
    per_grand = models.CharField(max_length=15, db_column='PER_GRAND', null=True)
    per_dob = models.CharField(max_length=10, db_column='PER_DOB', null=True)
    psno = models.IntegerField(db_column='PSNO', null=True)
    pcno = models.IntegerField(db_column='PCNO', null=True)

    per_vrc_id = models.IntegerField(db_column='VRC_ID', null=True)
    per_gov_id = models.IntegerField(db_column='GOV_MOT_ID', null=True)

    class Meta:
        managed = False
        db_table = 'PersonHD'
        app_label = 'elections'

class PCHd(models.Model):
    pcno = models.IntegerField(primary_key=True, db_column='PCNO')
    pc_name = models.CharField(max_length=70, db_column='PC_NAME', null=True)
    class Meta:
        managed = False
        db_table = 'PC_HD'
        app_label = 'elections'

class VrcHD(models.Model):
    vrc_id = models.IntegerField(primary_key=True, db_column='VRC_ID')
    vrc_name_ar = models.CharField(max_length=35, db_column='VRC_NAME_AR', null=True)
    class Meta:
        managed = False
        db_table = 'VRC_HD'
        app_label = 'elections'

class GovernorateHD(models.Model):
    gov_no = models.CharField(max_length=2, primary_key=True, db_column='GovNo')
    gov_name = models.CharField(max_length=15, db_column='GovName', null=True)
    class Meta:
        managed = False
        db_table = 'GovernorateHD'
        app_label = 'elections'
