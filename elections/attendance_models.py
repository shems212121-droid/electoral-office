# -*- coding: utf-8 -*-
"""
نماذج إضافية لنظام تسجيل الحضور والانصراف
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class AttendanceRecord(models.Model):
    """سجل حضور وانصراف الوكلاء والمراقبين"""
    
    RECORD_TYPE_CHOICES = [
        ('agent', 'وكيل كيان سياسي'),
        ('monitor', 'مراقب مرشح'),
    ]
    
    STATUS_CHOICES = [
        ('checked_in', 'حضر'),
        ('checked_out', 'انصرف'),
    ]
    
    # Agent or Monitor info
    agent = models.ForeignKey('PoliticalEntityAgent', on_delete=models.CASCADE, 
                             related_name='attendance_records', null=True, blank=True,
                             verbose_name="الوكيل")
    monitor = models.ForeignKey('CandidateMonitor', on_delete=models.CASCADE,
                               related_name='attendance_records', null=True, blank=True,
                               verbose_name="المراقب")
    
    # Center Director who recorded
    recorded_by = models.ForeignKey('CenterDirector', on_delete=models.CASCADE,
                                   related_name='attendance_records',
                                   verbose_name="سجل بواسطة")
    
    # Record details
    record_type = models.CharField(max_length=10, choices=RECORD_TYPE_CHOICES,
                                   verbose_name="نوع السجل")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES,
                             verbose_name="الحالة")
    
    # Timestamps
    check_in_time = models.DateTimeField(null=True, blank=True,
                                        verbose_name="وقت الحضور")
    check_out_time = models.DateTimeField(null=True, blank=True,
                                         verbose_name="وقت الانصراف")
    
    # Additional info
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_person_name(self):
        """الحصول على اسم الشخص"""
        if self.agent:
            return self.agent.full_name
        elif self.monitor:
            return self.monitor.full_name
        return "غير محدد"
    
    def get_duration(self):
        """حساب مدة التواجد"""
        if self.check_in_time and self.check_out_time:
            duration = self.check_out_time - self.check_in_time
            hours = duration.total_seconds() / 3600
            return f"{hours:.2f} ساعة"
        return "لم ينصرف بعد"
    
    def __str__(self):
        return f"{self.get_person_name()} - {self.get_status_display()} - {self.recorded_by.assigned_center_number}"
    
    class Meta:
        verbose_name = "سجل حضور"
        verbose_name_plural = "سجلات الحضور والانصراف"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['record_type', 'status']),
            models.Index(fields=['-created_at']),
        ]


class DirectorLoginLog(models.Model):
    """سجل تسجيل دخول مدراء المراكز"""
    
    director = models.ForeignKey('CenterDirector', on_delete=models.CASCADE,
                                related_name='login_logs',
                                verbose_name="مدير المركز")
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                            verbose_name="المستخدم")
    
    login_time = models.DateTimeField(auto_now_add=True,
                                     verbose_name="وقت تسجيل الدخول")
    logout_time = models.DateTimeField(null=True, blank=True,
                                      verbose_name="وقت تسجيل الخروج")
    
    ip_address = models.GenericIPAddressField(null=True, blank=True,
                                             verbose_name="عنوان IP")
    user_agent = models.TextField(blank=True, verbose_name="متصفح المستخدم")
    
    def get_session_duration(self):
        """حساب مدة الجلسة"""
        if self.logout_time:
            duration = self.logout_time - self.login_time
            hours = duration.total_seconds() / 3600
            return f"{hours:.2f} ساعة"
        return "جلسة نشطة"
    
    def __str__(self):
        return f"{self.director.full_name} - {self.login_time.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        verbose_name = "سجل تسجيل دخول مدير"
        verbose_name_plural = "سجلات تسجيل دخول المدراء"
        ordering = ['-login_time']
