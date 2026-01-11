from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.http import HttpResponse

def ping(request):
    return HttpResponse("Pong - System is Active")

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

