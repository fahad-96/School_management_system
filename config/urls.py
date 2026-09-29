from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('academics/', include('academics.urls')),
    path('attendance/', include('attendance.urls')),
    path('exams/', include('exams.urls')),
    path('fees/', include('fees.urls')),
    path('timetable/', include('timetable.urls')),
]
