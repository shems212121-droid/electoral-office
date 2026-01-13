from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.http import HttpResponse

def ping(request):
    from elections.models import Voter, PollingCenter, RegistrationCenter
    v_count = Voter.objects.count()
    pc_count = PollingCenter.objects.count()
    rc_count = RegistrationCenter.objects.count()
    return HttpResponse(f"Pong - System is Active. Voters: {v_count}, Centers: {pc_count}, RegCenters: {rc_count}")

urlpatterns = [
    path('test-ping/', ping),
    path('admin/', admin.site.urls),
    # path('finance/', include('finance.urls')),
    # path('archive/', include('archive.urls')),
    path('', include('elections.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

