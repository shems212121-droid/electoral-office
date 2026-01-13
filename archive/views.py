from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count
from django.http import FileResponse, Http404, JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Letter, CandidateDocument, FormTemplate, ArchiveFolder, ArchivedDocument
from .forms import (
    LetterForm, CandidateDocumentForm, FormTemplateForm,
    ArchiveFolderForm, ArchivedDocumentForm, LetterSearchForm
)


# ===== لوحة تحكم الأرشيف =====
def archive_dashboard(request):
    """الصفحة الرئيسية للأرشيف"""
    
    # إحصائيات الكتب
    total_letters = Letter.objects.count()
    incoming_letters = Letter.objects.filter(letter_type='incoming').count()
    outgoing_letters = Letter.objects.filter(letter_type='outgoing').count()
    pending_letters = Letter.objects.filter(status='pending').count()
    urgent_letters = Letter.objects.filter(
        priority__in=['urgent', 'very_urgent'],
        status__in=['pending', 'in_progress']
    ).count()
    
    # إحصائيات المرشحين
    total_candidate_docs = CandidateDocument.objects.count()
    candidates_with_cv = CandidateDocument.objects.filter(cv_file__isnull=False).count()
    candidates_with_photo = CandidateDocument.objects.filter(personal_photo__isnull=False).count()
    
    # إحصائيات الفورمات
    total_templates = FormTemplate.objects.filter(is_active=True).count()
    templates_by_category = FormTemplate.objects.filter(is_active=True).values(
        'category'
    ).annotate(count=Count('id'))
    
    # إحصائيات الأرشيف
    total_folders = ArchiveFolder.objects.count()
    total_archived_docs = ArchivedDocument.objects.count()
    
    # آخر الكتب
    recent_letters = Letter.objects.select_related().order_by('-created_at')[:5]
    
    # الكتب المتأخرة
    overdue_letters = [letter for letter in Letter.objects.filter(
        status__in=['pending', 'in_progress']
    ) if letter.is_overdue][:10]
    
    context = {
        'total_letters': total_letters,
        'incoming_letters': incoming_letters,
        'outgoing_letters': outgoing_letters,
        'pending_letters': pending_letters,
        'urgent_letters': urgent_letters,
        'total_candidate_docs': total_candidate_docs,
        'candidates_with_cv': candidates_with_cv,
        'candidates_with_photo': candidates_with_photo,
        'total_templates': total_templates,
        'templates_by_category': templates_by_category,
        'total_folders': total_folders,
        'total_archived_docs': total_archived_docs,
        'recent_letters': recent_letters,
        'overdue_letters': overdue_letters,
    }
    
    return render(request, 'archive/dashboard.html', context)


# ===== إدارة الكتب =====
def letter_list(request):
    """قائمة الكتب مع البحث"""
    
    letters = Letter.objects.all()
    form = LetterSearchForm(request.GET)
    
    if form.is_valid():
        search = form.cleaned_data.get('search')
        if search:
            letters = letters.filter(
                Q(letter_number__icontains=search) |
                Q(subject__icontains=search) |
                Q(from_entity__icontains=search) |
                Q(to_entity__icontains=search)
            )
        
        letter_type = form.cleaned_data.get('letter_type')
        if letter_type:
            letters = letters.filter(letter_type=letter_type)
        
        priority = form.cleaned_data.get('priority')
        if priority:
            letters = letters.filter(priority=priority)
        
        status = form.cleaned_data.get('status')
        if status:
            letters = letters.filter(status=status)
        
        date_from = form.cleaned_data.get('date_from')
        if date_from:
            letters = letters.filter(letter_date__gte=date_from)
        
        date_to = form.cleaned_data.get('date_to')
        if date_to:
            letters = letters.filter(letter_date__lte=date_to)
    
    # ترقيم الصفحات
    paginator = Paginator(letters, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': form,
    }
    
    return render(request, 'archive/letter_list.html', context)


def letter_add(request):
    """إضافة كتاب جديد"""
    
    if request.method == 'POST':
        form = LetterForm(request.POST, request.FILES)
        if form.is_valid():
            letter = form.save(commit=False)
            # يمكن إضافة اسم المستخدم هنا إذا كان هناك نظام مستخدمين
            letter.save()
            messages.success(request, 'تم إضافة الكتاب بنجاح')
            return redirect('archive:letter_list')
    else:
        form = LetterForm()
    
    context = {'form': form}
    return render(request, 'archive/letter_form.html', context)


def letter_edit(request, pk):
    """تعديل كتاب"""
    
    letter = get_object_or_404(Letter, pk=pk)
    
    if request.method == 'POST':
        form = LetterForm(request.POST, request.FILES, instance=letter)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث الكتاب بنجاح')
            return redirect('archive:letter_list')
    else:
        form = LetterForm(instance=letter)
    
    context = {
        'form': form,
        'letter': letter,
        'is_edit': True
    }
    return render(request, 'archive/letter_form.html', context)


def letter_delete(request, pk):
    """حذف كتاب"""
    
    letter = get_object_or_404(Letter, pk=pk)
    
    if request.method == 'POST':
        letter.delete()
        messages.success(request, 'تم حذف الكتاب بنجاح')
        return redirect('archive:letter_list')
    
    context = {'letter': letter}
    return render(request, 'archive/letter_confirm_delete.html', context)


def letter_detail(request, pk):
    """تفاصيل الكتاب"""
    
    letter = get_object_or_404(Letter, pk=pk)
    context = {'letter': letter}
    return render(request, 'archive/letter_detail.html', context)


# ===== إدارة وثائق المرشحين =====
def candidate_document_list(request):
    """قائمة وثائق المرشحين"""
    
    documents = CandidateDocument.objects.select_related('candidate').all()
    
    # البحث
    search = request.GET.get('search')
    if search:
        documents = documents.filter(candidate__full_name__icontains=search)
    
    # ترقيم الصفحات
    paginator = Paginator(documents, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj}
    return render(request, 'archive/candidate_document_list.html', context)


def candidate_document_add(request):
    """إضافة وثائق مرشح"""
    
    if request.method == 'POST':
        form = CandidateDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة وثائق المرشح بنجاح')
            return redirect('archive:candidate_document_list')
    else:
        form = CandidateDocumentForm()
    
    # Get all candidates for the datalist
    from elections.models import PartyCandidate
    candidates_list = PartyCandidate.objects.all().order_by('full_name')
    
    context = {'form': form, 'candidates_list': candidates_list}
    return render(request, 'archive/candidate_document_form.html', context)


def candidate_document_edit(request, pk):
    """تعديل وثائق مرشح"""
    
    document = get_object_or_404(CandidateDocument, pk=pk)
    
    if request.method == 'POST':
        form = CandidateDocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث وثائق المرشح بنجاح')
            return redirect('archive:candidate_document_list')
    else:
        form = CandidateDocumentForm(instance=document)
    
    # Get all candidates for the datalist
    from elections.models import PartyCandidate
    candidates_list = PartyCandidate.objects.all().order_by('full_name')
    
    context = {
        'form': form,
        'document': document,
        'candidates_list': candidates_list,
        'is_edit': True
    }
    return render(request, 'archive/candidate_document_form.html', context)


def candidate_document_detail(request, pk):
    """تفاصيل وثائق المرشح"""
    
    document = get_object_or_404(CandidateDocument, pk=pk)
    context = {'document': document}
    return render(request, 'archive/candidate_document_detail.html', context)


# ===== إدارة الفورمات الجاهزة =====
def template_list(request):
    """قائمة الفورمات الجاهزة"""
    
    templates = FormTemplate.objects.filter(is_active=True)
    
    # التصنيف
    category = request.GET.get('category')
    if category:
        templates = templates.filter(category=category)
    
    # البحث
    search = request.GET.get('search')
    if search:
        templates = templates.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
    
    # ترقيم الصفحات
    paginator = Paginator(templates, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # التصنيفات للفلترة
    categories = FormTemplate.CATEGORY_CHOICES
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category
    }
    return render(request, 'archive/template_list.html', context)


def template_add(request):
    """إضافة فورمات جديد"""
    
    if request.method == 'POST':
        form = FormTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة النموذج بنجاح')
            return redirect('archive:template_list')
    else:
        form = FormTemplateForm()
    
    context = {'form': form}
    return render(request, 'archive/template_form.html', context)


def template_edit(request, pk):
    """تعديل فورمات"""
    
    template = get_object_or_404(FormTemplate, pk=pk)
    
    if request.method == 'POST':
        form = FormTemplateForm(request.POST, request.FILES, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث النموذج بنجاح')
            return redirect('archive:template_list')
    else:
        form = FormTemplateForm(instance=template)
    
    context = {
        'form': form,
        'template': template,
        'is_edit': True
    }
    return render(request, 'archive/template_form.html', context)


def template_download(request, pk):
    """تحميل فورمات"""
    
    template = get_object_or_404(FormTemplate, pk=pk)
    
    try:
        # زيادة عداد التحميل
        template.increment_download()
        
        # إرجاع الملف
        response = FileResponse(template.file.open('rb'))
        response['Content-Disposition'] = f'attachment; filename="{template.file.name}"'
        return response
    except FileNotFoundError:
        raise Http404("الملف غير موجود")


# ===== إدارة الأرشيف =====
def archive_folder_list(request):
    """قائمة مجلدات الأرشيف"""
    
    folders = ArchiveFolder.objects.annotate(
        doc_count=Count('documents')
    ).order_by('name')
    
    context = {'folders': folders}
    return render(request, 'archive/folder_list.html', context)


def archived_document_list(request):
    """قائمة الوثائق المؤرشفة"""
    
    documents = ArchivedDocument.objects.select_related('folder').all()
    
    # التصفية بالمجلد
    folder_id = request.GET.get('folder')
    if folder_id:
        documents = documents.filter(folder_id=folder_id)
    
    # البحث
    search = request.GET.get('search')
    if search:
        documents = documents.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(tags__icontains=search) |
            Q(document_number__icontains=search)
        )
    
    # ترقيم الصفحات
    paginator = Paginator(documents, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # المجلدات للفلترة
    folders = ArchiveFolder.objects.all()
    
    context = {
        'page_obj': page_obj,
        'folders': folders
    }
    return render(request, 'archive/archived_document_list.html', context)


def archived_document_add(request):
    """إضافة وثيقة للأرشيف"""
    
    if request.method == 'POST':
        form = ArchivedDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            # يمكن إضافة اسم المستخدم هنا
            document.save()
            messages.success(request, 'تم أرشفة الوثيقة بنجاح')
            return redirect('archive:archived_document_list')
    else:
        form = ArchivedDocumentForm()
    
    context = {'form': form}
    return render(request, 'archive/archived_document_form.html', context)


def archived_document_edit(request, pk):
    """تعديل وثيقة مؤرشفة"""
    
    document = get_object_or_404(ArchivedDocument, pk=pk)
    
    if request.method == 'POST':
        form = ArchivedDocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث الوثيقة بنجاح')
            return redirect('archive:archived_document_list')
    else:
        form = ArchivedDocumentForm(instance=document)
    
    context = {
        'form': form,
        'document': document,
        'is_edit': True
    }
    return render(request, 'archive/archived_document_form.html', context)


def archived_document_download(request, pk):
    """تحميل وثيقة مؤرشفة"""
    
    document = get_object_or_404(ArchivedDocument, pk=pk)
    
    try:
        response = FileResponse(document.file.open('rb'))
        response['Content-Disposition'] = f'attachment; filename="{document.file.name}"'
        return response
    except FileNotFoundError:
        raise Http404("الملف غير موجود")


def archived_document_delete(request, pk):
    """حذف وثيقة مؤرشفة"""
    document = get_object_or_404(ArchivedDocument, pk=pk)
    
    if request.method == 'POST':
        document_title = document.title
        document.delete()
        messages.success(request, f'تم حذف الوثيقة: {document_title}')
        return redirect('archive:archived_document_list')
    
    return render(request, 'archive/archived_document_confirm_delete.html', {'document': document})


def archived_document_detail(request, pk):
    """تفاصيل وثيقة مؤرشفة"""
    document = get_object_or_404(ArchivedDocument, pk=pk)
    return render(request, 'archive/archived_document_detail.html', {'document': document})


def candidate_document_delete(request, pk):
    """حذف وثائق مرشح"""
    document = get_object_or_404(CandidateDocument, pk=pk)
    
    if request.method == 'POST':
        candidate_name = document.candidate.full_name
        document.delete()
        messages.success(request, f'تم حذف وثائق المرشح: {candidate_name}')
        return redirect('archive:candidate_document_list')
    
    return render(request, 'archive/candidate_document_confirm_delete.html', {'document': document})


def template_delete(request, pk):
    """حذف فورمات"""
    template = get_object_or_404(FormTemplate, pk=pk)
    
    if request.method == 'POST':
        template_title = template.title
        template.delete()
        messages.success(request, f'تم حذف النموذج: {template_title}')
        return redirect('archive:template_list')
    
    return render(request, 'archive/template_confirm_delete.html', {'template': template})


def template_detail(request, pk):
    """تفاصيل فورمات"""
    template = get_object_or_404(FormTemplate, pk=pk)
    return render(request, 'archive/template_detail.html', {'template': template})


# ===== استمارات المعلومات والمقابلات =====
from .models import CandidateInfoForm, CandidateInterview
from .forms import CandidateInfoFormForm, CandidateInterviewForm

def candidate_info_list(request):
    """قائمة استمارات معلومات المرشحين"""
    forms_list = CandidateInfoForm.objects.all().order_by('-created_at')
    
    # Search
    search = request.GET.get('search')
    if search:
        forms_list = forms_list.filter(
            Q(full_name__icontains=search) |
            Q(phone_number__icontains=search)
        )

    paginator = Paginator(forms_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'archive/candidate_info_list.html', {'page_obj': page_obj})

def candidate_info_add(request):
    """إضافة استمارة معلومات مرشح"""
    if request.method == 'POST':
        form = CandidateInfoFormForm(request.POST)
        if form.is_valid():
            info_form = form.save()
            messages.success(request, 'تم حفظ استمارة المعلومات بنجاح')
            return redirect('archive:candidate_info_list')
    else:
        form = CandidateInfoFormForm()
    return render(request, 'archive/candidate_info_form.html', {'form': form, 'title': 'إضافة استمارة معلومات مرشح'})

def candidate_info_edit(request, pk):
    """تعديل استمارة معلومات مرشح"""
    info_form = get_object_or_404(CandidateInfoForm, pk=pk)
    if request.method == 'POST':
        form = CandidateInfoFormForm(request.POST, instance=info_form)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث الاستمارة بنجاح')
            return redirect('archive:candidate_info_list')
    else:
        form = CandidateInfoFormForm(instance=info_form)
    return render(request, 'archive/candidate_info_form.html', {'form': form, 'title': 'تعديل استمارة معلومات مرشح'})

def candidate_info_detail(request, pk):
    """تفاصيل استمارة معلومات مرشح"""
    info_form = get_object_or_404(CandidateInfoForm, pk=pk)
    return render(request, 'archive/candidate_info_detail.html', {'info_form': info_form})


def candidate_interview_list(request):
    """قائمة استمارات المقابلات"""
    interviews = CandidateInterview.objects.all().order_by('-created_at')
    
    # Search
    search = request.GET.get('search')
    if search:
        interviews = interviews.filter(candidate_name__icontains=search)
        
    paginator = Paginator(interviews, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'archive/candidate_interview_list.html', {'page_obj': page_obj})

def candidate_interview_add(request):
    """إضافة استمارة مقابلة"""
    if request.method == 'POST':
        form = CandidateInterviewForm(request.POST)
        if form.is_valid():
            interview = form.save()
            messages.success(request, 'تم حفظ استمارة المقابلة بنجاح')
            return redirect('archive:candidate_interview_list')
    else:
        form = CandidateInterviewForm()
    return render(request, 'archive/candidate_interview_form.html', {'form': form, 'title': 'إضافة استمارة مقابلة'})

def candidate_interview_edit(request, pk):
    """تعديل استمارة مقابلة"""
    interview = get_object_or_404(CandidateInterview, pk=pk)
    if request.method == 'POST':
        form = CandidateInterviewForm(request.POST, instance=interview)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث استمارة المقابلة بنجاح')
            return redirect('archive:candidate_interview_list')
    else:
        form = CandidateInterviewForm(instance=interview)
    return render(request, 'archive/candidate_interview_form.html', {'form': form, 'title': 'تعديل استمارة مقابلة'})

def candidate_interview_detail(request, pk):
    """تفاصيل استمارة المقابلة"""
    interview = get_object_or_404(CandidateInterview, pk=pk)
    return render(request, 'archive/candidate_interview_detail.html', {'interview': interview})
