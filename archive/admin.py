from django.contrib import admin
from django.utils.html import format_html
from .models import Letter, CandidateDocument, FormTemplate, ArchiveFolder, ArchivedDocument


@admin.register(Letter)
class LetterAdmin(admin.ModelAdmin):
    list_display = [
        'letter_number', 'letter_type', 'subject', 
        'letter_date', 'priority_badge', 'status_badge',
        'has_attachment'
    ]
    list_filter = ['letter_type', 'priority', 'status', 'letter_date']
    search_fields = ['letter_number', 'subject', 'from_entity', 'to_entity']
    date_hierarchy = 'letter_date'
    
    fieldsets = (
        ('معلومات الكتاب', {
            'fields': ('letter_type', 'letter_number', 'letter_date')
        }),
        ('جهات الاتصال', {
            'fields': ('from_entity', 'to_entity')
        }),
        ('التفاصيل', {
            'fields': ('subject', 'description', 'attachment')
        }),
        ('الحالة والأولوية', {
            'fields': ('priority', 'status')
        }),
        ('معلومات النظام', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def priority_badge(self, obj):
        colors = {
            'normal': '#6c757d',
            'important': '#007bff',
            'urgent': '#ffc107',
            'very_urgent': '#dc3545'
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'الأولوية'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'in_progress': '#17a2b8',
            'completed': '#28a745',
            'archived': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'الحالة'
    
    def has_attachment(self, obj):
        if obj.attachment:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    has_attachment.short_description = 'مرفقات'


@admin.register(CandidateDocument)
class CandidateDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'candidate', 'has_cv', 'has_photo', 
        'has_id_copy', 'uploaded_at'
    ]
    list_filter = ['uploaded_at']
    search_fields = ['candidate__name', 'notes']
    
    fieldsets = (
        ('المرشح', {
            'fields': ('candidate',)
        }),
        ('السيرة الذاتية والصور', {
            'fields': ('cv_file', 'personal_photo', 'campaign_photo')
        }),
        ('الوثائق الرسمية', {
            'fields': (
                'id_copy', 
                'certificate_of_good_conduct',
                'educational_certificates',
                'other_documents'
            )
        }),
        ('ملاحظات', {
            'fields': ('notes',)
        }),
    )
    
    readonly_fields = ['uploaded_at', 'updated_at']
    
    def has_cv(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if obj.cv_file else 'red',
            '✓' if obj.cv_file else '✗'
        )
    has_cv.short_description = 'CV'
    
    def has_photo(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if obj.personal_photo else 'red',
            '✓' if obj.personal_photo else '✗'
        )
    has_photo.short_description = 'صورة'
    
    def has_id_copy(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if obj.id_copy else 'red',
            '✓' if obj.id_copy else '✗'
        )
    has_id_copy.short_description = 'هوية'


@admin.register(FormTemplate)
class FormTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'file_type', 
        'version', 'download_count', 'is_active'
    ]
    list_filter = ['category', 'is_active', 'file_type']
    search_fields = ['title', 'description']
    
    fieldsets = (
        ('معلومات النموذج', {
            'fields': ('title', 'category', 'description')
        }),
        ('الملف', {
            'fields': ('file', 'version')
        }),
        ('الإعدادات', {
            'fields': ('is_active', 'download_count')
        }),
    )
    
    readonly_fields = ['download_count', 'file_type']


@admin.register(ArchiveFolder)
class ArchiveFolderAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'document_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    
    def document_count(self, obj):
        count = obj.documents.count()
        return format_html(
            '<span style="font-weight: bold;">{}</span>',
            count
        )
    document_count.short_description = 'عدد الوثائق'


@admin.register(ArchivedDocument)
class ArchivedDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'folder', 'document_type',
        'document_number', 'document_date', 'archived_at'
    ]
    list_filter = ['folder', 'document_type', 'archived_at']
    search_fields = ['title', 'description', 'document_number', 'tags']
    date_hierarchy = 'archived_at'
    
    fieldsets = (
        ('المجلد', {
            'fields': ('folder',)
        }),
        ('معلومات الوثيقة', {
            'fields': (
                'title', 'document_type', 
                'document_number', 'document_date'
            )
        }),
        ('التفاصيل', {
            'fields': ('description', 'tags')
        }),
        ('الملف', {
            'fields': ('file',)
        }),
        ('معلومات الأرشفة', {
            'fields': ('archived_by', 'archived_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['archived_at']
