from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .models import VoteCount, PollingStation, PartyCandidate, UserRole, PollingCenter
from django import forms

def is_result_entry_user(user):
    return user.is_authenticated and (
        user.is_superuser or 
        (hasattr(user, 'userprofile') and user.userprofile.role == UserRole.DATA_ENTRY_RESULTS)
    )

class ResultEntryForm(forms.ModelForm):
    class Meta:
        model = VoteCount
        fields = ['station', 'candidate', 'vote_count', 'vote_type', 'notes']
        widgets = {
            'station': forms.Select(attrs={'class': 'form-control select2'}),
            'candidate': forms.Select(attrs={'class': 'form-control select2'}),
            'vote_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'vote_type': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optimize queries
        self.fields['station'].queryset = PollingStation.objects.select_related('center').all()
        self.fields['candidate'].queryset = PartyCandidate.objects.select_related('party').all()

@login_required
@user_passes_test(is_result_entry_user)
def result_entry_dashboard(request):
    """
    Dashboard for Result Entry Users.
    Shows only their own entries and provides interface to add new ones.
    """
    user_entries = VoteCount.objects.filter(entered_by=request.user).select_related(
        'station', 'station__center', 'candidate', 'candidate__party'
    ).order_by('-entered_at')[:50]  # Show last 50 entries

    user_stats = {
        'total_entries': VoteCount.objects.filter(entered_by=request.user).count(),
        'today_entries': VoteCount.objects.filter(
            entered_by=request.user, 
            entered_at__date=timezone.now().date()
        ).count()
    }

    context = {
        'entries': user_entries,
        'stats': user_stats,
        'page_title': 'لوحة إدخال نتائج الانتخابات'
    }
    return render(request, 'elections/result_entry/dashboard.html', context)

@login_required
@user_passes_test(is_result_entry_user)
def result_entry_add(request):
    if request.method == 'POST':
        form = ResultEntryForm(request.POST)
        if form.is_valid():
            try:
                # Check for uniqueness manually to give better error message
                station = form.cleaned_data['station']
                candidate = form.cleaned_data['candidate']
                vote_type = form.cleaned_data['vote_type']
                
                if VoteCount.objects.filter(station=station, candidate=candidate, vote_type=vote_type).exists():
                    messages.error(request, f'⚠️ خطأ: تم إدخال نتيجة لهذا المرشح ({candidate}) في هذه المحطة ({station}) ونوع التصويت ({vote_type}) مسبقاً! لا يمكن التكرار.')
                else:
                    vote_count = form.save(commit=False)
                    vote_count.entered_by = request.user
                    vote_count.save()
                    messages.success(request, '✅ تم حفظ النتيجة بنجاح!')
                    return redirect('result_entry_add')
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء الحفظ: {str(e)}')
        else:
             messages.error(request, 'يرجى تصحيح الأخطاء في النموذج')
    else:
        form = ResultEntryForm()

    return render(request, 'elections/result_entry/add_form.html', {'form': form})
